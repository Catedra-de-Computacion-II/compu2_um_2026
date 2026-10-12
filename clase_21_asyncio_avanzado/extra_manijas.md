# Clase 21: Asyncio avanzado - Extra Manijas

Material opcional para profundizar.

---

## Concurrencia estructurada: de dónde salió la idea

`TaskGroup` no se inventó en Python. Viene de un artículo de 2018 de Nathaniel Smith con un título provocador: *"Notes on structured concurrency, or: Go statement considered harmful"*.

El argumento es una analogía con la historia de la programación. En los años 60, Dijkstra escribió *"Go To Statement Considered Harmful"*: el `goto` permitía saltar a cualquier parte del programa, y eso hacía imposible razonar sobre el flujo. La solución fueron las estructuras de control —`if`, `while`, funciones— que **garantizan que lo que entra por arriba sale por abajo**.

Smith sostiene que `go func()` —y por extensión `create_task`, `thread.start()`, `gather`— es el `goto` de la concurrencia: lanzás algo que escapa del flujo del programa, y no hay forma de saber cuándo termina ni quién se hace cargo si falla.

La concurrencia estructurada impone la misma regla que las funciones: **una tarea no puede sobrevivir al bloque donde nació**. De ahí el `async with` de `TaskGroup`.

Las consecuencias prácticas son tres:

- **No hay tareas huérfanas.** Si el bloque terminó, todo lo que lanzó terminó.
- **Los errores no se pierden.** Una excepción en una tarea hija llega al padre.
- **La cancelación se propaga.** Cancelar el bloque cancela todo lo de adentro.

La biblioteca **Trio** nació para explorar estas ideas, y asyncio las fue adoptando: `TaskGroup` en 3.11, `asyncio.timeout()` en 3.11, y la mejora del manejo de `CancelledError` en 3.8.

---

## El problema de las tareas de fondo

La concurrencia estructurada tiene un caso incómodo: las tareas que **deben** sobrevivir al bloque.

Un worker que corre mientras el servidor está arriba no cabe en un `TaskGroup` de un endpoint. ¿Dónde vive entonces?

La respuesta es: en un `TaskGroup` de más arriba, del tamaño de su vida real. En FastAPI, eso es el `lifespan`:

```python
@asynccontextmanager
async def ciclo(app):
    async with asyncio.TaskGroup() as tg:
        for i in range(4):
            tg.create_task(worker(app.state.cola, i))
        app.state.tg = tg
        yield                          # el servidor atiende acá adentro
        # al salir, hay que cancelar o el TaskGroup espera para siempre
        for t in asyncio.all_tasks():
            ...
```

En la práctica eso se complica, porque un `TaskGroup` espera a que sus tareas terminen y los workers son bucles infinitos. Por eso en el TP2 conviene el enfoque más simple: `create_task` guardando las referencias, y cancelación explícita en el apagado.

La regla práctica: **`TaskGroup` para trabajo con principio y fin; `create_task` con referencia guardada para procesos de fondo**.

---

## Qué pasa si una tarea de fondo falla

Un detalle que muerde en producción: si una task lanza una excepción y **nadie la espera**, el error no aparece por ningún lado hasta que el recolector de basura destruye el objeto.

```python
async def worker(cola):
    while True:
        item = await cola.get()
        procesar(item)              # si esto lanza, el worker muere en silencio
```

El worker se cae, la cola se llena, y el servidor deja de procesar sin que nada lo avise.

Dos defensas. La primera es capturar adentro:

```python
async def worker(cola):
    while True:
        item = await cola.get()
        try:
            await procesar(item)
        except asyncio.CancelledError:
            raise                    # esta sí se relanza
        except Exception:
            logging.exception('falló procesando %r', item)
        finally:
            cola.task_done()
```

La segunda es un callback que avise:

```python
def vigilar(task):
    if not task.cancelled() and task.exception():
        logging.error('worker murió: %r', task.exception())

t = asyncio.create_task(worker(cola))
t.add_done_callback(vigilar)
```

En un sistema serio conviene además **reiniciar** el worker caído, o el servicio se degrada de a poco sin que nadie lo note.

---

