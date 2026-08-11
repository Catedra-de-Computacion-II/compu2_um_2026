# Clase 11: Sincronización - Extra Manijas

Material opcional para profundizar.

---

## Modelos de memoria y ordenamiento

### El problema de la visibilidad

En sistemas multiprocesador, cada CPU tiene su cache. Cambios hechos por un thread pueden no ser inmediatamente visibles para otros:

```
CPU 1                     CPU 2
┌─────┐                  ┌─────┐
│Cache│ x=0              │Cache│ x=0
└──┬──┘                  └──┬──┘
   │                        │
   └────────┬───────────────┘
            │
      ┌─────┴─────┐
      │  Memoria  │ x=0
      │  Principal│
      └───────────┘

Thread 1 escribe x=1 en su cache.
Thread 2 aún ve x=0 en su cache.
```

### Memory barriers

Las primitivas de sincronización incluyen barreras de memoria que fuerzan la sincronización de caches:

```python
import threading

# El Lock incluye barreras de memoria implícitas
lock = threading.Lock()
x = 0

def writer():
    global x
    x = 1  # Puede estar solo en cache
    with lock:  # Barrera: flush a memoria
        pass

def reader():
    with lock:  # Barrera: invalidar cache
        print(x)  # Garantizado ver el valor actualizado
```

### Operaciones atómicas en Python

Python garantiza atomicidad para ciertas operaciones:

```python
# Atómico en CPython (por el GIL)
x = y  # Asignación simple
x = []  # Asignación de referencia
L.append(x)  # append es atómico
L.pop()  # pop es atómico
D[x] = y  # Asignación a dict
D.get(x)  # get de dict

# NO atómico (incluso con GIL)
x += 1  # Es: temp = x; temp = temp + 1; x = temp
L[0] += 1  # Similar
D[x] += 1  # Similar
```

---

## Patrones avanzados de sincronización

### Monitor pattern

Un monitor encapsula datos + sincronización:

```python
import threading

class Monitor:
    """Patrón monitor: datos protegidos con métodos sincronizados."""

    def __init__(self):
        self._lock = threading.RLock()
        self._condition = threading.Condition(self._lock)
        self._data = []

    def synchronized(method):
        """Decorador para métodos sincronizados."""
        def wrapper(self, *args, **kwargs):
            with self._lock:
                return method(self, *args, **kwargs)
        return wrapper

    @synchronized
    def add(self, item):
        self._data.append(item)
        self._condition.notify_all()

    @synchronized
    def wait_for_data(self):
        while not self._data:
            self._condition.wait()
        return self._data.pop(0)

    @synchronized
    def size(self):
        return len(self._data)
```

### Active Object pattern

Encola operaciones para ejecución en un thread dedicado:

```python
import threading
import queue

class ActiveObject:
    def __init__(self):
        self._queue = queue.Queue()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self):
        while True:
            func, args, kwargs, result = self._queue.get()
            try:
                ret = func(*args, **kwargs)
                result.put(('ok', ret))
            except Exception as e:
                result.put(('error', e))

    def invoke(self, func, *args, **kwargs):
        result = queue.Queue()
        self._queue.put((func, args, kwargs, result))
        status, value = result.get()
        if status == 'error':
            raise value
        return value

# Uso
class Calculator(ActiveObject):
    def __init__(self):
        super().__init__()
        self.value = 0

    def add(self, x):
        return self.invoke(self._add, x)

    def _add(self, x):
        import time
        time.sleep(0.1)  # Simular trabajo
        self.value += x
        return self.value

calc = Calculator()
print(calc.add(5))   # Thread-safe automáticamente
print(calc.add(10))
```

### Future pattern

Representa un resultado que estará disponible en el futuro:

