# Clase 21: Asyncio avanzado

## Introducción: lo que falta para construir algo

Las tres clases anteriores armaron el andamiaje. En la 18 vimos de dónde salen las corrutinas, en la 19 cómo se expone una API, en la 20 cómo hacer I/O de red sin bloquear. Lo que falta es lo que convierte esas piezas en un sistema.

Un servicio real no es un endpoint que responde: es una **arquitectura** donde el trabajo entra por un lado, se encola, lo toman workers que corren en paralelo, y los resultados vuelven. Hoy vemos las cuatro herramientas que hacen falta para eso:

- **`asyncio.Queue`** para repartir trabajo entre workers
- **`TaskGroup`** para que un grupo de tareas se comporte como una unidad
- **Primitivas de sincronización** async, para cuando la cola no alcanza
- **Executors** para sacar del loop lo que no puede estar ahí

Es, casi literalmente, el diagrama del TP2. Al final de esta clase van a tener todo lo obligatorio del enunciado.

Y hay un tema de fondo que atraviesa la clase: **asyncio te da concurrencia pero no paralelismo**. Un event loop corre en un hilo, así que puede intercalar miles de esperas pero no puede sumar dos números al mismo tiempo que resta otros dos. Cuando el trabajo es cálculo, hay que salir del loop — y entender adónde ir es la última pieza.

> **Nota:** los archivos `cola.py`, `grupos.py` y `executor.py` acompañan la clase.

---

## asyncio.Queue: repartir trabajo

Una cola conecta a quien produce trabajo con quien lo consume, desacoplando sus ritmos. Es el patrón productor-consumidor de la clase 11, ahora entre corrutinas.

```python
import asyncio

async def productor(cola, n):
    for i in range(n):
        await cola.put(f'tarea-{i}')          # await: puede esperar si está llena

async def worker(cola, wid):
    while True:
        tarea = await cola.get()              # await: espera si está vacía
        try:
            await procesar(tarea)
        finally:
            cola.task_done()                  # avisar que terminó

async def main():
    cola = asyncio.Queue(maxsize=5)
    workers = [asyncio.create_task(worker(cola, i)) for i in range(3)]

    await productor(cola, 12)
    await cola.join()                         # esperar a que no quede nada

    for w in workers:
        w.cancel()                            # los workers son bucles infinitos
```

Doce tareas de 0.05 s repartidas entre tres workers tardan **0.20 s**, no 0.60: se procesan de a tres.

Hay varias cosas ahí que conviene mirar de cerca.

### maxsize es control de flujo

`asyncio.Queue(maxsize=5)` limita cuántos elementos pueden estar esperando. Si la cola está llena, `await cola.put()` **se suspende** hasta que un worker consuma algo.

Eso es *backpressure*, el mismo concepto que el `drain()` de la clase 20: si el productor es más rápido que los consumidores, se lo frena en vez de dejar que la cola crezca sin límite.

Con `maxsize=0` (el default) la cola es infinita, y un productor rápido puede agotar la memoria. En un servidor que recibe pedidos de afuera, **poner un límite es parte del diseño**: cuando se llena, podés rechazar con un 503 en vez de aceptar trabajo que nunca vas a poder hacer.

### task_done y join

`cola.join()` espera a que todas las tareas estén **procesadas**, no solo sacadas de la cola. Para que funcione, cada worker tiene que llamar a `cola.task_done()` cuando termina.

La cola lleva un contador interno: `put()` lo incrementa, `task_done()` lo decrementa, y `join()` espera a que llegue a cero. Si un worker se olvida de llamarlo, **`join()` espera para siempre**.

Por eso va en un `finally`: si `procesar()` lanza excepción, el contador tiene que bajar igual.

### Los workers son bucles infinitos

Un worker con `while True` nunca termina solo. Hay dos formas de pararlo.

**Cancelarlo**, como arriba. Simple, pero abrupto: si lo cancelás justo cuando estaba procesando algo, esa tarea queda a medias.

**Con un centinela**: poner en la cola un valor especial que signifique "terminá".

Antes del código, una palabra sobre `object()`, que aparece ahí y puede resultar extraño. `object()` crea una instancia del tipo base de Python: un objeto vacío, de 16 bytes, que no hace absolutamente nada. Su única propiedad útil es que **es único**, y por eso se compara con `is` (identidad) en vez de `==` (igualdad).

¿Por qué no usar un valor común como `None` o la cadena `'FIN'`? Porque cualquiera de esos podría ser un dato legítimo:

