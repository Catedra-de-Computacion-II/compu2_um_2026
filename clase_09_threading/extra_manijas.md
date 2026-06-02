# Clase 9: Threads - Extra Manijas

> Material de profundización **opcional**.
> Para quienes quieran ir más allá del contenido estándar de la clase.

---

## 1. Internals del GIL

### ¿Por qué existe el GIL?

CPython usa **reference counting** para garbage collection. Cada objeto tiene un contador de referencias, y cuando llega a 0, se libera la memoria.

Sin el GIL, múltiples threads podrían modificar ese contador simultáneamente, corrompiendo el estado del intérprete:

```
// Pseudocódigo de la race condition que el GIL evita

// Thread 1                    // Thread 2
ref_count = obj.ref_count     ref_count = obj.ref_count
ref_count = ref_count + 1     ref_count = ref_count + 1
obj.ref_count = ref_count     obj.ref_count = ref_count

// Resultado: ref_count = 2 en lugar de 3 → memory corruption
```

### El switch interval

El GIL no es un simple mutex global: usa un mecanismo de "check interval" para cambiar entre hilos.

```python
import sys

# Por defecto: 5ms (0.005 segundos)
print(f"Switch interval: {sys.getswitchinterval()}")

# Podés modificarlo (no recomendado en producción)
sys.setswitchinterval(0.001)  # Cambiar cada 1ms
```

### Demostrar el GIL empíricamente

```python
import threading
import time

N = 10_000_000

def cpu_bound(n):
    total = 0
    for i in range(n):
        total += i
    return total

# Un solo hilo
inicio = time.perf_counter()
cpu_bound(N)
tiempo_single = time.perf_counter() - inicio

# Dos hilos (debería ser más rápido en teoría, pero no por el GIL)
inicio = time.perf_counter()
h1 = threading.Thread(target=cpu_bound, args=(N // 2,))
h2 = threading.Thread(target=cpu_bound, args=(N // 2,))
h1.start(); h2.start()
h1.join(); h2.join()
tiempo_multi = time.perf_counter() - inicio

print(f"Single thread: {tiempo_single:.3f}s")
print(f"Multi thread:  {tiempo_multi:.3f}s")
print(f"Ratio: {tiempo_multi/tiempo_single:.2f}x")
# El ratio será ~1 o incluso >1, demostrando que el GIL elimina el beneficio
```

### Cuándo se libera el GIL

1. **Durante I/O**: operaciones de red, disco, etc.
2. **Extensiones C**: código C que declara `Py_BEGIN_ALLOW_THREADS` (numpy, lxml, etc.)
3. **Cada N instrucciones**: Python libera el GIL periódicamente (`sys.getswitchinterval()`)

---

## 2. Free-threaded Python (sin GIL)

Como vimos en el contenido principal, **PEP 703** introduce un build de Python sin GIL. Acá profundizamos.

### Verificar si tu Python tiene GIL

```python
import sys

# Disponible desde Python 3.13
if hasattr(sys, '_is_gil_enabled'):
    if sys._is_gil_enabled():
        print("GIL activo")
    else:
        print("Free-threaded build (sin GIL)")
else:
    print("Python anterior a 3.13: GIL activo (siempre)")
```

### Instalar el free-threaded build

En **Linux/macOS** (instaladores oficiales desde python.org):
- Bajar el instalador "freethreaded" desde python.org/downloads
- Tener cuidado: queda como un python aparte (`python3.14t` o `python3.13t`, donde `t` viene de "threaded")

En **Linux compilando desde fuente**:
```bash
./configure --disable-gil
make
```

En **Conda**:
```bash
conda install python-freethreading
```

### Cómo cambia el código

**Threads y CPU-bound**: en free-threaded, esto SÍ escala:

```python
# Idéntico al ejemplo anterior, pero en free-threaded
# verás algo como:
# Single thread: 1.20s
# Multi thread:  0.65s   ← casi 2x más rápido!
# Ratio: 0.54
```

### Los costos

**Penalización single-threaded (5-10%)**:
Los objetos ya no se protegen con el GIL global; ahora cada objeto tiene un lock interno más fino, y el reference counting es atómico. Eso cuesta CPU incluso si solo hay un thread.

**Compatibilidad con librerías C**:
Muchas extensiones C no son thread-safe por sí mismas (dependían del GIL para serializarse). Necesitan ser actualizadas. Ejemplo: numpy tuvo que hacer trabajo para soportar free-threading.

Para verificar si un paquete soporta free-threading:
```bash
pip install <paquete>
# si no soporta, vas a ver warnings o el build va a fallar
```

### Cuándo (no) adoptar free-threaded

**Sí adoptar:**
- Programas CPU-bound que multiprocessing era la única opción
- Workloads con mucho cómputo paralelo
- Cuando el overhead de IPC de multiprocessing es problemático

**No adoptar todavía:**
- En producción si dependés de librerías C que no lo soportan
- Si el costo del 5-10% en single-threaded importa
- Si tu código no es CPU-bound (no vas a ver mejoras)

### Roadmap

- **3.13** (2024): experimental
- **3.14** (2025): supported, no default
- **3.15+**: posible default
- **Futuro**: el GIL desaparece como opción

Para esta materia (y el 99% del código Python en uso hoy) asumimos GIL. Pero es muy probable que para cuando se gradúen, free-threaded sea el default.

---

## 3. Implementar tus propias primitivas

