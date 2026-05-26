# Clase 8: Multiprocessing Avanzado - Ejercicios Prácticos

> **Antes de empezar**: estos ejercicios asumen que ya viste los fundamentos de `multiprocessing` (`Process`, `Queue`, `Pipe` básico) de la clase 7. Acá nos enfocamos en `Pool`, memoria compartida y patrones.

---

## Ejercicio 1: Conociendo los métodos de Pool

**Objetivo:** Explorar los distintos métodos de Pool y entender cuándo conviene cada uno.

**Consigna:** ejecutá el siguiente programa y observá las diferencias entre `map`, `imap`, `imap_unordered`, `starmap` y `apply_async`. Modificá la duración aleatoria (`time.sleep`) y observá cómo cambia el orden de salida en `imap` vs `imap_unordered`.

```python
#!/usr/bin/env python3
"""Explorar los métodos de Pool."""
from multiprocessing import Pool
import time
import random

def cuadrado(x):
    """Tarea con duración variable para apreciar las diferencias."""
    duracion = random.uniform(0.1, 1.0)
    time.sleep(duracion)
    return x ** 2

def suma(a, b):
    return a + b

if __name__ == "__main__":
    with Pool(4) as pool:
        # map: síncrono, ordenado, bloquea hasta tener todo
        print("== map ==")
        print(pool.map(cuadrado, range(8)))

        # map_async: igual pero asíncrono
        print("\n== map_async ==")
        async_result = pool.map_async(cuadrado, range(8))
        print(f"ready inmediatamente? {async_result.ready()}")
        print(f"resultados: {async_result.get()}")

        # imap: iterador lazy, mantiene orden
        print("\n== imap (mantiene orden) ==")
        for r in pool.imap(cuadrado, range(8)):
            print(f"  llegó: {r}")

        # imap_unordered: lazy, sin orden (más rápido)
        print("\n== imap_unordered (orden de finalización) ==")
        for r in pool.imap_unordered(cuadrado, range(8)):
            print(f"  llegó: {r}")

        # starmap: función con múltiples argumentos
        print("\n== starmap ==")
        print(pool.starmap(suma, [(1, 2), (3, 4), (5, 6)]))

        # apply_async: control fino sobre tareas individuales
        print("\n== apply_async ==")
        resultado = pool.apply_async(cuadrado, (10,))
        print(f"ready? {resultado.ready()}")
        print(f"resultado: {resultado.get()}")
```

**Preguntas para reflexionar:**
- ¿Por qué `imap_unordered` puede ser más rápido que `imap` en la práctica?
- ¿Cuándo conviene usar `apply_async` en lugar de `map`?
- ¿Qué pasaría si la duración de las tareas fuera constante?

---

## Ejercicio 2: Comparación secuencial vs paralelo

**Objetivo:** Verificar empíricamente la ganancia de paralelismo en tareas CPU-bound.

**Consigna:** implementá una función CPU-intensive y compará el tiempo de ejecución secuencial contra Pool con distintos números de workers (1, 2, 4, 8). Graficá o tabulá los resultados.

```python
#!/usr/bin/env python3
"""Speedup de multiprocessing con tareas CPU-bound."""
from multiprocessing import Pool
import time
import math

def cpu_task(n):
    """Tarea CPU-intensive: sumar raíces cuadradas."""
    return sum(math.sqrt(i) for i in range(n))

N = 500_000
TAREAS = 8

if __name__ == "__main__":
    # Secuencial
    inicio = time.time()
    resultados = [cpu_task(N) for _ in range(TAREAS)]
    t_seq = time.time() - inicio
    print(f"Secuencial:  {t_seq:.2f}s")

    # Con distintos números de workers
    for workers in [1, 2, 4, 8]:
        inicio = time.time()
        with Pool(workers) as pool:
            resultados = pool.map(cpu_task, [N] * TAREAS)
        t_par = time.time() - inicio
        speedup = t_seq / t_par
        print(f"Pool({workers}):    {t_par:.2f}s  (speedup: {speedup:.2f}x)")
```

