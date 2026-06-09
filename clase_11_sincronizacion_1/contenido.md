# Clase 11: Sincronización Avanzada - Coordinando la Concurrencia

## Introducción: el desafío de la coordinación

En la clase anterior vimos los conceptos básicos de threading y algunos primitivos de sincronización. Ahora profundizaremos en técnicas avanzadas para coordinar threads de forma correcta y eficiente.

La sincronización es quizás el aspecto más difícil de la programación concurrente. Los bugs son sutiles, difíciles de reproducir, y pueden manifestarse solo bajo ciertas condiciones de timing. Entender profundamente los primitivos de sincronización y cuándo usar cada uno es esencial para escribir código concurrente robusto.

---

## Repaso: por qué necesitamos sincronización

Cuando múltiples threads acceden a recursos compartidos, pueden ocurrir problemas:

### Race condition

```python
import threading

# Variable compartida
saldo = 1000

def retirar(cantidad):
    global saldo
    if saldo >= cantidad:
        # Ventana de vulnerabilidad: otro thread puede modificar saldo aquí
        saldo -= cantidad
        return True
    return False

# Sin sincronización, dos retiros simultáneos pueden causar saldo negativo
```

### Datos corruptos

```python
import threading

# Estructura compartida
datos = {"contador": 0, "suma": 0}

def actualizar(valor):
    # Las dos operaciones deberían ser atómicas
    datos["contador"] += 1
    datos["suma"] += valor
    # Si se interrumpe entre ambas, los datos quedan inconsistentes
```

---

## Lock: exclusión mutua básica

El Lock garantiza que solo un thread puede ejecutar una sección crítica a la vez.

### Lock con timeout

```python
import threading
import time

lock = threading.Lock()

def operacion_critica():
    # Intentar adquirir con timeout
    if lock.acquire(timeout=5.0):
        try:
            print("Lock adquirido, ejecutando operación...")
            time.sleep(1)
        finally:
            lock.release()
    else:
        print("No se pudo adquirir el lock en 5 segundos")

# Uso con blocking=False para no bloquear
def operacion_no_bloqueante():
    if lock.acquire(blocking=False):
        try:
            print("Lock disponible!")
        finally:
            lock.release()
    else:
        print("Lock ocupado, haciendo otra cosa...")
```

### RLock: lock reentrante

Permite que el mismo thread adquiera el lock múltiples veces:

```python
import threading

rlock = threading.RLock()

class CuentaBancaria:
    def __init__(self, saldo_inicial):
        self.saldo = saldo_inicial
        self.lock = threading.RLock()

    def depositar(self, cantidad):
        with self.lock:
            self.saldo += cantidad

    def retirar(self, cantidad):
        with self.lock:
            if self.saldo >= cantidad:
                self.saldo -= cantidad
                return True
            return False

    def transferir_a(self, otra_cuenta, cantidad):
        # Necesitamos el lock propio Y potencialmente llamar métodos
        # que también usan el lock
        with self.lock:
            if self.retirar(cantidad):  # Esto también usa self.lock
                otra_cuenta.depositar(cantidad)
                return True
            return False
```

### Problema del lock: deadlock

```python
import threading

lock_a = threading.Lock()
lock_b = threading.Lock()

def thread_1():
    with lock_a:
        print("Thread 1: tengo A")
        with lock_b:  # Espera B
            print("Thread 1: tengo A y B")

def thread_2():
    with lock_b:
        print("Thread 2: tengo B")
        with lock_a:  # Espera A - DEADLOCK!
            print("Thread 2: tengo B y A")
```

### Solución: orden consistente

```python
import threading

# Siempre adquirir locks en el mismo orden
def thread_1():
    with lock_a:
        with lock_b:
            print("Thread 1: tengo A y B")

def thread_2():
    with lock_a:  # Mismo orden que thread_1
        with lock_b:
            print("Thread 2: tengo A y B")

# O mejor: usar un solo lock cuando sea posible
lock_global = threading.Lock()
```

---

## Condition: esperar por condiciones

Condition permite que threads esperen hasta que cierta condición sea verdadera.

### El patrón básico

```python
import threading

condition = threading.Condition()
datos_disponibles = False
datos = None

def productor():
    global datos_disponibles, datos

    with condition:
        # Producir datos
        datos = "datos producidos"
        datos_disponibles = True

        # Notificar a los que esperan
        condition.notify()  # notify_all() para despertar a todos

def consumidor():
    global datos_disponibles

    with condition:
        # Esperar hasta que haya datos
        while not datos_disponibles:
            condition.wait()  # Libera el lock mientras espera

        # Procesar datos
        print(f"Recibido: {datos}")
        datos_disponibles = False
```

### Buffer acotado con Condition

