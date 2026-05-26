# Clase 8: Multiprocessing Avanzado

## Retomando

En la clase 7 vimos los fundamentos de `multiprocessing`: cómo crear procesos con `Process`, comunicarlos básicamente con `Queue` y `Pipe`, los métodos de arranque (`fork`/`spawn`/`forkserver`) y los daemon processes.

Pero crear procesos uno por uno se vuelve incómodo cuando tenés cientos o miles de tareas. Y comunicarlos solo con `Queue` se queda corto cuando necesitás compartir estructuras de datos completas. Esta clase cubre las herramientas avanzadas del módulo que resuelven esos problemas:

- **Pool**: paralelizar tareas masivamente
- **Memoria compartida** con `Value`, `Array` y `Manager`: conectando con lo que vimos en mmap (clase 6)
- **Patrones**: Map-Reduce y Pipeline de procesos

> **Nota sobre sincronización**: cuando varios procesos acceden a memoria compartida, aparecen condiciones de carrera (race conditions). Las **primitivas de sincronización** (Lock, Semaphore, Event, Condition) las veremos en detalle en las clases 10 y 11. En esta clase mencionaremos algunas brevemente al usar memoria compartida, pero el estudio formal viene más adelante.

---

## Pool: el caballo de batalla

`Pool` mantiene un conjunto fijo de procesos worker listos para ejecutar tareas. En vez de crear un proceso por cada tarea (caro), reutiliza los workers. Es la herramienta más usada de `multiprocessing` en la práctica.

```python
from multiprocessing import Pool
import time

def procesar(x):
    time.sleep(0.5)  # Simular trabajo
    return x ** 2

if __name__ == "__main__":
    # Crear pool con 4 procesos
    with Pool(4) as pool:
        # map: aplica función a cada elemento (bloquea hasta terminar todo)
        resultados = pool.map(procesar, range(10))
        print(f"map: {resultados}")
```

### Métodos principales de Pool

Pool tiene varios métodos que se diferencian en tres ejes:
- **Cuándo devuelven resultados**: todos al final vs uno por uno
- **Si preservan el orden**: sí, no, o no importa
- **Cómo pasás los argumentos**: un solo argumento o múltiples

Tabla rápida y después explicamos cada uno:

| Método | Cuándo devuelve | Orden | Bloquea | Argumentos |
|--------|-----------------|-------|---------|------------|
| `map` | Al final, todos juntos | Preservado | Sí | Un solo arg por tarea |
| `imap` | Uno a uno (lazy) | Preservado | Sí (sobre cada item) | Un solo arg por tarea |
| `imap_unordered` | Uno a uno (lazy) | El que termina primero | Sí (sobre cada item) | Un solo arg por tarea |
| `apply_async` | Cuando vos lo pedís | N/A (una sola tarea) | No, devuelve un Future | Múltiples (como argumentos normales) |
| `starmap` | Al final, todos juntos | Preservado | Sí | Múltiples (desempaquetados) |
| `starmap_async` | Cuando vos lo pedís | Preservado | No, devuelve un Future | Múltiples (desempaquetados) |

#### `map(func, iterable)` — el más común

Aplica `func` a cada elemento del iterable, en paralelo entre los workers del pool, y devuelve una **lista con los resultados en el mismo orden** del iterable de entrada. **Bloquea hasta que todas las tareas terminen**.

```python
with Pool(4) as pool:
    resultados = pool.map(procesar, range(10))
    # resultados[0] corresponde a procesar(0), resultados[1] a procesar(1), etc.
```

Usalo cuando:
- Tenés una lista de tareas y querés todos los resultados al final
- Te interesa que el orden de salida coincida con el de entrada
- No te importa esperar a que todas terminen para empezar a procesar

#### `imap(func, iterable)` — para resultados streaming

Similar a `map`, pero en vez de devolver una lista al final, devuelve un **iterador**. Vos podés empezar a consumir los resultados a medida que van llegando, **respetando el orden original**.

```python
with Pool(4) as pool:
    for r in pool.imap(procesar, range(10)):
        print(f"Recibido: {r}")  # imprime apenas el primero está listo
```

La diferencia con `map` es importante: si tenés 10000 tareas, `map` te obliga a esperar a que las 10000 terminen y construir una lista de 10000 elementos en memoria. `imap` te deja procesar cada resultado apenas está listo, sin acumular nada.

