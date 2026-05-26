# Clase 8: Multiprocessing - Ejercicios Prácticos

## Ejercicio 1: Comparación threads vs procesos

```python
#!/usr/bin/env python3
"""Comparar rendimiento threads vs procesos para CPU-bound."""
from multiprocessing import Pool
from concurrent.futures import ThreadPoolExecutor
import time
import math

def cpu_task(n):
    """Tarea CPU-intensive."""
    return sum(math.sqrt(i) for i in range(n))

N = 500000
TASKS = 8

if __name__ == "__main__":
    # Secuencial
    start = time.time()
    results = [cpu_task(N) for _ in range(TASKS)]
    print(f"Secuencial: {time.time() - start:.2f}s")

    # Threads
    start = time.time()
    with ThreadPoolExecutor(4) as executor:
        results = list(executor.map(cpu_task, [N] * TASKS))
    print(f"Threads(4): {time.time() - start:.2f}s")

    # Procesos
    start = time.time()
    with Pool(4) as pool:
        results = pool.map(cpu_task, [N] * TASKS)
    print(f"Procesos(4): {time.time() - start:.2f}s")
```

---

## Ejercicio 2: Productor-Consumidor con Queue

```python
#!/usr/bin/env python3
"""Productor-consumidor multiprocess."""
from multiprocessing import Process, Queue
import time
import random
import os

def productor(queue, num_items, id):
    for i in range(num_items):
        item = f"P{id}-{i}"
        queue.put(item)
        print(f"[Prod-{id} PID={os.getpid()}] Produjo: {item}")
        time.sleep(random.uniform(0.1, 0.3))
    print(f"[Prod-{id}] Terminó")

def consumidor(queue, id, total_productores):
    fins = 0
    while fins < total_productores:
        item = queue.get()
        if item is None:
            fins += 1
        else:
            print(f"[Cons-{id} PID={os.getpid()}] Consumió: {item}")
            time.sleep(random.uniform(0.05, 0.15))
    print(f"[Cons-{id}] Terminó")

if __name__ == "__main__":
    NUM_PROD = 2
    NUM_CONS = 2
    ITEMS_PER_PROD = 5

    queue = Queue()

    # Crear productores
    productores = [Process(target=productor, args=(queue, ITEMS_PER_PROD, i))
                   for i in range(NUM_PROD)]

    # Crear consumidores
    consumidores = [Process(target=consumidor, args=(queue, i, NUM_PROD))
                    for i in range(NUM_CONS)]

    for p in productores + consumidores:
        p.start()

    for p in productores:
        p.join()

    # Enviar señales de fin
    for _ in range(NUM_CONS):
        queue.put(None)

    for c in consumidores:
        c.join()

    print("Fin del programa")
```

---

## Ejercicio 3: Pool con diferentes métodos

```python
#!/usr/bin/env python3
"""Explorar diferentes métodos de Pool."""
from multiprocessing import Pool
import time

def cuadrado(x):
    time.sleep(0.2)
    return x ** 2

def suma(a, b):
    return a + b

if __name__ == "__main__":
    with Pool(4) as pool:
        # map: síncrono, ordenado
        print("map:", pool.map(cuadrado, range(8)))

        # map_async: asíncrono
        async_result = pool.map_async(cuadrado, range(8))
        print("map_async (trabajando):", async_result.ready())
        print("map_async:", async_result.get())

        # imap: iterador lazy
        print("imap:", list(pool.imap(cuadrado, range(4))))

        # imap_unordered: más rápido, sin orden
        print("imap_unordered:", list(pool.imap_unordered(cuadrado, range(4))))

        # starmap: múltiples argumentos
        print("starmap:", pool.starmap(suma, [(1,2), (3,4), (5,6)]))

        # apply_async: una tarea
        result = pool.apply_async(cuadrado, (10,))
        print("apply_async:", result.get())
```

---

## Ejercicio 4: Memoria compartida

```python
#!/usr/bin/env python3
"""Memoria compartida entre procesos."""
from multiprocessing import Process, Value, Array, Lock
import time

def incrementar(contador, lock, id):
    for _ in range(10000):
        with lock:
            contador.value += 1
    print(f"Worker {id} terminó")

def llenar_array(arr, start_val):
    for i in range(len(arr)):
        arr[i] = start_val + i

if __name__ == "__main__":
    # Value compartido con Lock
    contador = Value('i', 0)
    lock = Lock()

    procs = [Process(target=incrementar, args=(contador, lock, i))
             for i in range(4)]

    for p in procs:
        p.start()
    for p in procs:
        p.join()

    print(f"Contador final: {contador.value}")  # Debe ser 40000

    # Array compartido
    arr = Array('i', 10)
    p = Process(target=llenar_array, args=(arr, 100))
    p.start()
    p.join()

    print(f"Array: {list(arr)}")
```

---

## Ejercicio 5: Procesador de imágenes paralelo (Obligatorio)

### Objetivo

Crear un procesador que aplique transformaciones a múltiples "imágenes" (simuladas como matrices) en paralelo.

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
    """Aplica un filtro (simula procesamiento costoso)."""
    size = len(imagen)
    resultado = [[0] * size for _ in range(size)]

    for i in range(1, size - 1):
        for j in range(1, size - 1):
            # Filtro de blur simple
            suma = 0
            for di in [-1, 0, 1]:
                for dj in [-1, 0, 1]:
                    suma += imagen[i + di][j + dj]
            resultado[i][j] = suma // 9

    return resultado

def procesar_imagen(args):
    """Procesa una imagen (para usar con pool.map)."""
    idx, imagen = args
    inicio = time.time()
    resultado = aplicar_filtro(imagen)
    duracion = time.time() - inicio
    return idx, duracion, sum(sum(row) for row in resultado)

if __name__ == "__main__":
    # Crear imágenes de prueba
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

---

## Ejercicio 6: Manager para estructuras compartidas

```python
#!/usr/bin/env python3
"""Usar Manager para compartir estructuras complejas."""
from multiprocessing import Process, Manager
import time

def worker(shared_dict, shared_list, id):
    # Modificar diccionario compartido
    shared_dict[f"worker_{id}"] = {
        "status": "done",
        "result": id ** 2
    }

    # Agregar a lista compartida
    shared_list.append(f"Completado por worker {id}")

    time.sleep(0.5)

if __name__ == "__main__":
    with Manager() as manager:
        d = manager.dict()
        l = manager.list()

        procs = [Process(target=worker, args=(d, l, i))
                 for i in range(5)]

        for p in procs:
            p.start()
        for p in procs:
            p.join()

        print("Diccionario compartido:")
        for k, v in d.items():
            print(f"  {k}: {v}")

        print("\nLista compartida:")
        for item in l:
            print(f"  {item}")
```

---

## Verificación del ejercicio obligatorio

### Ejercicio 5: Procesador de imágenes

Tu implementación debe:

- [ ] Crear múltiples "imágenes" (matrices)
- [ ] Aplicar un filtro a cada imagen
- [ ] Usar Pool para procesamiento paralelo
- [ ] Mostrar tiempo secuencial vs paralelo
- [ ] Calcular speedup
- [ ] Funcionar correctamente con `if __name__ == "__main__":`

---

## Ejercicios adicionales

### Calculador de pi Monte Carlo

Usá multiprocessing para estimar pi con el método de Monte Carlo en paralelo.

### Web scraper paralelo

Creá un scraper que descargue múltiples páginas en paralelo usando ProcessPoolExecutor.

### Merge sort paralelo

Implementá merge sort usando multiprocessing para ordenar en paralelo.

---

*Computación II - 2026 - Clase 8*