```python
import threading
import time
import random

class BufferAcotado:
    def __init__(self, capacidad):
        self.capacidad = capacidad
        self.buffer = []
        self.condition = threading.Condition()

    def put(self, item):
        with self.condition:
            # Esperar si está lleno
            while len(self.buffer) >= self.capacidad:
                print(f"Buffer lleno ({len(self.buffer)}), esperando...")
                self.condition.wait()

            self.buffer.append(item)
            print(f"Agregado {item}, buffer: {len(self.buffer)}/{self.capacidad}")

            # Notificar que hay espacio/datos
            self.condition.notify_all()

    def get(self):
        with self.condition:
            # Esperar si está vacío
            while len(self.buffer) == 0:
                print("Buffer vacío, esperando...")
                self.condition.wait()

            item = self.buffer.pop(0)
            print(f"Sacado {item}, buffer: {len(self.buffer)}/{self.capacidad}")

            # Notificar que hay espacio
            self.condition.notify_all()
            return item

# Uso
buffer = BufferAcotado(3)

def productor(id):
    for i in range(5):
        time.sleep(random.uniform(0.1, 0.5))
        buffer.put(f"item-{id}-{i}")

def consumidor(id):
    for _ in range(5):
        time.sleep(random.uniform(0.2, 0.6))
        item = buffer.get()
```

### wait() con timeout

```python
import threading

condition = threading.Condition()

def esperador():
    with condition:
        resultado = condition.wait(timeout=5.0)
        if resultado:
            print("Condición notificada")
        else:
            print("Timeout - no hubo notificación")
```

---

## Semaphore: control de acceso concurrente

Un Semaphore mantiene un contador interno que controla cuántos threads pueden acceder a un recurso.

### Semáforo básico

```python
import threading
import time

# Máximo 3 conexiones simultáneas
pool_conexiones = threading.Semaphore(3)

def usar_conexion(id):
    print(f"[{id}] Esperando conexión...")

    pool_conexiones.acquire()
    try:
        print(f"[{id}] Conectado!")
        time.sleep(2)  # Usar la conexión
    finally:
        pool_conexiones.release()
        print(f"[{id}] Desconectado")

# 10 threads intentan conectar, máximo 3 simultáneos
threads = [threading.Thread(target=usar_conexion, args=(i,)) for i in range(10)]
for t in threads:
    t.start()
for t in threads:
    t.join()
```

### BoundedSemaphore: prevenir errores

```python
import threading

# BoundedSemaphore no permite más releases que acquires
sem = threading.BoundedSemaphore(2)

sem.acquire()
sem.release()
sem.release()  # ValueError! Excede el valor inicial
```

### Semáforo binario vs Lock

Un Semaphore(1) es similar a un Lock, pero con diferencias importantes:

```python
import threading

lock = threading.Lock()
sem = threading.Semaphore(1)

# Lock: solo el thread que lo adquirió puede liberarlo (conceptualmente)
# Semaphore: cualquier thread puede hacer release

# Esto es válido con Semaphore pero sería un error lógico con Lock:
def thread_a():
    sem.acquire()

def thread_b():
    sem.release()  # OK con Semaphore, problemático con Lock
```

---

## Event: señalización simple

Event es un flag thread-safe que threads pueden esperar.

### Patrón de inicio coordinado

```python
import threading
import time

inicio = threading.Event()

def worker(id):
    print(f"[Worker {id}] Listo, esperando inicio...")
    inicio.wait()  # Bloquea hasta que inicio.set()
    print(f"[Worker {id}] ¡Arrancando!")
    time.sleep(1)
    print(f"[Worker {id}] Terminado")

# Crear workers
threads = [threading.Thread(target=worker, args=(i,)) for i in range(5)]
for t in threads:
    t.start()

# Dar tiempo a que todos lleguen
time.sleep(1)

print("\n¡GO!\n")
inicio.set()  # Todos arrancan

for t in threads:
    t.join()
```

### Patrón de cancelación

```python
import threading
import time

detener = threading.Event()

def worker_cancelable():
    print("Worker iniciado")
    while not detener.is_set():
        print("Trabajando...")
        # wait() con timeout permite chequear periódicamente
        detener.wait(timeout=1.0)
    print("Worker detenido")

t = threading.Thread(target=worker_cancelable)
t.start()

time.sleep(3)
print("Solicitando detención...")
detener.set()

t.join()
```

### Event vs Condition

| Event | Condition |
|-------|-----------|
| Flag booleano simple | Permite condiciones complejas |
| set() despierta a todos | notify() puede despertar uno |
| El estado persiste | Se combina con predicados |
| Más simple | Más flexible |

---

## Barrier: punto de sincronización

Barrier hace que N threads esperen hasta que todos lleguen a un punto.