```python
import threading
import time

class Future:
    def __init__(self):
        self._result = None
        self._exception = None
        self._done = threading.Event()

    def set_result(self, result):
        self._result = result
        self._done.set()

    def set_exception(self, exception):
        self._exception = exception
        self._done.set()

    def result(self, timeout=None):
        if not self._done.wait(timeout):
            raise TimeoutError()
        if self._exception:
            raise self._exception
        return self._result

    def done(self):
        return self._done.is_set()

def async_operation(future, value):
    time.sleep(1)
    future.set_result(value * 2)

# Uso
future = Future()
threading.Thread(target=async_operation, args=(future, 21)).start()

print("Esperando resultado...")
print(f"Resultado: {future.result()}")  # 42
```

---

## Lock-free programming

### Compare-and-swap conceptual

```python
import threading

class AtomicCounter:
    """Contador usando lock (no hay CAS nativo en Python)."""

    def __init__(self, initial=0):
        self._value = initial
        self._lock = threading.Lock()

    def increment(self):
        with self._lock:
            self._value += 1
            return self._value

    def get(self):
        return self._value

# En lenguajes con CAS nativo sería:
# def increment(self):
#     while True:
#         old = self._value
#         new = old + 1
#         if compare_and_swap(self._value, old, new):
#             return new
```

### Estructuras lock-free

Python no tiene primitivas lock-free nativas, pero podés usar:

```python
import queue

# queue.Queue es thread-safe sin locks explícitos para el usuario
q = queue.Queue()
q.put(item)
item = q.get()

# collections.deque tiene operaciones atómicas específicas
from collections import deque
d = deque()
d.append(x)  # Atómico
d.appendleft(x)  # Atómico
x = d.pop()  # Atómico
x = d.popleft()  # Atómico
```

---

## Problemas clásicos de concurrencia

### Filósofos comensales: la solución del camarero

Las dos soluciones vistas en clase —jerarquía de recursos y `Semaphore(N-1)`— evitan el deadlock pero no dicen nada sobre equidad: un filósofo con vecinos lentos puede comer mucho más que el resto.

Una tercera vía es introducir un árbitro que otorgue permiso explícito, con estados por filósofo. Es más código, pero permite razonar sobre inanición:

```python
import threading
import time
import random

NUM = 5
PENSANDO, HAMBRIENTO, COMIENDO = 0, 1, 2

class Mesa:
    def __init__(self):
        self.estado = [PENSANDO] * NUM
        self.cond = threading.Condition()
        self.comidas = [0] * NUM

    def _puede_comer(self, i):
        izq, der = (i - 1) % NUM, (i + 1) % NUM
        return (self.estado[i] == HAMBRIENTO
                and self.estado[izq] != COMIENDO
                and self.estado[der] != COMIENDO)

    def _intentar(self, i):
        if self._puede_comer(i):
            self.estado[i] = COMIENDO
            self.cond.notify_all()

    def tomar_tenedores(self, i):
        with self.cond:
            self.estado[i] = HAMBRIENTO
            self._intentar(i)
            while self.estado[i] != COMIENDO:
                self.cond.wait()
            self.comidas[i] += 1

    def dejar_tenedores(self, i):
        with self.cond:
            self.estado[i] = PENSANDO
            # Darle una oportunidad a los vecinos que esperaban
            self._intentar((i - 1) % NUM)
            self._intentar((i + 1) % NUM)


def filosofo(i, mesa, rondas=5):
    for _ in range(rondas):
        time.sleep(random.uniform(0.01, 0.05))
        mesa.tomar_tenedores(i)
        time.sleep(random.uniform(0.02, 0.06))
        mesa.dejar_tenedores(i)


mesa = Mesa()
hilos = [threading.Thread(target=filosofo, args=(i, mesa)) for i in range(NUM)]
for t in hilos: t.start()
for t in hilos: t.join()
print(f"Comidas por filósofo: {mesa.comidas}")
```

Acá no hay un lock por tenedor: el estado de la mesa entero se protege con una sola `Condition`, y un filósofo pasa a `COMIENDO` solo si ninguno de sus vecinos lo está. Es el patrón *monitor* aplicado al problema.