```python
CENTINELA = 'FIN'
tareas = ['descargar', 'FIN', 'hashear']    # un usuario encoló la cadena 'FIN'
# el worker se apaga en el segundo item, dejando trabajo sin hacer
```

Con `object()` eso es imposible: la única referencia a ese objeto la tiene tu código, así que nada que venga de afuera puede ser idéntico a él. Es el modismo estándar de Python para "valor único que no se puede confundir con un dato". La biblioteca estándar usa la misma idea en varios lugares, aunque con una clase propia en vez de `object()` directo, para que el `repr` sea legible al depurar: `dataclasses.MISSING` es una instancia de `_MISSING_TYPE`, e `inspect.Parameter.empty` de `_empty`. Si el centinela es interno a tu código, `object()` alcanza.

```python
CENTINELA = object()

async def worker(cola):
    while True:
        item = await cola.get()
        if item is CENTINELA:
            cola.task_done()
            break                             # salida ordenada
        try:
            await procesar(item)
        finally:
            cola.task_done()

# Para parar N workers, hay que poner N centinelas
for _ in range(len(workers)):
    await cola.put(CENTINELA)
```

El centinela es más prolijo porque cada worker termina su trabajo actual antes de salir. Para el apagado ordenado que pide el TP2, es la opción correcta.

### Variantes

```python
asyncio.Queue()            # FIFO: el primero que entra, el primero que sale
asyncio.LifoQueue()        # LIFO: como una pila
asyncio.PriorityQueue()    # ordenada: sale primero el de menor prioridad
```

La de prioridad recibe tuplas `(prioridad, item)` y entrega la de número más bajo. Ojo con un detalle: si dos elementos tienen la misma prioridad, Python compara el segundo campo, y si no es comparable da `TypeError`. La solución es meter un contador en el medio: `(prioridad, contador, item)`.

Y una advertencia de diseño: una cola con prioridad puede provocar **inanición**. Si siempre entran tareas urgentes, las de baja prioridad no se procesan nunca. Es el mismo problema que vimos en la clase 11.

---

## TaskGroup: tareas que viven juntas

En la clase 20 usamos `gather()` para lanzar varias corrutinas. Funciona, pero tiene un problema cuando algo falla:

```python
await asyncio.gather(tarea_a(), tarea_b(), tarea_c())
```

Si `tarea_a` lanza una excepción, `gather` la propaga — pero **`tarea_b` y `tarea_c` siguen corriendo**, huérfanas, sin nadie que las espere ni las cancele. En un servidor eso significa trabajo fantasma consumiendo recursos.

Desde Python 3.11 hay una alternativa mejor:

```python
async with asyncio.TaskGroup() as grupo:
    grupo.create_task(tarea_a())
    grupo.create_task(tarea_b())
    grupo.create_task(tarea_c())
# al salir del bloque, las tres terminaron
```

La diferencia está en el manejo de errores: **si una falla, las hermanas se cancelan automáticamente** y el error se propaga al salir del bloque.

Eso se llama **concurrencia estructurada**, y la idea es simple: las tareas viven dentro de un bloque y no lo sobreviven, igual que las variables locales viven dentro de una función. No quedan tareas sueltas por ahí.

### Capturar los errores

Como pueden fallar varias a la vez, el error llega envuelto en un `ExceptionGroup`, y se captura con una sintaxis nueva:

```python
try:
    async with asyncio.TaskGroup() as grupo:
        grupo.create_task(puede_fallar())
        grupo.create_task(otra())
except* ValueError as eg:                     # el asterisco no es un error
    print(f'fallaron {len(eg.exceptions)} tareas con ValueError')
except* TimeoutError as eg:
    print('hubo timeouts')
```

El `except*` captura **todas** las excepciones de ese tipo dentro del grupo. A diferencia del `except` común, pueden ejecutarse varias ramas: si fallaron un `ValueError` y un `TimeoutError`, entran las dos.

### Cuándo usar cada uno

| Situación | Herramienta |
|-----------|-------------|
| Tareas relacionadas, si una falla no sirve seguir | `TaskGroup` |
| Tareas independientes, querés los resultados igual | `gather(..., return_exceptions=True)` |
| Necesitás los resultados en orden | `gather` (los devuelve ordenados) |
| Tareas de larga duración (workers) | `create_task` suelto, con referencia guardada |

`TaskGroup` no devuelve resultados directamente: hay que guardar las tasks y leer su `.result()` después.

---

## Sincronización: las primitivas de la clase 11, en versión async

La clase 20 dejó la regla: **hace falta lock solo si la sección crítica contiene un `await`**. Cuando hace falta, asyncio tiene las mismas primitivas que `threading`, con la misma semántica.