```python
import threading
import time
import random

# Barrera para 4 threads
barrera = threading.Barrier(4)

def fase(id):
    # Fase 1
    print(f"[{id}] Fase 1: trabajando...")
    time.sleep(random.uniform(0.5, 1.5))
    print(f"[{id}] Fase 1: completada, esperando en barrera...")

    barrera.wait()  # Esperar a que todos completen fase 1

    # Fase 2
    print(f"[{id}] Fase 2: trabajando...")
    time.sleep(random.uniform(0.5, 1.5))
    print(f"[{id}] Fase 2: completada, esperando en barrera...")

    barrera.wait()  # Esperar a que todos completen fase 2

    print(f"[{id}] ¡Todas las fases completadas!")

threads = [threading.Thread(target=fase, args=(i,)) for i in range(4)]
for t in threads:
    t.start()
for t in threads:
    t.join()
```

### Barrier con acción

```python
import threading

def cuando_todos_llegan():
    print("=== TODOS LLEGARON A LA BARRERA ===")

barrera = threading.Barrier(3, action=cuando_todos_llegan)
```

### Barrier con timeout

```python
import threading

barrera = threading.Barrier(3)

def worker(id, delay):
    import time
    time.sleep(delay)
    try:
        barrera.wait(timeout=5.0)
        print(f"[{id}] Pasó la barrera")
    except threading.BrokenBarrierError:
        print(f"[{id}] Barrera rota!")
```

---

## Patrones de sincronización

### Readers-Writers Lock

Permite múltiples lectores o un único escritor:

```python
import threading

class ReadWriteLock:
    def __init__(self):
        self.readers = 0
        self.resource_lock = threading.Lock()
        self.readers_lock = threading.Lock()

    def acquire_read(self):
        with self.readers_lock:
            self.readers += 1
            if self.readers == 1:
                self.resource_lock.acquire()

    def release_read(self):
        with self.readers_lock:
            self.readers -= 1
            if self.readers == 0:
                self.resource_lock.release()

    def acquire_write(self):
        self.resource_lock.acquire()

    def release_write(self):
        self.resource_lock.release()

# Context managers
class ReadContext:
    def __init__(self, rwlock):
        self.rwlock = rwlock

    def __enter__(self):
        self.rwlock.acquire_read()

    def __exit__(self, *args):
        self.rwlock.release_read()

class WriteContext:
    def __init__(self, rwlock):
        self.rwlock = rwlock

    def __enter__(self):
        self.rwlock.acquire_write()

    def __exit__(self, *args):
        self.rwlock.release_write()
```

### Double-checked locking

Para inicialización lazy thread-safe:

```python
import threading

class Singleton:
    _instance = None
    _lock = threading.Lock()

    @classmethod
    def get_instance(cls):
        if cls._instance is None:  # Primera comprobación sin lock
            with cls._lock:
                if cls._instance is None:  # Segunda comprobación con lock
                    cls._instance = cls()
        return cls._instance
```

---

## Comparación de primitivos

| Primitivo | Uso principal | Comportamiento |
|-----------|---------------|----------------|
| Lock | Exclusión mutua básica | Un thread a la vez |
| RLock | Exclusión mutua reentrante | Mismo thread puede readquirir |
| Semaphore | Limitar acceso concurrente | N threads simultáneos |
| Condition | Esperar condiciones | wait/notify pattern |
| Event | Señalización simple | Flag compartido |
| Barrier | Punto de sincronización | Esperar N threads |

### Cuándo usar cada uno

- **Lock:** Proteger modificación de datos compartidos
- **RLock:** Cuando métodos que usan lock llaman a otros métodos que también lo usan
- **Semaphore:** Pool de recursos, rate limiting
- **Condition:** Productor-consumidor, esperar estados específicos
- **Event:** Start/stop signals, one-time notifications
- **Barrier:** Algoritmos por fases, sincronización de grupo

---

## Conceptos clave

1. **Siempre usar `with` para locks** - Garantiza release incluso con excepciones.

2. **Minimizar secciones críticas** - Menos tiempo con lock = mejor concurrencia.

3. **Evitar locks anidados** - Principal causa de deadlocks.

4. **Orden consistente** - Si necesitás múltiples locks, siempre en el mismo orden.

5. **Preferir Queue para comunicación** - Es thread-safe y más simple.

6. **wait() siempre en un loop** - Las condiciones pueden cambiar entre notify y wake.

---

## Preparación para la próxima clase

En la clase 10 vamos a aplicar todas estas primitivas a problemas clásicos de concurrencia: productor-consumidor con buffer acotado, filósofos comensales (deadlock y soluciones), lectores-escritores y patrones de sincronización por fases.

---

*Computación II - 2026 - Clase 11*