Usalo cuando:
- Tenés muchas tareas y no querés esperar a todas
- Querés ir mostrando progreso a medida que terminan
- El procesamiento de cada resultado también lleva tiempo (pipelining natural)

Hay un detalle: como respeta el orden, si la tarea 0 tarda 10s y la tarea 1 tarda 1s, vas a recibir primero el resultado de 0 (cuando termine) y después el de 1 — aunque 1 haya terminado mucho antes.

#### `imap_unordered(func, iterable)` — el más rápido cuando no importa el orden

Como `imap`, pero **no respeta el orden**: te entrega los resultados **en el orden en que las tareas terminan**.

```python
with Pool(4) as pool:
    for r in pool.imap_unordered(procesar, range(10)):
        print(f"Terminó: {r}")  # llega el primero que terminó, sin importar su índice
```

Esto es más rápido en la práctica porque ningún worker se queda "esperando" a uno más lento solo para mantener el orden.

Usalo cuando:
- Las tareas tardan tiempos muy distintos
- No te importa el orden de salida
- Querés máxima velocidad

Ejemplo típico: descargar 100 archivos. No te importa el orden en que se terminan de descargar; querés procesarlos apenas estén disponibles.

#### `apply(func, args)` y `apply_async(func, args)` — para una sola tarea

`apply` ejecuta una sola tarea en el pool y espera el resultado (bloquea). En la práctica casi no se usa porque es equivalente a llamar la función directamente — el sentido de un pool es paralelizar.

`apply_async` es más interesante: **lanza una tarea sin esperar** y devuelve un objeto `AsyncResult`. Después podés pedir el valor cuando lo necesites.

```python
with Pool(4) as pool:
    # Lanzar 3 tareas asíncronas que corren en paralelo
    futuro_a = pool.apply_async(procesar, (10,))
    futuro_b = pool.apply_async(procesar, (20,))
    futuro_c = pool.apply_async(procesar, (30,))

    # Hacer otras cosas mientras tanto...
    print("Esperando...")

    # Cuando necesito los valores
    print(f"a = {futuro_a.get()}")
    print(f"b = {futuro_b.get()}")
    print(f"c = {futuro_c.get()}")
```

El `AsyncResult` tiene métodos útiles:

```python
futuro = pool.apply_async(procesar, (10,))

futuro.ready()                    # True si terminó (no bloquea)
futuro.successful()               # True si terminó sin excepción
futuro.wait(timeout=2)            # espera hasta 2 segundos
futuro.get(timeout=5)             # devuelve resultado o lanza TimeoutError
```

Usalo cuando:
- Querés disparar pocas tareas heterogéneas (no un map sobre lista)
- Necesitás control fino sobre cada tarea (timeout, errores)
- Querés mezclar ejecución en background con trabajo en el main

#### `starmap(func, iterable_de_tuplas)` — para funciones con múltiples argumentos

`map` solo le pasa **un argumento** a la función por cada elemento del iterable. Si tu función toma dos o más argumentos, necesitás `starmap`, que **desempaqueta cada tupla** del iterable como argumentos posicionales.

```python
def sumar(a, b):
    return a + b

with Pool(4) as pool:
    # Con map tendrías que pasar tuplas y desempaquetar adentro:
    # resultados = pool.map(lambda t: sumar(*t), [(1,2), (3,4)])  # (no funciona, lambdas no se pickle-an)

    # Con starmap es directo:
    resultados = pool.starmap(sumar, [(1, 2), (3, 4), (5, 6)])
    # equivale a: [sumar(1,2), sumar(3,4), sumar(5,6)] → [3, 7, 11]
```

El nombre viene del operador `*` de Python que desempaqueta: `sumar(*(1,2))` es igual a `sumar(1, 2)`. `starmap` aplica eso automáticamente.

#### `starmap_async` y los demás `_async`

Casi todos los métodos tienen una versión asíncrona (`map_async`, `starmap_async`) que devuelven un `AsyncResult` en lugar de bloquear. Útil cuando querés disparar el procesamiento en paralelo con otra cosa que el programa principal está haciendo.

```python
with Pool(4) as pool:
    # Disparar el procesamiento sin bloquear
    futuro = pool.map_async(procesar, range(100))

    # Hacer otras cosas en el main
    print("Procesamiento corriendo en background...")

    # Cuando necesite los resultados
    resultados = futuro.get()  # ahora sí bloquea hasta tener todo
```