```python
import asyncio

lock = asyncio.Lock()
sem = asyncio.Semaphore(5)
evento = asyncio.Event()
```

Todas se usan con `async with` en vez de `with`, porque adquirirlas puede suspender la corrutina.

### Lock

```python
async with lock:
    saldo = cuentas[origen]
    await registrar(monto)              # el await que hace necesario el lock
    cuentas[origen] = saldo - monto
```

Sin él, el ejemplo de la clase 20 perdía 99 de 100 operaciones.

### Semaphore

Limita cuántas corrutinas hacen algo a la vez. Ya lo usamos para acotar descargas:

```python
sem = asyncio.Semaphore(10)

async def descargar(url):
    async with sem:                     # como mucho 10 simultáneas
        return await cliente.get(url)
```

La diferencia con una cola es sutil pero importante: el semáforo **no encola trabajo**, solo limita la concurrencia de tareas que ya existen. La cola además desacopla quién produce de quién consume.

### Event

Una bandera que las corrutinas pueden esperar. Sirve para coordinar el arranque o el apagado:

```python
listo = asyncio.Event()

async def esperar_arranque():
    await listo.wait()                  # se suspende hasta que alguien lo setee
    print('ya puedo trabajar')

async def inicializar():
    await cargar_configuracion()
    listo.set()                         # despierta a todos los que esperan
```

Es lo que usamos en la clase 20 para el cierre ordenado con señales.

### Condition y Barrier

También existen `asyncio.Condition` (esperar a que se cumpla una condición) y, desde 3.11, `asyncio.Barrier` (que N tareas se sincronicen en un punto). Son los equivalentes directos de la clase 11, y se usan poco: la mayoría de los casos se resuelven mejor con una cola.

> **Regla general:** si podés resolver algo con una `Queue`, hacelo. Los locks y eventos son necesarios, pero el código con colas es más fácil de razonar — no hay estado compartido que proteger, hay mensajes que viajan.

---

## Sacar el trabajo pesado del loop

Llegamos al tema que más importa para el TP2, y al límite estructural de asyncio.

### El problema, medido

Un cálculo de hash iterado que tarda unos 5 segundos, ejecutado dentro de una corrutina. Mientras tanto, otra tarea intenta despertarse cada 50 ms para medir si el loop responde:

| Cómo se ejecuta el cálculo | Duración | Peor atraso del loop |
|---------------------------|----------|---------------------|
| Directamente en la corrutina | 4.81 s | **4807 ms** |
| Con `ProcessPoolExecutor` | 4.21 s | 6.3 ms |
| Con `asyncio.to_thread` | 4.20 s | 6.1 ms |

El primer caso es catastrófico: el loop queda congelado **casi cinco segundos**. Ninguna otra tarea avanza, ningún pedido se atiende, ningún timeout se dispara. Desde afuera, el servidor está colgado.

Con executor, el peor atraso baja a 6 ms. El trabajo tarda lo mismo —el cálculo no se acelera— pero deja de bloquear a todos los demás.

### Las dos herramientas

```python
import asyncio
from concurrent.futures import ProcessPoolExecutor

# Para I/O bloqueante: un thread
contenido = await asyncio.to_thread(open('grande.txt').read)

# Para CPU: un proceso
pool = ProcessPoolExecutor(max_workers=4)
loop = asyncio.get_running_loop()
resultado = await loop.run_in_executor(pool, calculo_pesado, dato)
```

`asyncio.to_thread()` es azúcar sobre `run_in_executor` con el threadpool por defecto. Es lo que FastAPI usa por dentro con los endpoints `def`, como vimos en la clase 19.

### Cuál elegir: el GIL otra vez

Con **una** tarea pesada, threads y procesos dan casi lo mismo. La diferencia aparece con varias en paralelo:

| 4 tareas CPU-bound simultáneas | Tiempo |
|-------------------------------|--------|
| `asyncio.to_thread` (threads) | **11.53 s** |
| `ProcessPoolExecutor` (procesos) | **3.42 s** |

Tres veces y media de diferencia, y la razón es la de la clase 10: **el GIL**. Los cuatro threads se turnan para ejecutar bytecode, así que el trabajo se serializa. Los procesos tienen su propio intérprete y corren de verdad en paralelo.

La tabla de decisión, entonces:

| Qué hace tu función | Dónde ponerla |
|---------------------|---------------|
| Espera I/O con bibliotecas async | En el loop, con `await` |
| Espera I/O con bibliotecas bloqueantes | `asyncio.to_thread` |
| Calcula | `ProcessPoolExecutor` |
| Calcula poco (milisegundos) | En el loop, no vale la pena |

