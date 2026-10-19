# Clase 22: concurrent.futures

## Introducción: la abstracción que unifica

Este cuatrimestre vimos tres formas de hacer varias cosas a la vez, y cada una con su API.

Threads: creás objetos `Thread`, los arrancás, los esperás con `join()`, y si querés resultados los sacás de una estructura compartida con locks. Procesos: casi lo mismo pero con `multiprocessing`, y los resultados viajan por una `Queue` o un `Manager`. Corrutinas: `async def`, `await`, un event loop.

Tres mecanismos, tres vocabularios, tres formas de recuperar un resultado.

`concurrent.futures` propone otra cosa: **una sola interfaz para todas**. Le entregás trabajo a un *executor* y te devuelve un *future* —un recibo por un resultado que todavía no existe. Cómo se ejecute ese trabajo (en un thread, en un proceso) pasa a ser un detalle que se cambia en una línea.

```python
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(4) as pool:      # cambiar a ProcessPoolExecutor
    futuro = pool.submit(trabajo, dato)  # y todo lo demás sigue igual
    print(futuro.result())
```

Esa capacidad de intercambiar la estrategia sin tocar el código es el aporte principal del módulo, y la razón por la que vale una clase propia.

Ya lo usamos dos veces: en la clase 14 para el pool de servidores y en la 21 para sacar el cálculo del event loop. Hoy lo damos vuelta: qué es exactamente un `Future`, cómo recuperar resultados a medida que llegan, y por qué el manejo de excepciones acá es distinto a todo lo que vimos.

> **Nota:** los archivos `futuros.py`, `patrones.py` y `errores.py` acompañan la clase.

---

## Future: un recibo por algo que todavía no está

Cuando hacés `submit()`, el trabajo se encola y la llamada **vuelve enseguida**. Lo que te devuelve no es el resultado sino una promesa:

```python
futuro = pool.submit(descargar, url)    # vuelve en microsegundos
```

Ese objeto `Future` tiene un ciclo de vida de tres estados:

```
  PENDING  ──>  RUNNING  ──>  FINISHED
  (en cola)    (ejecutando)   (con resultado o con excepción)
                   │
                   └──>  CANCELLED  (si lo cancelaste a tiempo)
```

Y una API chica para consultarlo:

| Método | Qué hace | ¿Bloquea? |
|--------|----------|-----------|
| `done()` | ¿Ya terminó? | No |
| `running()` | ¿Está ejecutándose ahora? | No |
| `cancelled()` | ¿Fue cancelado? | No |
| `result()` | El valor devuelto | **Sí**, hasta que esté |
| `result(timeout=5)` | Igual, pero con límite | Sí, hasta 5 s |
| `exception()` | La excepción, si hubo | **Sí** |
| `cancel()` | Intenta cancelarlo | No |

La distinción entre lo que bloquea y lo que no es la que hay que tener presente. `done()` es una consulta instantánea; `result()` es una espera.

### cancel() solo funciona si no arrancó

```python
futuro = pool.submit(tarea_larga)
futuro.cancel()        # True si todavía estaba en cola, False si ya arrancó
```

A diferencia de asyncio, acá **no hay forma de interrumpir una tarea en ejecución**. Un thread no se puede matar desde afuera en Python, y un proceso sí pero dejaría el estado a medias. `cancel()` solo saca de la cola lo que no empezó.

Es una diferencia importante con la clase 21: ahí `cancel()` inyectaba una excepción en el próximo `await`. Acá no hay puntos de suspensión donde inyectar nada.

---

## Recuperar resultados: map contra as_completed

Tenés cuatro tareas de distinta duración y querés sus resultados. Hay dos formas, y la diferencia se ve en los tiempos.

### map: en orden de entrada

```python
with ThreadPoolExecutor(4) as pool:
    for resultado in pool.map(tarea, [5, 1, 2, 4]):
        print(resultado)
```

```
r5  (t=0.50s)
r1  (t=0.50s)
r2  (t=0.50s)
r4  (t=0.50s)
```

Las cuatro llegan juntas, a los 0.50 s. Y eso que `r1` estuvo lista a los 0.10 s.

El motivo es que `map` devuelve los resultados **en el orden en que le pasaste los argumentos**. Como el primero tardaba 0.50 s, los otros tres esperaron su turno aunque ya estuvieran listos.

Las tareas sí corrieron en paralelo —el total fue 0.50 y no 1.20— pero la *entrega* es secuencial.

### as_completed: a medida que terminan

```python
with ThreadPoolExecutor(4) as pool:
    futuros = [pool.submit(tarea, n) for n in [5, 1, 2, 4]]
    for futuro in as_completed(futuros):
        print(futuro.result())
```

```
r1  (t=0.10s)
r2  (t=0.20s)
r4  (t=0.40s)
r5  (t=0.50s)
```

Cada resultado aparece apenas está listo. El orden es el de finalización, no el de entrada.

### Cuál usar