> **El error clásico**: intentar el orden consistente ordenando los objetos `Lock` en vez de sus índices. `min(lock_a, lock_b)` compara direcciones de memoria —un orden real, pero arbitrario y sin relación con la topología de la mesa—, así que dos filósofos pueden terminar tomando sus tenedores en órdenes opuestos y el ciclo de espera reaparece. El orden total tiene que definirse sobre un identificador estable del recurso.

Ni siquiera esta versión garantiza ausencia de inanición: `notify_all` despierta a todos y el que gana depende del scheduler. Para eso haría falta encolar a los hambrientos y atenderlos en orden de llegada.

### Sleeping Barber

```python
import threading
import time
import random

class BarberShop:
    def __init__(self, num_chairs):
        self.num_chairs = num_chairs
        self.waiting_customers = 0
        self.lock = threading.Lock()
        self.customer_ready = threading.Semaphore(0)
        self.barber_ready = threading.Semaphore(0)
        self.customer_done = threading.Semaphore(0)
        self.barber_done = threading.Semaphore(0)

    def customer(self, id):
        with self.lock:
            if self.waiting_customers >= self.num_chairs:
                print(f"Customer {id}: No chairs, leaving")
                return
            self.waiting_customers += 1
            print(f"Customer {id}: Waiting ({self.waiting_customers} in queue)")

        self.customer_ready.release()  # Wake barber
        self.barber_ready.acquire()    # Wait for barber

        # Getting haircut
        print(f"Customer {id}: Getting haircut")

        self.customer_done.release()
        self.barber_done.acquire()

        with self.lock:
            self.waiting_customers -= 1
        print(f"Customer {id}: Done!")

    def barber(self):
        while True:
            print("Barber: Sleeping...")
            self.customer_ready.acquire()  # Wait for customer

            self.barber_ready.release()    # Ready to cut

            # Cutting hair
            print("Barber: Cutting hair")
            time.sleep(random.uniform(0.3, 0.7))

            self.barber_done.release()
            self.customer_done.acquire()

shop = BarberShop(3)

# Start barber
barber = threading.Thread(target=shop.barber, daemon=True)
barber.start()

# Customers arrive
for i in range(10):
    threading.Thread(target=shop.customer, args=(i,)).start()
    time.sleep(random.uniform(0.1, 0.4))

time.sleep(5)  # Let things finish
```

---

## Herramientas de debugging

### ThreadSanitizer (TSan)

Para código C/C++ que interactúa con Python:

```bash
# Compilar extensión con TSan
gcc -fsanitize=thread -g extension.c

# Ejecutar
TSAN_OPTIONS="history_size=7" python3 programa.py
```

### tracemalloc para detectar leaks

```python
import tracemalloc
import threading

tracemalloc.start()

def worker():
    data = [0] * 1000000  # Leak potencial

threads = [threading.Thread(target=worker) for _ in range(10)]
for t in threads:
    t.start()
for t in threads:
    t.join()

snapshot = tracemalloc.take_snapshot()
top_stats = snapshot.statistics('lineno')

print("Top 10 memory allocations:")
for stat in top_stats[:10]:
    print(stat)
```

### faulthandler para deadlocks

```python
import faulthandler
import threading
import time

# Habilitar dump en SIGQUIT (Ctrl+\)
faulthandler.enable()

# O dump automático después de timeout
faulthandler.dump_traceback_later(10, repeat=True)

lock = threading.Lock()

def deadlock():
    with lock:
        with lock:  # Deadlock con Lock normal
            pass

# Si hay deadlock, Ctrl+\ muestra traceback de todos los threads
```

---

## Recursos adicionales

- [Python threading primitives](https://docs.python.org/3/library/threading.html#lock-objects)
- [The Little Book of Semaphores](https://greenteapress.com/semaphores/)
- [Java Concurrency in Practice](https://jcip.net/) - Conceptos aplicables a Python
- [Mutex vs Semaphore](https://barrgroup.com/Embedded-Systems/How-To/RTOS-Mutex-Semaphore)

---

*Computación II - 2026 - Clase 11 - Material opcional*
