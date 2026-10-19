# Clase 22: concurrent.futures - Extra Manijas

Material opcional para profundizar.

---

## De dónde salió la palabra "future"

El concepto es de 1977, de un artículo de Henry Baker y Carl Hewitt. La idea que proponían era casi filosófica: **separar el momento en que se pide un valor del momento en que se necesita**.

En la programación secuencial los dos momentos son el mismo. Escribís `x = calcular()` y la línea siguiente no corre hasta que `x` tenga un valor. El pedido y la necesidad están pegados.

Baker y Hewitt notaron que casi nunca necesitás el valor en la línea siguiente. Normalmente lo necesitás varias líneas después, o dentro de un `if`, o nunca si el programa se va por otra rama. Todo ese tiempo intermedio es tiempo que el programa podría estar haciendo otra cosa.

El `Future` es el objeto que llena ese hueco. No es el valor: es **la promesa de que habrá un valor**, con una identidad propia que podés guardar, pasar por parámetro y meter en una lista.

El mismo concepto reapareció con nombres distintos en cada lenguaje:

| Lenguaje | Nombre |
|---|---|
| Python | `Future` (y `Task` en asyncio) |
| JavaScript | `Promise` |
| Java | `Future`, `CompletableFuture` |
| C++ | `std::future` |
| Rust | `Future` (pero perezoso, ver abajo) |
| Scala | `Future` |

La diferencia interesante es Rust: ahí un `Future` **no arranca** hasta que alguien lo espera. En Python arranca solo. Eso cambia todo el diseño del lenguaje alrededor, y es la razón por la que en Rust hace falta un "ejecutor" explícito.

---

## El deadlock que sí existe (y el que no)

Hay una advertencia que circula sobre no anidar executors. Vale la pena medirla, porque la mitad es falsa.

**Lo que no pasa:** un pool creado adentro de una tarea de otro pool funciona perfectamente.

```python
from concurrent.futures import ThreadPoolExecutor

def anidada():
    with ThreadPoolExecutor(max_workers=1) as ex:
        return ex.submit(lambda: 42).result()

with ThreadPoolExecutor(max_workers=1) as ex:
    print(ex.submit(anidada).result())   # imprime 42
```

Funciona porque cada executor tiene **sus propios threads**. El de adentro no compite por los del de afuera.

**Lo que sí pasa:** tareas del mismo pool esperándose entre sí.

```python
import time
from concurrent.futures import ThreadPoolExecutor

def espera_a(fut):
    return fut.result()

ex = ThreadPoolExecutor(max_workers=2)
a = ex.submit(time.sleep, 10)
b = ex.submit(espera_a, a)              # ocupa el worker 2 esperando a 'a'
c = ex.submit(lambda: "yo solo queria correr")

print(c.result(timeout=2))              # TimeoutError
```

Medido: `c` nunca corre. Los dos workers están ocupados —uno durmiendo, el otro esperando al que duerme— y `c` se queda en la cola para siempre. Con `max_workers=10` el síntoma desaparece, lo cual lo hace peor: es un bug que aparece solo bajo carga.

La regla es: **una tarea nunca debe esperar el resultado de una tarea de su propio pool**. Si necesitás esa dependencia, el pool no es la herramienta: lo que tenés es un grafo de dependencias, y eso se resuelve ordenando el trabajo afuera.

---

## chunksize: el parámetro que cambia todo

`map` tiene un tercer parámetro que en `ThreadPoolExecutor` se ignora y en `ProcessPoolExecutor` decide si el programa tarda un segundo o un minuto.

Con 200.000 tareas triviales (`lambda n: n * 2`) y 4 procesos:

| chunksize | Tiempo |
|---|---|
| 1 (default) | 72.64 s |
| 1000 | 0.30 s |

Doscientas cuarenta veces. El cálculo no cambió: lo que cambió es cuántas veces se cruzó la frontera entre procesos.

Con `chunksize=1`, cada número viaja solo: se serializa con pickle, se escribe en un pipe, se lee del otro lado, se deserializa, se calcula —una multiplicación— y el resultado vuelve por el mismo camino. El transporte cuesta miles de veces más que el trabajo.

Con `chunksize=1000`, viajan mil números por envío. El transporte se amortiza entre mil multiplicaciones.

Como referencia, los mismos 200.000 con threads tardan 9.44 s: ahí no hay pickle ni pipes, pero el GIL no deja paralelizar nada y además se paga la coordinación de 200.000 tareas.

La regla práctica: **si las tareas son más rápidas que un milisegundo, subí el chunksize**. Un punto de partida razonable es `len(datos) // (max_workers * 4)`, que es lo que hace `multiprocessing.Pool` por default. Si cada tarea dura segundos, dejalo en 1: ahí el transporte es despreciable y conviene el reparto fino, porque un chunk grande puede dejar a un worker con todo el trabajo pesado mientras los otros terminaron.

Y la lectura de fondo, que es la de la clase 14: **el paralelismo con procesos tiene un costo fijo por tarea, y hay un tamaño de tarea por debajo del cual nunca conviene**.

---

## initializer: estado que vive en el worker

Un caso frecuente: cada tarea necesita algo caro de armar —una conexión a la base, un modelo cargado en memoria, un cliente HTTP— y armarlo por tarea sería absurdo.

```python
from concurrent.futures import ProcessPoolExecutor
import os

conexion = None

def arrancar():
    global conexion
    conexion = abrir_conexion()        # una vez por worker
    print(f"init en pid {os.getpid()}")

with ProcessPoolExecutor(max_workers=3, initializer=arrancar) as ex:
    list(ex.map(consultar, range(1000)))
```