| Querés... | Usá |
|-----------|-----|
| Los resultados en el mismo orden que la entrada | `map` |
| Empezar a procesar lo que vaya llegando | `as_completed` |
| Mostrar progreso al usuario | `as_completed` |
| Una transformación simple de una lista | `map` |
| Saber cuál falló | `as_completed` (ver abajo) |

Un detalle de `as_completed`: pierde la correspondencia entre resultado y entrada. Si la necesitás, guardá un diccionario:

```python
futuros = {pool.submit(bajar, url): url for url in urls}

for futuro in as_completed(futuros):
    url = futuros[futuro]               # recuperar de qué era
    print(url, futuro.result())
```

Ese patrón —el future como clave del diccionario— es idiomático y conviene conocerlo.

### wait: cuando querés más control

```python
from concurrent.futures import wait, FIRST_COMPLETED, FIRST_EXCEPTION

listos, pendientes = wait(futuros, timeout=5, return_when=FIRST_COMPLETED)
```

Devuelve dos conjuntos: los que terminaron y los que no. Sirve para casos como "esperá al primero que responda y cancelá el resto", o "frená todo si alguno falla" con `FIRST_EXCEPTION`.

---

## Excepciones: el capítulo que sorprende

Acá está lo menos intuitivo del módulo, y la fuente de bugs más común.

**Una excepción dentro de un worker no se propaga cuando ocurre.** Queda guardada en el `Future`, y solo aparece cuando pedís el resultado:

```python
futuro = pool.submit(funcion_que_falla)
# submit() no lanzó nada

time.sleep(1)
futuro.done()          # True: terminó
futuro.exception()     # ValueError('falló'): acá está, guardada

futuro.result()        # AHORA sí la lanza
```

Es coherente con el modelo: el worker corre en otro hilo o proceso, así que la excepción no puede subir por tu pila de llamadas. Se guarda y te espera.

### El bug silencioso

La consecuencia es grave: **si nunca pedís el resultado, la excepción desaparece**.

```python
with ThreadPoolExecutor(2) as pool:
    pool.submit(tarea_que_falla)        # no guardo el future
# el programa sigue como si nada
```

Nada en la salida indica que algo salió mal. La tarea falló, el error se guardó en un `Future` que nadie miró, y el objeto se destruyó.

En un servidor que procesa trabajo en segundo plano, eso significa que las tareas fallan **en silencio** y nadie se entera hasta que alguien nota que faltan resultados.

> Asyncio es menos cruel acá: si una Task falla y nadie la espera, al destruirse imprime `Task exception was never retrieved`. `concurrent.futures` no avisa nada.

### Las tres defensas

**Siempre consumir los resultados**, aunque no los necesites:

```python
futuros = [pool.submit(tarea, x) for x in datos]
for f in as_completed(futuros):
    try:
        f.result()
    except Exception:
        logging.exception('una tarea falló')
```

**Capturar adentro de la función**, para que el worker nunca lance:

```python
def tarea_segura(x):
    try:
        return ('ok', procesar(x))
    except Exception as e:
        return ('error', str(e))
```

**Un callback que vigile:**

```python
def vigilar(futuro):
    if futuro.exception():
        logging.error('falló: %r', futuro.exception())

futuro.add_done_callback(vigilar)
```

### map y las excepciones

Con `map` el comportamiento es distinto y también confunde: la excepción se lanza **al iterar**, no al llamar.

```python
resultados = pool.map(tarea, datos)     # no lanza nada todavía
for r in resultados:                    # acá sí, cuando llega al que falló
    print(r)
```

Y lo que es peor: **corta la iteración**. Los resultados posteriores al que falló no los vas a ver, aunque estén calculados.

Si querés procesar todo y después revisar los errores, `as_completed` con `try/except` adentro es la opción correcta.

---

## Threads o procesos: la tabla definitiva

Los dos executors tienen la misma interfaz, así que la decisión es solo sobre qué hace tu función.

```python
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

ThreadPoolExecutor(max_workers=8)       # comparten memoria, los frena el GIL
ProcessPoolExecutor(max_workers=4)      # memoria separada, paralelismo real
```

| | ThreadPool | ProcessPool |
|---|---|---|
| Paralelismo real en CPU | No (GIL) | Sí |
| Costo de crear el pool | ~0.4 ms | ~10 ms |
| Costo por tarea | Bajo | Pickle de argumentos y resultado |
| Memoria compartida | Sí | No |
| Argumentos | Cualquier objeto | Solo picklables |
| Para qué sirve | I/O bloqueante | Cálculo |

Los números de la primera fila los medimos en la clase 21: cuatro tareas CPU-bound tardaron 16.94 s con threads y 4.78 s con procesos.

### El costo del pickle

Todo lo que entra y sale de un `ProcessPoolExecutor` se serializa. Medido:

```
mandar 2.000.000 de enteros:  0.20 s
mandar un solo entero:        0.0019 s
```

Cien veces más. Si tu función recibe estructuras grandes, **el transporte puede costar más que el cálculo**, y los procesos terminan siendo más lentos que los threads.