#### Ejemplo completo combinando varios métodos

```python
from multiprocessing import Pool
import time
import random

def procesar(x):
    """Tarea con duración variable."""
    time.sleep(random.uniform(0.1, 1.0))
    return x ** 2

def sumar(a, b):
    return a + b

if __name__ == "__main__":
    with Pool(4) as pool:
        # map: todos al final, en orden
        print("=== map ===")
        print(pool.map(procesar, range(5)))

        # imap_unordered: a medida que terminan
        print("\n=== imap_unordered ===")
        for r in pool.imap_unordered(procesar, range(5)):
            print(f"  llegó: {r}")

        # apply_async: tareas individuales con control fino
        print("\n=== apply_async ===")
        f1 = pool.apply_async(procesar, (10,))
        f2 = pool.apply_async(procesar, (20,))
        print(f"  f1 listo? {f1.ready()}")
        print(f"  resultados: {f1.get()}, {f2.get()}")

        # starmap: función con múltiples argumentos
        print("\n=== starmap ===")
        print(pool.starmap(sumar, [(1, 2), (3, 4), (5, 6)]))
```

### Comparación de rendimiento

El verdadero valor de Pool aparece con tareas CPU-bound. Veamos un ejemplo:

```python
from multiprocessing import Pool
import time

def cpu_intensive(n):
    """Tarea que usa mucho CPU."""
    return sum(i * i for i in range(n))

N = 1_000_000
TAREAS = 8

if __name__ == "__main__":
    # Secuencial
    inicio = time.time()
    resultados = [cpu_intensive(N) for _ in range(TAREAS)]
    print(f"Secuencial: {time.time() - inicio:.2f}s")

    # Con Pool de 4 procesos
    inicio = time.time()
    with Pool(4) as pool:
        resultados = pool.map(cpu_intensive, [N] * TAREAS)
    print(f"Pool(4): {time.time() - inicio:.2f}s")
```

En una máquina con 4 cores, la versión con Pool debería ser cercana a 4× más rápida. Cada proceso tiene su propio intérprete de Python ejecutando en paralelo en un core distinto, así que verdaderamente se aprovechan los múltiples cores del CPU.

### ¿Cuántos workers usar?

La regla general es **tantos workers como cores de CPU tengas** para tareas CPU-bound. Podés obtener ese número con:

```python
import os
import multiprocessing

print(os.cpu_count())                # cores físicos + lógicos (con hyperthreading)
print(multiprocessing.cpu_count())   # equivalente

# Pool sin argumentos usa os.cpu_count() automáticamente
with Pool() as pool:
    ...
```

Más workers que cores no acelera nada (los procesos se pelean por el CPU) y solo agrega overhead.

---

## Memoria compartida con `multiprocessing`

En la clase 6 vimos `mmap` directamente: el mecanismo del SO para compartir memoria entre procesos. `multiprocessing` provee envoltorios más cómodos sobre esa misma idea.

### `Value`: compartir un valor simple

```python
from multiprocessing import Process, Value

def incrementar(contador, cantidad):
    for _ in range(cantidad):
        # get_lock() previene race conditions (lo vemos formalmente en clase 10)
        with contador.get_lock():
            contador.value += 1

if __name__ == "__main__":
    # Tipos: 'i' = int, 'd' = double, 'b' = byte, etc.
    contador = Value('i', 0)

    procesos = [Process(target=incrementar, args=(contador, 10000))
                for _ in range(4)]

    for p in procesos:
        p.start()
    for p in procesos:
        p.join()

    print(f"Contador final: {contador.value}")  # 40000
```

`Value('i', 0)` reserva 4 bytes en una región de memoria compartida y los inicializa en 0. Por debajo usa `mmap` anónimo, igual que vimos. La diferencia es que no tenés que serializar manualmente: accedés con `.value`.

> **Atención**: si varios procesos modifican `contador.value` sin lock, se pisan entre sí — eso es una **race condition**. La línea `with contador.get_lock():` lo previene. Veremos esto en profundidad en clase 10.

### `Array`: compartir una secuencia

```python
from multiprocessing import Process, Array

def modificar(arr, idx):
    arr[idx] = arr[idx] ** 2

if __name__ == "__main__":
    numeros = Array('i', [1, 2, 3, 4, 5])  # array compartido

    procesos = [Process(target=modificar, args=(numeros, i))
                for i in range(5)]

    for p in procesos:
        p.start()
    for p in procesos:
        p.join()

    print(f"Array: {list(numeros)}")  # [1, 4, 9, 16, 25]
```