## asyncio.Queue no es thread-safe

Una trampa que aparece al mezclar mundos: `asyncio.Queue` **no** sirve para comunicarse entre threads. Está pensada solo para corrutinas del mismo loop y no tiene locks internos.

Si un thread —por ejemplo uno del executor— necesita mandarle algo al loop, hay dos caminos:

```python
# Desde otro thread, agendar trabajo en el loop
loop.call_soon_threadsafe(cola.put_nowait, item)

# O correr una corrutina completa en el loop desde otro thread
futuro = asyncio.run_coroutine_threadsafe(cola.put(item), loop)
futuro.result(timeout=5)
```

Las dos funciones tienen `threadsafe` en el nombre justamente porque son las únicas de asyncio que se pueden llamar desde afuera del loop. **Todo el resto de la API asume que corre en el hilo del loop.**

Si necesitás una cola entre threads, usá `queue.Queue` de la stdlib, que sí es thread-safe pero bloquea —y por lo tanto no se puede usar directo desde una corrutina.

---

## Timeouts sobre un grupo entero

`asyncio.timeout()` se puede combinar con `TaskGroup` para acotar todo un conjunto de tareas:

```python
try:
    async with asyncio.timeout(10):
        async with asyncio.TaskGroup() as tg:
            tg.create_task(descargar('a'))
            tg.create_task(descargar('b'))
            tg.create_task(descargar('c'))
except TimeoutError:
    print('el lote no terminó en 10 segundos')
```

Si vence el timeout, se cancela el grupo entero y con él las tres descargas. Es más limpio que ponerle timeout a cada una por separado, porque lo que importa es el presupuesto total.

También existe `asyncio.timeout_at(instante)` para fijar un momento absoluto en vez de una duración, útil cuando varias etapas comparten una fecha límite.

---

## shield: lo que no hay que cancelar

A veces una operación no debe interrumpirse aunque cancelen la tarea que la lanzó — típicamente algo que dejaría estado inconsistente a la mitad.

```python
await asyncio.shield(guardar_en_base(datos))
```

`shield` protege la corrutina de adentro: si cancelan la externa, la protegida **sigue corriendo** hasta terminar.

Usalo con cuidado. Si algo no se puede cancelar, tampoco se puede acotar con timeout, y un `shield` mal puesto deja operaciones corriendo después de que el servidor pidió cerrar. La regla: protegé la escritura, no la espera.

---

## Medir el event loop en producción

El medidor de `executor.py` no es un juguete didáctico: es la métrica que más dice sobre la salud de un servidor async.

```python
async def monitor_del_loop(umbral_ms=100):
    while True:
        t0 = time.perf_counter()
        await asyncio.sleep(0.1)
        atraso = (time.perf_counter() - t0 - 0.1) * 1000
        if atraso > umbral_ms:
            logging.warning('el event loop se atrasó %.0f ms', atraso)
```

Un atraso alto significa que **alguien bloqueó el loop**, y la causa casi siempre es una de tres: un cálculo sin executor, una biblioteca sincrónica usada por error, o una corrutina que procesa una lista enorme sin ceder.

Asyncio trae algo parecido incorporado:

```python
asyncio.run(main(), debug=True)
```

Eso avisa de callbacks que tardan más de 100 ms, corrutinas nunca esperadas y tasks destruidas pendientes. En desarrollo conviene dejarlo siempre activo.

---

## Lecturas

- [Notes on structured concurrency](https://vorpus.org/blog/notes-on-structured-concurrency-or-go-statement-considered-harmful/) - Nathaniel Smith, 2018. El texto que originó `TaskGroup`
- [asyncio: colas](https://docs.python.org/3/library/asyncio-queue.html)
- [asyncio: sincronización](https://docs.python.org/3/library/asyncio-sync.html)
- [PEP 654](https://peps.python.org/pep-0654/) - `ExceptionGroup` y `except*`
- [asyncio: desarrollo con asyncio](https://docs.python.org/3/library/asyncio-dev.html) - la sección de modo debug
- [Trio](https://trio.readthedocs.io/) - la biblioteca donde se probaron estas ideas primero

---

*Computación II - 2026 - Clase 21*