Medido con 3 workers y 30 tareas, el initializer corre **3 veces**, una por proceso, no 30. El estado queda en una global de cada worker y las tareas lo encuentran ahí.

Es la contracara de lo que vimos: normalmente las globales no se comparten entre procesos, y acá eso es justamente la ventaja. Cada worker tiene su conexión, sin locks, sin coordinación.

Lo que no hay que hacer con esto es guardar estado que las tareas **modifiquen** y que importe después. Si el worker muere, se pierde; si hay N workers, hay N copias divergentes. Sirve para recursos de solo lectura o reconstruibles, no para resultados.

---

## Por qué existen dos APIs para lo mismo

`multiprocessing.Pool` ya hacía casi todo esto, y es anterior. Entonces, ¿por qué se agregó `concurrent.futures` en 3.2?

Las diferencias concretas:

| | `multiprocessing.Pool` | `ProcessPoolExecutor` |
|---|---|---|
| Hermano para threads | `multiprocessing.dummy` (poco usado) | `ThreadPoolExecutor`, misma interfaz |
| Objeto de resultado | `AsyncResult` | `Future`, compartido con asyncio |
| Un worker muere | el pool puede colgarse | `BrokenProcessPool` en todos los futures |
| Recolección por orden de fin | `imap_unordered` | `as_completed` |
| Callbacks | en `apply_async` | `add_done_callback` |

Lo decisivo es la primera y la segunda fila. `concurrent.futures` no se agregó porque hiciera algo nuevo, sino porque **unificó la interfaz**: el mismo código corre con threads o procesos, y el `Future` que devuelve es el mismo tipo que usa `run_in_executor` de asyncio. Esa compatibilidad es lo que permite el puente de la clase 21.

`multiprocessing.Pool` sigue existiendo y tiene cosas que el executor no: `imap` perezoso para datos que no caben en memoria, `starmap` para funciones de varios argumentos, y un control más fino del arranque. Para código nuevo, el executor es el default; `Pool` aparece cuando hace falta algo de esa lista.

---

## BrokenProcessPool: cuando un worker se muere

Hay una falla que no es una excepción de la tarea, y que conviene conocer antes de encontrarla.

Si un proceso worker muere de forma no controlada —un `kill -9`, el OOM killer, un segfault en una extensión C, un `os._exit()`— el pool entero queda inservible. Todos los futures pendientes fallan con `BrokenProcessPool` y cualquier `submit()` posterior también.

```python
import os
from concurrent.futures import ProcessPoolExecutor

def suicida():
    os._exit(1)        # no es una excepcion: el proceso desaparece

with ProcessPoolExecutor(max_workers=2) as ex:
    try:
        ex.submit(suicida).result()
    except Exception as e:
        print(type(e).__name__)        # BrokenProcessPool
```

Es deliberado: el pool no puede saber si el worker alcanzó a dejar estado corrupto, así que falla entero en lugar de seguir con garantías dudosas. `ThreadPoolExecutor` no tiene el problema equivalente, porque un thread no puede morir sin matar al proceso entero.

La consecuencia de diseño es que **un servidor de larga vida necesita poder recrear su pool**. Si el pool se creó en el `lifespan` de FastAPI y se rompe a las tres semanas, no hay a quién pedirle uno nuevo. Las soluciones son `max_tasks_per_child` (3.11+, recicla workers periódicamente) o un envoltorio que detecte el `BrokenProcessPool` y reconstruya.

---

## max_workers: de dónde salen los defaults

Los dos executors eligen muy distinto si no les decís nada.

`ThreadPoolExecutor`: `min(32, os.cpu_count() + 4)`. En una máquina de 8 núcleos, 12 threads. El `+4` existe porque se asume trabajo I/O-bound: los threads van a estar esperando, no calculando, así que conviene tener más que núcleos. El techo de 32 está para que una máquina de 64 núcleos no abra 68 threads cuando casi nadie los necesita.

`ProcessPoolExecutor`: `os.cpu_count()`. Ni uno más. Acá se asume CPU-bound, y más procesos que núcleos solo agrega cambios de contexto y memoria.

Los dos defaults codifican el supuesto sobre para qué se usa cada uno. Y los dos se quedan cortos en el caso que más aparece en la práctica: 200 descargas concurrentes necesitan bastante más de 12 threads, y ahí el número correcto no sale de los núcleos sino de cuánta concurrencia tolera el servidor del otro lado.

Que es, dicho de otro modo, la razón por la que para 10.000 conexiones nada de esto alcanza. Un thread tiene un costo de memoria fijo —el stack— que no se puede amortizar. Esa es la frontera que cruzamos con asyncio en la clase 18: ahí la unidad de concurrencia es una corrutina, que cuesta cientos de bytes en lugar de megabytes.

---

## Lecturas

- **PEP 3148** — la propuesta de `concurrent.futures`. Corta y clara sobre por qué unificar la interfaz.
- Baker y Hewitt, *The Incremental Garbage Collection of Processes* (1977) — el artículo donde aparece el concepto de future, en un contexto completamente distinto.
- La documentación de `concurrent.futures`, sección "ProcessPoolExecutor": las advertencias sobre picklabilidad y deadlocks están todas ahí, y se leen mucho mejor después de haberlas provocado.
- Para quien quiera ver la frontera desde el otro lado: la documentación de `loop.run_in_executor` y de `asyncio.to_thread`.

---

*Computación II - 2026 - Clase 22*