### El costo de los procesos

`ProcessPoolExecutor` no es gratis. Los argumentos y resultados viajan **pickleados** entre procesos, así que:

- Lo que mandes tiene que ser serializable (una función lambda no lo es)
- Mandar objetos grandes cuesta más que el cálculo, a veces
- Crear el pool lleva tiempo: hay que crearlo una vez y reutilizarlo

Por eso conviene crear el pool al arrancar la aplicación —en el `lifespan` de FastAPI, que vimos en las manijas de la clase 19— y no por pedido.

---

## Juntando todo: la arquitectura del TP2

Con lo de hoy, el diagrama del enunciado se puede leer completo:

```
   POST /tareas  ──>  asyncio.Queue  ──>  N workers (corrutinas)
                        (maxsize)              │
                                               ├─ I/O-bound: await directo
                                               └─ CPU-bound: run_in_executor
```

Las piezas y de dónde salen:

| Pieza | Clase |
|-------|-------|
| La API que recibe los pedidos | 19 |
| El event loop que lo corre todo | 18 |
| I/O de red sin bloquear | 20 |
| La cola que desacopla | hoy |
| Los workers que la consumen | hoy |
| El executor para lo que calcula | hoy |
| Cancelación y timeouts | 20 |
| El apagado ordenado | 20 y hoy |

Un esqueleto mínimo:

```python
from contextlib import asynccontextmanager
import asyncio
from concurrent.futures import ProcessPoolExecutor
from fastapi import FastAPI

@asynccontextmanager
async def ciclo(app):
    app.state.cola = asyncio.Queue(maxsize=100)
    app.state.pool = ProcessPoolExecutor(max_workers=2)
    app.state.workers = [
        asyncio.create_task(worker(app.state.cola, app.state.pool))
        for _ in range(4)
    ]
    yield
    for w in app.state.workers:
        w.cancel()
    await asyncio.gather(*app.state.workers, return_exceptions=True)
    app.state.pool.shutdown()

app = FastAPI(lifespan=ciclo)
```

No está completo —falta el estado de cada tarea, los endpoints, el manejo de errores— pero la estructura es esa.

---

## Conceptos clave

1. **`asyncio.Queue` desacopla productor de consumidores**: es productor-consumidor de la clase 11, entre corrutinas.
2. **`maxsize` es backpressure**: frena al productor en vez de dejar crecer la cola sin límite.
3. **`task_done()` va en un `finally`**, o `join()` espera para siempre.
4. **Un centinela apaga workers de forma ordenada**; cancelarlos los corta a mitad de trabajo.
5. **`gather` deja tareas huérfanas si una falla**; `TaskGroup` cancela a las hermanas.
6. **`except*` captura `ExceptionGroup`** y puede ejecutar varias ramas.
7. **Las primitivas async se usan con `async with`**, porque adquirirlas puede suspender.
8. **Si podés usar una cola en vez de un lock, usala**: no hay estado compartido que proteger.
9. **Cálculo dentro de una corrutina congela el loop**: medido, 4807 ms de atraso contra 6 ms con executor.
10. **Threads para I/O bloqueante, procesos para CPU**: con 4 tareas, 11.53 s contra 3.42 s por el GIL.
11. **El pool se crea una vez**, al arrancar, no por pedido.
12. **Los argumentos de `ProcessPoolExecutor` viajan pickleados**: no todo se puede mandar.

---

## Preparación para la próxima clase

En la **clase 22 (concurrent.futures)** profundizamos el módulo que hoy usamos de refilón: `Future`, `as_completed`, `map`, y el manejo de excepciones en executors. Es la API sincrónica equivalente, y la que van a usar cuando no haya un event loop de por medio.

Para llegar preparado:

- Corré `executor.py` y guardá los números de tu máquina.
- Con lo de hoy ya tenés todo lo obligatorio del TP2: armá el esqueleto con la cola y los workers.

---

## Referencias

- [asyncio: colas](https://docs.python.org/3/library/asyncio-queue.html)
- [asyncio: TaskGroup](https://docs.python.org/3/library/asyncio-task.html#task-groups)
- [asyncio: sincronización](https://docs.python.org/3/library/asyncio-sync.html)
- [PEP 654](https://peps.python.org/pep-0654/) - `ExceptionGroup` y `except*`
- [Notes on structured concurrency](https://vorpus.org/blog/notes-on-structured-concurrency-or-go-statement-considered-harmful/) - Nathaniel Smith, el texto que instaló la idea

---

*Computación II - 2026 - Clase 21*