`Array` también vive en memoria compartida vía `mmap`. Soporta los mismos tipos que `Value`.

### `Manager`: estructuras complejas compartidas

Para diccionarios, listas, namespaces, etc., usamos `Manager`. La diferencia con `Value`/`Array` es importante: el Manager **arranca un proceso aparte** que mantiene las estructuras y los demás procesos se comunican con él vía IPC.

```python
from multiprocessing import Process, Manager

def worker(d, l, id):
    d[id] = id ** 2
    l.append(id)

if __name__ == "__main__":
    with Manager() as manager:
        d = manager.dict()
        l = manager.list()

        procesos = [Process(target=worker, args=(d, l, i)) for i in range(5)]

        for p in procesos:
            p.start()
        for p in procesos:
            p.join()

        print(f"Dict: {dict(d)}")
        print(f"List: {list(l)}")
```

### Tabla comparativa: cuándo usar qué

| Mecanismo | Velocidad | Tipos | Casos de uso |
|-----------|-----------|-------|--------------|
| `Value`/`Array` | Alta (mmap directo) | Tipos primitivos de C (int, double, char...) | Contadores, arrays numéricos, flags |
| `Manager.dict/list/...` | Baja (IPC vía socket interno) | Objetos Python arbitrarios | Estructuras complejas, prototipos |
| `shared_memory` (3.8+) | Alta | Bytes crudos | Compartir bloques grandes entre procesos independientes (vimos en clase 6) |
| `Queue`/`Pipe` | Media | Picklables | Pasar mensajes, no compartir estado |

La regla: **si necesitás velocidad y son datos simples, `Value`/`Array`. Si necesitás conveniencia y son datos complejos, `Manager`.**

---

## Patrones comunes

### Map-Reduce

Patrón clásico para procesar grandes volúmenes de datos en paralelo: dividir, procesar en paralelo, combinar.

> **¿Qué es `reduce`?**
> `reduce` es una función del módulo `functools` que **combina los elementos de una secuencia aplicando una función de dos argumentos de forma acumulativa**. Empieza con los dos primeros, los combina, el resultado lo combina con el tercero, y así sucesivamente hasta procesar toda la lista.
>
> ```python
> from functools import reduce
>
> # Sumar todos los números de una lista
> reduce(lambda a, b: a + b, [1, 2, 3, 4])
> # paso 1: (1, 2) → 3
> # paso 2: (3, 3) → 6
> # paso 3: (6, 4) → 10
> # resultado: 10
> ```
>
> Es decir, aplica `func` "acumulativamente" reduciendo la lista a un solo valor. En el patrón Map-Reduce: `map` produce muchos resultados en paralelo, `reduce` los combina secuencialmente en uno solo.

```python
from multiprocessing import Pool
from functools import reduce

def mapper(texto):
    """Cuenta palabras en un texto."""
    palabras = texto.lower().split()
    conteo = {}
    for p in palabras:
        conteo[p] = conteo.get(p, 0) + 1
    return conteo

def reducer(dict1, dict2):
    """Combina dos diccionarios de conteo."""
    resultado = dict1.copy()
    for palabra, count in dict2.items():
        resultado[palabra] = resultado.get(palabra, 0) + count
    return resultado

if __name__ == "__main__":
    textos = [
        "hola mundo hola",
        "mundo cruel mundo",
        "hola hola hola"
    ]

    with Pool(3) as pool:
        # Map: contar en paralelo
        conteos = pool.map(mapper, textos)

        # Reduce: combinar resultados (secuencial)
        resultado = reduce(reducer, conteos)

    print(resultado)
    # {'hola': 5, 'mundo': 3, 'cruel': 1}
```

Este patrón escala bien: si tenés 1000 archivos para procesar, podés dividirlos entre los workers y cada uno trabaja en paralelo.

### Pipeline de procesos

Otro patrón clásico: una cadena de etapas donde cada una transforma los datos y los pasa a la siguiente. Cada etapa corre en su propio proceso.