La forma de evitarlo es mandar poco: en vez del dataset entero, un índice o una ruta de archivo que el worker lea por su cuenta.

Y hay cosas que directamente no se pueden mandar:

```python
pool.submit(lambda x: x * 2, 5)
# AttributeError: Can't pickle local object
```

Las lambdas, las funciones definidas adentro de otras y los objetos con sockets o archivos abiertos no son picklables. Para `ProcessPoolExecutor`, las funciones tienen que estar **al nivel del módulo**.

### Crear el pool una vez

Crear procesos cuesta unos 10 ms —veinticinco veces más que crear threads. No parece mucho, pero si lo hacés por pedido en un servidor, son 10 ms de latencia agregada a cada uno.

```python
# MAL: un pool por pedido
def manejar(datos):
    with ProcessPoolExecutor(4) as pool:
        return pool.submit(procesar, datos).result()

# BIEN: uno solo, al arrancar
pool = ProcessPoolExecutor(4)
def manejar(datos):
    return pool.submit(procesar, datos).result()
```

Es lo que hicimos en la clase 21 con el `lifespan` de FastAPI.

---

## Dónde encaja esto en todo lo que vimos

`concurrent.futures` es la capa de más alto nivel de las herramientas sincrónicas, y conviene ubicarla respecto del resto:

```
  concurrent.futures        <- pools con una interfaz común
         │
    ┌────┴────┐
threading   multiprocessing  <- los mecanismos de abajo
```

Y en relación con asyncio, son dos mundos que se tocan en un punto:

```python
# Desde asyncio, delegar a un executor
resultado = await loop.run_in_executor(pool, funcion, arg)
```

Esa línea —la de la clase 21— es el puente. Asyncio maneja la concurrencia de I/O; cuando aparece algo que no puede estar en el loop, lo manda a un executor y espera el resultado sin bloquearse.

La tabla de decisión completa del cuatrimestre:

| Situación | Herramienta | Clase |
|-----------|-------------|-------|
| Muchas conexiones de red | asyncio | 18-21 |
| I/O bloqueante, pocas tareas | `ThreadPoolExecutor` | hoy |
| Cálculo pesado | `ProcessPoolExecutor` | hoy |
| Control fino sobre threads | `threading` | 10 |
| Control fino sobre procesos | `multiprocessing` | 8-9 |
| Trabajo distribuido entre máquinas | Celery | 23-24 |

---

## Conceptos clave

1. **Un `Future` es un recibo**: el resultado que todavía no está.
2. **`submit()` vuelve enseguida**; `result()` bloquea hasta que haya valor.
3. **`cancel()` solo sirve si la tarea no arrancó**: no se puede interrumpir un thread en ejecución.
4. **`map` devuelve en orden de entrada**: el primero lento retrasa la entrega de todos.
5. **`as_completed` devuelve en orden de finalización**: medido, 0.10 / 0.20 / 0.40 / 0.50 s contra 0.50 s los cuatro.
6. **Para saber de qué era cada resultado**, usá el future como clave de un diccionario.
7. **La excepción no se propaga al fallar**: se guarda en el `Future` y aparece al pedir `result()`.
8. **Si nunca pedís el resultado, la excepción se pierde en silencio**: es el bug más común del módulo.
9. **Con `map`, una excepción corta la iteración**: los resultados posteriores se pierden.
10. **Threads para I/O, procesos para CPU**: misma interfaz, se cambia en una línea.
11. **Todo lo que va a un `ProcessPoolExecutor` se picklea**: mandar 2M de enteros cuesta 100 veces más que uno.
12. **Las lambdas no se pueden mandar a procesos**: las funciones tienen que estar al nivel del módulo.
13. **Crear el pool una vez**, al arrancar: 10 ms por pool de procesos contra 0.4 ms de threads.

---

## Preparación para la próxima clase

En la **clase 23 (Celery I)** damos el último salto de escala. Hasta acá toda la concurrencia vivió **dentro de un proceso o en procesos hijos de la misma máquina**. Celery reparte el trabajo entre máquinas distintas, con un broker en el medio que guarda la cola.

Es la misma idea de hoy —encolar trabajo, recibir un recibo, consultar el resultado— pero donde los workers pueden estar en otro servidor, sobrevivir a un reinicio, y escalarse agregando máquinas.

Para llegar preparado:

- Corré `errores.py` y entendé por qué la primera parte no imprime nada.
- Para el TP2: la medición 2 es exactamente lo de la clase 21, pero ahora tenés el vocabulario completo para explicarla.

---

## Referencias

- [`concurrent.futures`](https://docs.python.org/3/library/concurrent.futures.html) - documentación oficial
- [PEP 3148](https://peps.python.org/pep-3148/) - el documento que lo introdujo, con la justificación del diseño
- [`asyncio.loop.run_in_executor`](https://docs.python.org/3/library/asyncio-eventloop.html#asyncio.loop.run_in_executor) - el puente con asyncio
- [`pickle`](https://docs.python.org/3/library/pickle.html) - qué se puede serializar y qué no

---

*Computación II - 2026 - Clase 22*
