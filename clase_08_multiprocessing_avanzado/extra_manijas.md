# Clase 8: Multiprocessing - Extra Manijas

Material opcional para profundizar.

---

## Métodos de inicio de procesos

Linux y Windows usan métodos diferentes por defecto:

```python
import multiprocessing as mp

# Ver método actual
print(mp.get_start_method())

# Cambiar método (debe ser al inicio del programa)
# mp.set_start_method('fork')    # Linux default - más rápido
# mp.set_start_method('spawn')   # Windows default - más seguro
# mp.set_start_method('forkserver')  # Híbrido
```

**fork:** Copia el proceso padre. Rápido pero puede causar problemas con recursos compartidos.

**spawn:** Inicia un intérprete nuevo. Más lento pero más seguro.

**forkserver:** Un servidor hace forks. Balance entre velocidad y seguridad.

---

## shared_memory (Python 3.8+)

Memoria compartida de bajo nivel, más eficiente que Manager:

```python
from multiprocessing import shared_memory, Process
import numpy as np

def worker(shm_name, shape, dtype):
    existing_shm = shared_memory.SharedMemory(name=shm_name)
    arr = np.ndarray(shape, dtype=dtype, buffer=existing_shm.buf)
    arr[:] = arr * 2  # Modificar en su lugar
    existing_shm.close()

if __name__ == "__main__":
    # Crear array numpy
    original = np.array([1, 2, 3, 4, 5])

    # Crear memoria compartida
    shm = shared_memory.SharedMemory(create=True, size=original.nbytes)
    shared_array = np.ndarray(original.shape, dtype=original.dtype, buffer=shm.buf)
    shared_array[:] = original

    # Proceso modifica la memoria compartida
    p = Process(target=worker, args=(shm.name, original.shape, original.dtype))
    p.start()
    p.join()

    print(f"Resultado: {shared_array}")  # [2, 4, 6, 8, 10]

    shm.close()
    shm.unlink()
```

---

## Profiling de código paralelo

```python
import cProfile
import pstats
from multiprocessing import Pool
import io

def task(n):
    return sum(i*i for i in range(n))

if __name__ == "__main__":
    profiler = cProfile.Profile()
    profiler.enable()

    with Pool(4) as pool:
        results = pool.map(task, [100000] * 8)

    profiler.disable()
    stream = io.StringIO()
    stats = pstats.Stats(profiler, stream=stream).sort_stats('cumulative')
    stats.print_stats(20)
    print(stream.getvalue())
```

---

## Recursos adicionales

- [multiprocessing docs](https://docs.python.org/3/library/multiprocessing.html)
- [shared_memory docs](https://docs.python.org/3/library/multiprocessing.shared_memory.html)
- [Real Python - multiprocessing](https://realpython.com/python-multiprocessing/)

---

*Computación II - 2026 - Clase 8 - Material opcional*