Si querés entender cómo funcionan los locks por dentro, intentá implementar tu propio semáforo usando solo `Lock` y `Condition`. Vas a ver que la lógica no es trivial.

```python
import threading
import time

class MiSemaforo:
    """Implementación de Semáforo usando Condition."""

    def __init__(self, valor_inicial=1):
        self._valor = valor_inicial
        self._condition = threading.Condition(threading.Lock())

    def acquire(self, blocking=True, timeout=None):
        with self._condition:
            if not blocking:
                if self._valor <= 0:
                    return False
                self._valor -= 1
                return True

            if timeout is not None:
                deadline = time.monotonic() + timeout

            while self._valor <= 0:
                if timeout is not None:
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        return False
                    self._condition.wait(timeout=remaining)
                else:
                    self._condition.wait()

            self._valor -= 1
            return True

    def release(self, n=1):
        with self._condition:
            self._valor += n
            self._condition.notify_all()

    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self, *args):
        self.release()
```

Las primitivas estándar (`Lock`, `Condition`, `Event`, `Semaphore`, `Barrier`) las vemos en detalle en las **clases 10 y 11**.

---

## 4. Patrones avanzados

### Thread-safe Singleton (con double-checked locking)

```python
import threading

class Singleton:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        # Primera verificación sin lock (rápido)
        if cls._instance is None:
            with cls._lock:
                # Segunda verificación con lock (correcto)
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

s1 = Singleton()
s2 = Singleton()
print(s1 is s2)  # True
```

### Object pool thread-safe

```python
import threading
import queue
import time

class ObjectPool:
    def __init__(self, factory, max_size=5):
        self.factory = factory
        self.pool = queue.Queue(max_size)

        for _ in range(max_size):
            self.pool.put(factory())

    def acquire(self, timeout=None):
        try:
            return self.pool.get(timeout=timeout)
        except queue.Empty:
            return None

    def release(self, obj):
        self.pool.put(obj)
```

---

## 5. Debugging avanzado

### Detector de deadlocks simple

Monitorea threads y alerta si no hay progreso:

```python
import threading
import time
import sys
import traceback

class DeadlockDetector:
    def __init__(self, timeout=5):
        self._timeout = timeout
        self._running = True
        self._monitor = threading.Thread(
            target=self._detectar,
            name="DeadlockDetector",
            daemon=True
        )

    def start(self):
        self._monitor.start()

    def stop(self):
        self._running = False

    def _detectar(self):
        prev_frames = {}
        while self._running:
            time.sleep(self._timeout)
            curr_frames = sys._current_frames()

            frozen_threads = []
            for tid, frame in curr_frames.items():
                if tid in prev_frames and prev_frames[tid] == frame.f_lineno:
                    hilo = next((h for h in threading.enumerate() if h.ident == tid), None)
                    if hilo and hilo.name not in ("MainThread", "DeadlockDetector"):
                        frozen_threads.append((hilo.name, frame))

            if len(frozen_threads) > 1:
                print("\nPOSIBLE DEADLOCK DETECTADO")
                for nombre, frame in frozen_threads:
                    print(f"\nHilo congelado: {nombre}")
                    traceback.print_stack(frame)

            prev_frames = {tid: frame.f_lineno for tid, frame in curr_frames.items()}
```

### Stack trace de todos los threads bajo demanda

Si el programa se cuelga, podés inspeccionarlo desde otra terminal sin matarlo. Registrá un handler para SIGUSR1:

```python
import signal
import sys
import traceback

def dump_threads(sig, frame):
    print("\n=== Thread Dump ===")
    for thread_id, frame in sys._current_frames().items():
        print(f"\nThread {thread_id}:")
        traceback.print_stack(frame)

signal.signal(signal.SIGUSR1, dump_threads)
# Ahora desde otra terminal: kill -USR1 <pid>
```

### `faulthandler` para crashes

```python
import faulthandler
faulthandler.enable()

# Si el programa crashea (o le mandás SIGABRT desde afuera),
# faulthandler dumpea el stack de TODOS los threads.
```

---

## 6. Lecturas y recursos

### Para entender el GIL en profundidad

- **["Understanding the Python GIL"](https://www.youtube.com/watch?v=Obt-vMVdM8s)** - David Beazley (PyCon 2010)
  Video clásico que explica el GIL con benchmarks reales.
- **[PEP 703](https://peps.python.org/pep-0703/)** - Making the GIL Optional in CPython
- **[PEP 779](https://peps.python.org/pep-0779/)** - Criteria for supported status for free-threaded Python
- **[py-free-threading.github.io](https://py-free-threading.github.io/)** - Guía oficial de free-threading

### Libros

- **"Python Concurrency with asyncio"** - Matthew Fowler
- **"High Performance Python"** - Micha Gorelick & Ian Ozsvald

### Documentación oficial

- [Python threading](https://docs.python.org/3/library/threading.html)
- [Python queue](https://docs.python.org/3/library/queue.html)
- [Python 3.14 What's New - free-threading](https://docs.python.org/3/whatsnew/3.14.html)

### Bibliotecas para explorar (alternativas a threading)

- **`gevent`** - greenlets y coroutines para I/O concurrente
- **`trio`** - librería de concurrencia moderna
- **`uvloop`** - reemplazo de alta performance para el event loop de asyncio

---

*Computación II - 2026 - Clase 9 - Material opcional*