**Esperado:** speedup cercano a N para N workers, hasta saturar los cores del CPU. A partir de ahí, agregar más workers no acelera (o incluso ralentiza por overhead).

---

## Ejercicio 3: Memoria compartida con Value y Array

**Objetivo:** Practicar el uso de memoria compartida con tipos simples.

**Consigna:** implementá un sistema donde varios procesos incrementan un contador compartido y, en paralelo, otro grupo llena un array compartido con resultados. Usá `Value` con `get_lock()` para evitar race conditions en el contador.

> **Nota:** la sincronización formal (Lock, Semaphore, etc.) la vemos en clase 10. Acá usamos `get_lock()` que es un método integrado de `Value`.

```python
#!/usr/bin/env python3
"""Memoria compartida con Value y Array."""
from multiprocessing import Process, Value, Array
import time

def incrementar(contador, n_veces, id):
    for _ in range(n_veces):
        # get_lock() previene race conditions (estudiado formalmente en clase 10)
        with contador.get_lock():
            contador.value += 1
    print(f"Worker {id} terminó sus {n_veces} incrementos")

def llenar_array(arr, valor_inicial, id):
    """Cada worker llena su segmento del array."""
    inicio = id * (len(arr) // 4)
    fin = inicio + (len(arr) // 4)
    for i in range(inicio, fin):
        arr[i] = valor_inicial + i

if __name__ == "__main__":
    # Value compartido con auto-lock
    contador = Value('i', 0)

    procs = [Process(target=incrementar, args=(contador, 10000, i))
             for i in range(4)]

    for p in procs:
        p.start()
    for p in procs:
        p.join()

    print(f"\nContador final: {contador.value}")
    assert contador.value == 40000, "¡Race condition! Falta el lock"

    # Array compartido, particionado por worker
    arr = Array('i', 100)
    procs = [Process(target=llenar_array, args=(arr, 1000, i))
             for i in range(4)]

    for p in procs:
        p.start()
    for p in procs:
        p.join()

    print(f"Array completo (primeros 10): {list(arr)[:10]}")
    print(f"Array completo (últimos 10): {list(arr)[-10:]}")
```

**Preguntas:**
- ¿Qué pasa si quitás el `with contador.get_lock():`?
- ¿Necesitarías un lock para el `Array` en este caso? ¿Por qué no?

---

## Ejercicio 4: Manager para estructuras complejas

**Objetivo:** Usar `Manager` para compartir un diccionario y una lista entre procesos.

**Consigna:** simulá un sistema donde 5 workers reportan su estado (status y resultado) en un diccionario compartido, y agregan un mensaje a una lista compartida. Al final, el padre muestra todos los resultados.

```python
#!/usr/bin/env python3
"""Usar Manager para compartir estructuras complejas."""
from multiprocessing import Process, Manager
import time
import random

def worker(shared_dict, shared_list, id):
    # Simular trabajo de duración variable
    duracion = random.uniform(0.2, 1.0)
    time.sleep(duracion)

    # Modificar diccionario compartido
    shared_dict[f"worker_{id}"] = {
        "status": "done",
        "result": id ** 2,
        "duracion": round(duracion, 2)
    }

    # Agregar a lista compartida
    shared_list.append(f"Worker {id} completó en {duracion:.2f}s")

if __name__ == "__main__":
    with Manager() as manager:
        d = manager.dict()
        l = manager.list()

        procs = [Process(target=worker, args=(d, l, i)) for i in range(5)]

        for p in procs:
            p.start()
        for p in procs:
            p.join()

        print("Diccionario compartido:")
        for k, v in d.items():
            print(f"  {k}: {v}")

        print("\nLista compartida (orden de finalización):")
        for item in l:
            print(f"  {item}")
```