```python
from multiprocessing import Process, Queue

def etapa1(input_q, output_q):
    """Multiplica por 2."""
    while True:
        item = input_q.get()
        if item is None:
            output_q.put(None)  # propagar señal de fin
            break
        output_q.put(item * 2)

def etapa2(input_q, output_q):
    """Suma 10."""
    while True:
        item = input_q.get()
        if item is None:
            output_q.put(None)
            break
        output_q.put(item + 10)

if __name__ == "__main__":
    q1 = Queue()
    q2 = Queue()
    q3 = Queue()

    p1 = Process(target=etapa1, args=(q1, q2))
    p2 = Process(target=etapa2, args=(q2, q3))

    p1.start()
    p2.start()

    # Alimentar pipeline
    for i in range(5):
        q1.put(i)
    q1.put(None)  # señal de fin

    # Recoger resultados
    while True:
        result = q3.get()
        if result is None:
            break
        print(f"Resultado: {result}")  # 10, 12, 14, 16, 18

    p1.join()
    p2.join()
```

Este patrón es útil cuando las etapas son de naturaleza distinta (ej: leer archivo → parsear → transformar → guardar). Cada etapa puede tener su propio ritmo, y el pipeline absorbe diferencias gracias a las queues.

---

## Consideraciones prácticas

### Serialización (pickle)

Todo lo que viaja entre procesos (argumentos, resultados, items de queues) se serializa con `pickle`. Esto implica:

```python
from multiprocessing import Pool

# Esto funciona: función nombrada en el módulo
def duplicar(x):
    return x * 2

# Esto NO funciona: lambdas no son picklables
# with Pool() as p:
#     p.map(lambda x: x * 2, range(10))  # PicklingError

# Esto NO funciona: funciones definidas dentro de otra función
def crear_funcion():
    def interna(x):
        return x * 3
    return interna

# Esto tampoco: objetos con sockets, file handles, conexiones abiertas, etc.
```

En general, lo que pasés a un proceso hijo tiene que ser:
- Funciones nombradas a nivel de módulo (no lambdas, no closures)
- Tipos básicos (int, str, list, dict...) o clases picklables
- Sin handles abiertos (archivos, sockets, conexiones)

### Overhead

Crear procesos es **caro**. Una mala práctica es crear un proceso por tarea pequeña:

```python
# MAL: crea/destruye proceso por cada tarea
for i in range(1000):
    p = Process(target=func, args=(i,))
    p.start()
    p.join()

# BIEN: reutiliza los workers del pool
with Pool(4) as pool:
    pool.map(func, range(1000))
```

Con `Pool` los 4 workers se crean una sola vez al inicio y se reutilizan. La diferencia de performance puede ser de **decenas de veces** más rápido.

### ¿Cuándo conviene multiprocessing?

| Caso | ¿multiprocessing? |
|------|------------------|
| Procesar muchos archivos en paralelo | Sí |
| Cálculos numéricos pesados (CPU-bound) | Sí |
| Compresión/descompresión de datos | Sí |
| Esperar respuestas de la red (I/O-bound) | No, mejor async (clases 19-21) |
| Servir muchas conexiones cortas | No, mejor threads o async |
| Operación rápida (< 10ms cada una) | No, el overhead come la ganancia |

La regla mental: **multiprocessing tiene sentido cuando el costo de la tarea individual es mucho mayor que el costo de serializar argumentos y resultados.**

---

## Conceptos clave

1. **`Pool` reutiliza workers** — Forma estándar de paralelizar tareas masivas
2. **`Value` y `Array`** son envoltorios de mmap para datos simples compartidos
3. **`Manager`** es más flexible pero más lento, ideal para estructuras complejas
4. **Map-Reduce y Pipeline** son los dos patrones más comunes
5. **Pickle limita qué se puede pasar** entre procesos
6. **Overhead alto** — multiprocessing vale la pena solo si la tarea es significativa

---

## Preparación para la próxima clase

En la **clase 9 (Threading)** vamos a ver el otro modelo de concurrencia: hilos dentro de un mismo proceso. Veremos:

- Qué son los threads y en qué se diferencian de los procesos
- El **GIL (Global Interpreter Lock)** y por qué los threads de Python no escalan en CPU-bound
- Por qué entonces sirven (I/O-bound)
- El módulo `threading` y sus primitivas
- Conexión con lo que vimos hoy: `Pool` y `ThreadPoolExecutor` son la misma idea, pero con threads en lugar de procesos

Y a partir de la clase 10 entramos a **sincronización formal**: los Locks, Semáforos, Events y Conditions que hoy mencionamos solo de pasada.

---

*Computación II - 2026 - Clase 8*