**Preguntas:**
- ¿En qué orden aparecen los items en la lista? ¿Por qué?
- ¿`Manager` es más rápido o más lento que `Value`/`Array`? ¿Por qué?

---

## Ejercicio 5: Procesador de imágenes paralelo (Obligatorio)

**Objetivo:** Aplicar `Pool.map` a un caso realista de procesamiento de datos en paralelo.

**Consigna:** crear un procesador que aplique un filtro (simulado con un blur 3x3) a múltiples "imágenes" (matrices de enteros). Comparar tiempo secuencial vs paralelo y calcular speedup.

```python
#!/usr/bin/env python3
"""
Procesador de imágenes paralelo.
Simula procesamiento de imágenes usando matrices.
"""
from multiprocessing import Pool
import time
import random

def crear_imagen(size):
    """Crea una 'imagen' como lista de listas."""
    return [[random.randint(0, 255) for _ in range(size)]
            for _ in range(size)]

def aplicar_filtro(imagen):
    """Aplica un filtro blur 3x3 (CPU-intensive)."""
    size = len(imagen)
    resultado = [[0] * size for _ in range(size)]

    for i in range(1, size - 1):
        for j in range(1, size - 1):
            suma = 0
            for di in [-1, 0, 1]:
                for dj in [-1, 0, 1]:
                    suma += imagen[i + di][j + dj]
            resultado[i][j] = suma // 9

    return resultado

def procesar_imagen(args):
    """Procesa una imagen y devuelve métricas."""
    idx, imagen = args
    inicio = time.time()
    resultado = aplicar_filtro(imagen)
    duracion = time.time() - inicio
    return idx, duracion, sum(sum(row) for row in resultado)

if __name__ == "__main__":
    NUM_IMAGENES = 8
    SIZE = 100

    print(f"Creando {NUM_IMAGENES} imágenes de {SIZE}x{SIZE}...")
    imagenes = [(i, crear_imagen(SIZE)) for i in range(NUM_IMAGENES)]

    # Procesar secuencialmente
    print("\nProcesamiento secuencial:")
    inicio = time.time()
    for img in imagenes:
        procesar_imagen(img)
    tiempo_secuencial = time.time() - inicio
    print(f"Tiempo: {tiempo_secuencial:.2f}s")

    # Procesar en paralelo
    print("\nProcesamiento paralelo (4 workers):")
    inicio = time.time()
    with Pool(4) as pool:
        resultados = pool.map(procesar_imagen, imagenes)
    tiempo_paralelo = time.time() - inicio

    for idx, duracion, checksum in resultados:
        print(f"  Imagen {idx}: {duracion:.3f}s")

    print(f"Tiempo total: {tiempo_paralelo:.2f}s")
    print(f"Speedup: {tiempo_secuencial / tiempo_paralelo:.2f}x")
```

**Verificación:** tu implementación debe:
- Crear múltiples imágenes (matrices) aleatorias
- Aplicar el filtro a cada imagen
- Usar `Pool.map` para procesamiento paralelo
- Mostrar tiempo secuencial vs paralelo
- Calcular speedup
- Funcionar correctamente con `if __name__ == "__main__":`

---

## Ejercicio 6: Map-Reduce para conteo de palabras

**Objetivo:** Implementar el patrón Map-Reduce clásico para contar palabras en varios textos.

**Consigna:** dado un conjunto de textos, contar la frecuencia de cada palabra usando Map-Reduce: cada worker cuenta las palabras de un texto, y luego se combinan todos los conteos.

```python
#!/usr/bin/env python3
"""Map-Reduce para conteo de palabras."""
from multiprocessing import Pool
from functools import reduce

TEXTOS = [
    "el rapido zorro marron salta sobre el perro perezoso",
    "el perro duerme bajo el arbol mientras el zorro corre",
    "rapido como el viento el zorro vuelve a saltar sobre el perro",
    "el arbol es viejo y el perro lo mira con curiosidad",
    "saltar correr el zorro y el perro juegan bajo el arbol",
]

def mapper(texto):
    """Cuenta palabras en un texto (etapa map)."""
    conteo = {}
    for palabra in texto.lower().split():
        conteo[palabra] = conteo.get(palabra, 0) + 1
    return conteo

def reducer(dict1, dict2):
    """Combina dos diccionarios de conteo (etapa reduce)."""
    resultado = dict1.copy()
    for palabra, count in dict2.items():
        resultado[palabra] = resultado.get(palabra, 0) + count
    return resultado

if __name__ == "__main__":
    with Pool(4) as pool:
        # Map: contar en paralelo
        conteos_parciales = pool.map(mapper, TEXTOS)

    # Reduce: combinar resultados (secuencial)
    conteo_total = reduce(reducer, conteos_parciales)

    # Ordenar por frecuencia descendente
    palabras_ordenadas = sorted(conteo_total.items(),
                                 key=lambda x: -x[1])

    print("Top palabras más frecuentes:")
    for palabra, count in palabras_ordenadas[:10]:
        print(f"  {palabra:15s} {count}")
```

**Extensión:** modificá el programa para que procese un archivo grande dividiéndolo en chunks y aplicando Map-Reduce.

---

## Ejercicio 7: Pipeline de procesos

**Objetivo:** Implementar un pipeline de varias etapas conectadas por colas.

**Consigna:** construí un pipeline de 3 etapas para procesar números:
1. **Etapa 1**: multiplicar por 2
2. **Etapa 2**: sumar 10
3. **Etapa 3**: convertir a string formateado

Cada etapa corre en su propio proceso y se conecta con la siguiente vía `Queue`.

```python
#!/usr/bin/env python3
"""Pipeline de 3 etapas con multiprocessing."""
from multiprocessing import Process, Queue
import time

def etapa_multiplicar(input_q, output_q):
    while True:
        item = input_q.get()
        if item is None:
            output_q.put(None)
            break
        time.sleep(0.05)
        output_q.put(item * 2)

def etapa_sumar(input_q, output_q):
    while True:
        item = input_q.get()
        if item is None:
            output_q.put(None)
            break
        time.sleep(0.05)
        output_q.put(item + 10)

def etapa_formatear(input_q, output_q):
    while True:
        item = input_q.get()
        if item is None:
            output_q.put(None)
            break
        time.sleep(0.05)
        output_q.put(f"resultado_{item:03d}")

if __name__ == "__main__":
    q1, q2, q3, q4 = Queue(), Queue(), Queue(), Queue()

    p1 = Process(target=etapa_multiplicar, args=(q1, q2))
    p2 = Process(target=etapa_sumar, args=(q2, q3))
    p3 = Process(target=etapa_formatear, args=(q3, q4))

    p1.start(); p2.start(); p3.start()

    # Alimentar el pipeline
    for i in range(10):
        q1.put(i)
    q1.put(None)

    # Recoger resultados
    while True:
        result = q4.get()
        if result is None:
            break
        print(f"Final: {result}")

    p1.join(); p2.join(); p3.join()
```

**Preguntas:**
- ¿Qué pasa si una etapa es mucho más lenta que las otras?
- ¿Cómo escalarías la etapa lenta?

---

## Ejercicios adicionales

### Cálculo de pi con Monte Carlo

Estimá π usando el método de Monte Carlo: generar puntos aleatorios en un cuadrado [0,1]×[0,1] y contar cuántos caen dentro del círculo unitario. Paralelizá con `Pool`.

### Merge sort paralelo

Implementá merge sort donde la división se paraleliza con procesos. ¿A partir de qué tamaño de lista conviene paralelizar?

### Procesador de archivos en paralelo

Dada una carpeta con muchos archivos, procesarlos en paralelo: contar líneas, buscar un patrón, calcular hash, etc.

---

*Computación II - 2026 - Clase 8*
