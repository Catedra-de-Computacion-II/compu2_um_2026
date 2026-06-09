# Clase 11: Sincronización Avanzada - Coordinando la Concurrencia

## Introducción: el desafío de la coordinación

En la clase anterior vimos los conceptos básicos de threading y `Lock`, el primitivo de sincronización más simple. Ahora profundizamos: las primitivas avanzadas (`RLock`, `Condition`, `Semaphore`, `Event`, `Barrier`), cómo aparecen los **deadlocks** y patrones más complejos.

La sincronización es quizás el aspecto más difícil de la programación concurrente. Los bugs son sutiles, difíciles de reproducir, y pueden manifestarse solo bajo ciertas condiciones de timing. Entender profundamente los primitivos y cuándo usar cada uno es esencial para escribir código concurrente robusto.

> **Nota:** Todos los ejemplos de esta clase son **completos y ejecutables**. Copialos y corrélos para ver el comportamiento en vivo. El archivo `demo_race_condition.py` que acompaña esta clase demuestra empíricamente cómo la falta de sincronización produce resultados distintos en cada ejecución.

---

## Repaso: por qué necesitamos sincronización

Cuando múltiples threads acceden a recursos compartidos, pueden ocurrir problemas:

### Race condition (clásico: saldo bancario)

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

# Lanzar 10 threads que intentan retirar simultáneamente
hilos = [threading.Thread(target=retirar, args=(200,)) for _ in range(10)]
for h in hilos: h.start()
for h in hilos: h.join()

print(f"Saldo final: {saldo}")  # ¡Puede ser negativo!
```

Para ver la race condition empíricamente, ejecutá [`demo_race_condition.py`](demo_race_condition.py) que viene con esta clase:

```bash
python3 demo_race_condition.py --runs 10
```

### Datos corruptos (estructura compartida)

```python
import threading

# Estructura compartida
datos = {"contador": 0, "suma": 0}

def actualizar(valor):
    # Las dos operaciones deberían ser atómicas
    datos["contador"] += 1
    datos["suma"] += valor
    # Si se interrumpe entre ambas, los datos quedan inconsistentes

# Lanzar 100 threads incrementando
hilos = [threading.Thread(target=actualizar, args=(10,)) for _ in range(100)]
for h in hilos: h.start()
for h in hilos: h.join()

print(f"contador: {datos['contador']}, suma: {datos['suma']}")
# Esperado: contador=100, suma=1000
# Real: puede salir cualquier cosa menor
```

---

## Lock: exclusión mutua básica

El `Lock` garantiza que solo un thread puede ejecutar una sección crítica a la vez. Ya lo vimos en clase 10, acá profundizamos sus modos avanzados.

### Lock con timeout

A veces no querés esperar indefinidamente. `acquire()` acepta un timeout:

```python
import threading
import time

lock = threading.Lock()

def operacion_critica(id):
    print(f"[{id}] Intentando adquirir el lock...")
    # Intentar adquirir con timeout de 5 segundos
    if lock.acquire(timeout=5.0):
        try:
            print(f"[{id}] Lock adquirido, ejecutando operación...")
            time.sleep(3)  # Trabajo dentro de la sección crítica
        finally:
            lock.release()
            print(f"[{id}] Lock liberado")
    else:
        print(f"[{id}] No se pudo adquirir el lock en 5 segundos")

# Lanzar 3 threads: el primero agarra, los otros dos esperan
hilos = [threading.Thread(target=operacion_critica, args=(i,)) for i in range(3)]
for h in hilos: h.start()
for h in hilos: h.join()
```

### Lock no bloqueante

`acquire(blocking=False)` retorna `True` o `False` inmediatamente, sin esperar:

```python
import threading
import time

lock = threading.Lock()

def operacion_no_bloqueante(id):
    if lock.acquire(blocking=False):
        try:
            print(f"[{id}] Lock disponible, ejecutando...")
            time.sleep(1)
        finally:
            lock.release()
    else:
        print(f"[{id}] Lock ocupado, haciendo otra cosa...")

# 5 threads compiten: solo uno entra, los demás siguen de largo
hilos = [threading.Thread(target=operacion_no_bloqueante, args=(i,)) for i in range(5)]
for h in hilos: h.start()
for h in hilos: h.join()
```

### RLock: lock reentrante

`RLock` permite que el **mismo thread** adquiera el lock múltiples veces sin bloquearse. Es útil cuando un método protegido por lock llama a otro método que también necesita el mismo lock.

```python
import threading

class CuentaBancaria:
    def __init__(self, saldo_inicial):
        self.saldo = saldo_inicial
        self.lock = threading.RLock()

    def depositar(self, cantidad):
        with self.lock:
            self.saldo += cantidad
            print(f"Depositados {cantidad}. Saldo: {self.saldo}")

    def retirar(self, cantidad):
        with self.lock:
            if self.saldo >= cantidad:
                self.saldo -= cantidad
                print(f"Retirados {cantidad}. Saldo: {self.saldo}")
                return True
            return False

    def transferir_a(self, otra_cuenta, cantidad):
        # Este método adquiere self.lock Y llama a retirar()
        # que también adquiere self.lock. Con Lock normal: DEADLOCK.
        # Con RLock: funciona, porque es el mismo thread.
        with self.lock:
            if self.retirar(cantidad):
                otra_cuenta.depositar(cantidad)
                return True
            return False


cuenta_a = CuentaBancaria(1000)
cuenta_b = CuentaBancaria(500)

# Transferencia en un thread
t = threading.Thread(target=cuenta_a.transferir_a, args=(cuenta_b, 300))
t.start()
t.join()

print(f"Saldo A: {cuenta_a.saldo}")  # 700
print(f"Saldo B: {cuenta_b.saldo}")  # 800
```

### El peligro: deadlock con múltiples locks

Cuando dos threads adquieren dos locks distintos en **orden inverso**, se cuelgan mutuamente:

```python
import threading
import time

lock_a = threading.Lock()
lock_b = threading.Lock()

def thread_1():
    with lock_a:
        print("Thread 1: tengo A")
        time.sleep(0.1)
        print("Thread 1: pidiendo B...")
        with lock_b:  # Espera B
            print("Thread 1: tengo A y B")

def thread_2():
    with lock_b:
        print("Thread 2: tengo B")
        time.sleep(0.1)
        print("Thread 2: pidiendo A...")
        with lock_a:  # Espera A: DEADLOCK
            print("Thread 2: tengo B y A")

t1 = threading.Thread(target=thread_1)
t2 = threading.Thread(target=thread_2)
t1.start(); t2.start()
# El programa se cuelga: ninguno termina porque cada uno espera al otro.
# Matar con Ctrl+C después de verlo colgado.
```

### Solución: orden consistente

La regla de oro: **siempre adquirir los locks en el mismo orden** en todos los threads.

```python
import threading

lock_a = threading.Lock()
lock_b = threading.Lock()

def thread_1():
    with lock_a:
        with lock_b:
            print("Thread 1: tengo A y B")

def thread_2():
    with lock_a:    # Mismo orden que thread_1
        with lock_b:
            print("Thread 2: tengo A y B")

t1 = threading.Thread(target=thread_1)
t2 = threading.Thread(target=thread_2)
t1.start(); t2.start()
t1.join(); t2.join()
```

Otra solución, cuando sea posible: **usar un solo lock que proteja a ambos recursos**.

---

## Condition: esperar por condiciones

`Condition` combina un lock con la capacidad de **esperar** y **notificar**. Útil cuando un thread necesita esperar a que cierta condición sea verdadera, y otro thread la hace verdadera.

### El patrón básico

```python
import threading
import time

condition = threading.Condition()
datos_disponibles = False
datos = None

def productor():
    global datos_disponibles, datos
    time.sleep(2)  # simular trabajo de producción

    with condition:
        datos = "datos producidos"
        datos_disponibles = True
        print("Productor: datos listos, notificando")
        condition.notify()  # notify_all() para despertar a todos

def consumidor(id):
    global datos_disponibles

    with condition:
        print(f"Consumidor {id}: esperando datos...")
        while not datos_disponibles:
            condition.wait()  # Libera el lock mientras espera
        print(f"Consumidor {id}: recibí '{datos}'")


t_prod = threading.Thread(target=productor)
t_cons = threading.Thread(target=consumidor, args=(1,))

t_cons.start()  # consumidor arranca primero, espera
t_prod.start()  # productor produce y notifica

t_prod.join()
t_cons.join()
```

> **Regla importante**: siempre usar `while` (no `if`) en la condición. Existen "spurious wakeups": un thread puede despertarse sin que se haya cumplido la condición. El loop garantiza re-chequear.

### Buffer acotado con Condition (productor-consumidor)

Patrón clásico: productores que generan datos, consumidores que los procesan, con un buffer de capacidad limitada.

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
            while len(self.buffer) >= self.capacidad:
                print(f"Buffer lleno ({len(self.buffer)}/{self.capacidad}), productor espera...")
                self.condition.wait()

            self.buffer.append(item)
            print(f"+ {item}  buffer: {len(self.buffer)}/{self.capacidad}")
            self.condition.notify_all()

    def get(self):
        with self.condition:
            while len(self.buffer) == 0:
                print("Buffer vacío, consumidor espera...")
                self.condition.wait()

            item = self.buffer.pop(0)
            print(f"- {item}  buffer: {len(self.buffer)}/{self.capacidad}")
            self.condition.notify_all()
            return item


buffer = BufferAcotado(3)

def productor(id):
    for i in range(5):
        time.sleep(random.uniform(0.1, 0.5))
        buffer.put(f"item-{id}-{i}")

def consumidor(id):
    for _ in range(5):
        time.sleep(random.uniform(0.2, 0.6))
        buffer.get()


productores = [threading.Thread(target=productor, args=(i,)) for i in range(2)]
consumidores = [threading.Thread(target=consumidor, args=(i,)) for i in range(2)]

for t in productores + consumidores:
    t.start()
for t in productores + consumidores:
    t.join()

print("Todos terminaron")
```

### wait() con timeout

```python
import threading
import time

condition = threading.Condition()

def esperador():
    with condition:
        print("Esperando hasta 5 segundos...")
        resultado = condition.wait(timeout=5.0)
        if resultado:
            print("Condición notificada a tiempo")
        else:
            print("Timeout: no hubo notificación")

t = threading.Thread(target=esperador)
t.start()
# Nadie llama a notify(): el thread espera 5s y reporta timeout
t.join()
```

---

## Semaphore: control de acceso concurrente

Un `Semaphore` mantiene un contador interno que controla cuántos threads pueden acceder a un recurso. Útil para limitar concurrencia (rate limiting, pools de conexiones).

### Semáforo básico: pool de conexiones simulado

```python
import threading
import time
import random

# Máximo 3 conexiones simultáneas
pool_conexiones = threading.Semaphore(3)

def usar_conexion(id):
    print(f"[{id}] Esperando conexión...")
    with pool_conexiones:
        print(f"[{id}] Conectado")
        time.sleep(random.uniform(1, 2))  # Trabajo con la conexión
        print(f"[{id}] Desconectando")


# 10 threads compiten por las 3 conexiones disponibles
hilos = [threading.Thread(target=usar_conexion, args=(i,)) for i in range(10)]
for t in hilos: t.start()
for t in hilos: t.join()
print("Todos terminaron")
```

### BoundedSemaphore: prevenir errores de release

`Semaphore` deja que llames `release()` más veces que `acquire()` (el contador crece indefinidamente). `BoundedSemaphore` lanza error si pasa eso:

```python
import threading

# Semaphore: no chequea
sem = threading.Semaphore(2)
sem.release()  # OK, contador = 3 (¡error silencioso!)
print(f"Semaphore contador: ahora {sem._value}")

# BoundedSemaphore: lanza ValueError
bsem = threading.BoundedSemaphore(2)
try:
    bsem.release()  # Excede el valor inicial
except ValueError as e:
    print(f"BoundedSemaphore detectó el error: {e}")
```

### Semáforo binario vs Lock

Un `Semaphore(1)` se parece a un `Lock`, pero hay una diferencia importante:

- **Lock**: conceptualmente, solo el thread que adquirió puede liberar. (En Python en realidad no se enforce, pero es la convención.)
- **Semaphore**: cualquier thread puede liberar.

Esto permite usar `Semaphore` para casos donde la liberación se hace desde otro thread, pero al costo de perder esa garantía:

```python
import threading
import time

sem = threading.Semaphore(0)  # arranca en 0 (bloqueado)

def consumidor():
    print("Consumidor: esperando señal...")
    sem.acquire()
    print("Consumidor: recibí señal, sigo")

def disparador():
    time.sleep(2)
    print("Disparador: enviando señal")
    sem.release()  # OK aunque sea otro thread

t1 = threading.Thread(target=consumidor)
t2 = threading.Thread(target=disparador)
t1.start(); t2.start()
t1.join(); t2.join()
```

---

## Event: señalización simple

`Event` es un flag thread-safe que threads pueden esperar. Más simple que `Condition` cuando solo querés notificar "esto pasó".

### Patrón de inicio coordinado: la línea de largada

```python
import threading
import time
import random

inicio = threading.Event()

def corredor(id):
    print(f"[Corredor {id}] En la línea de partida...")
    inicio.wait()  # Bloquea hasta que inicio.set()
    print(f"[Corredor {id}] ¡Arrancó!")
    tiempo = random.uniform(1, 3)
    time.sleep(tiempo)
    print(f"[Corredor {id}] Llegó en {tiempo:.2f}s")


corredores = [threading.Thread(target=corredor, args=(i,)) for i in range(5)]
for t in corredores: t.start()

# Dar tiempo a que todos lleguen a la línea
time.sleep(1)

print("\n=== PREPARADOS... LISTOS... YA! ===\n")
inicio.set()  # Todos arrancan simultáneamente

for t in corredores: t.join()
```

### Patrón de cancelación: workers que se pueden detener

```python
import threading
import time

detener = threading.Event()

def worker_cancelable(id):
    print(f"[Worker {id}] Iniciado")
    i = 0
    while not detener.is_set():
        print(f"[Worker {id}] Iteración {i}")
        i += 1
        # wait() con timeout permite chequear periódicamente sin polling activo
        detener.wait(timeout=1.0)
    print(f"[Worker {id}] Detenido limpiamente")


workers = [threading.Thread(target=worker_cancelable, args=(i,)) for i in range(3)]
for t in workers: t.start()

time.sleep(3)
print("\n=== Solicitando detención de todos los workers ===\n")
detener.set()

for t in workers: t.join()
print("Todos terminaron")
```

### Métodos de Event

```python
import threading

evento = threading.Event()

evento.set()            # señala (estado = True)
print(evento.is_set())  # True
evento.clear()          # resetea (estado = False)
print(evento.is_set())  # False

# wait() retorna True si fue señalado, False si timeout
evento.set()
print(evento.wait(timeout=1.0))   # True, inmediato
```

### Event vs Condition

| Event | Condition |
|-------|-----------|
| Flag booleano simple | Permite condiciones complejas |
| `set()` despierta a todos los que esperan | `notify()` puede despertar uno solo |
| El estado persiste hasta `clear()` | Se combina con predicados (variables externas) |
| Más simple | Más flexible |

---

## Barrier: punto de sincronización

`Barrier` hace que N threads esperen hasta que todos lleguen a un punto. Útil para algoritmos paralelos por fases.

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
    barrera.wait()  # espera a que los 4 lleguen

    # Fase 2
    print(f"[{id}] Fase 2: trabajando...")
    time.sleep(random.uniform(0.5, 1.5))
    print(f"[{id}] Fase 2: completada, esperando en barrera...")
    barrera.wait()  # espera a que los 4 lleguen

    print(f"[{id}] Todas las fases completadas")


hilos = [threading.Thread(target=fase, args=(i,)) for i in range(4)]
for t in hilos: t.start()
for t in hilos: t.join()
```

### Barrier con acción

Podés pasar una función que se ejecuta **una sola vez**, cuando todos llegan a la barrera:

```python
import threading
import time

def cuando_todos_llegan():
    print(">>> TODOS LLEGARON A LA BARRERA <<<")

barrera = threading.Barrier(3, action=cuando_todos_llegan)

def worker(id):
    print(f"[{id}] llegó")
    barrera.wait()
    print(f"[{id}] continúa")

hilos = [threading.Thread(target=worker, args=(i,)) for i in range(3)]
for t in hilos: t.start()
for t in hilos: t.join()
```

### Barrier con timeout

Si un thread no llega en el timeout, la barrera se "rompe" y todos los esperando reciben `BrokenBarrierError`:

```python
import threading
import time

barrera = threading.Barrier(3)

def worker(id, delay):
    time.sleep(delay)
    try:
        barrera.wait(timeout=2.0)
        print(f"[{id}] Pasó la barrera")
    except threading.BrokenBarrierError:
        print(f"[{id}] Barrera rota: alguien no llegó")

hilos = [
    threading.Thread(target=worker, args=(0, 0.5)),
    threading.Thread(target=worker, args=(1, 1.0)),
    threading.Thread(target=worker, args=(2, 5.0)),  # éste tarda demasiado
]
for t in hilos: t.start()
for t in hilos: t.join()
```

---

## Patrones de sincronización

### Readers-Writers Lock

Múltiples threads pueden leer simultáneamente, pero un escritor necesita acceso exclusivo. La standard library de Python no lo provee, pero se puede implementar:

```python
import threading
import time
import random

class ReadWriteLock:
    """Lock que permite múltiples lectores O un solo escritor."""

    def __init__(self):
        self.readers = 0
        self.resource_lock = threading.Lock()   # protege el recurso
        self.readers_lock = threading.Lock()    # protege el contador

    def acquire_read(self):
        with self.readers_lock:
            self.readers += 1
            if self.readers == 1:
                # El primer lector toma el lock del recurso
                self.resource_lock.acquire()

    def release_read(self):
        with self.readers_lock:
            self.readers -= 1
            if self.readers == 0:
                # El último lector libera el recurso
                self.resource_lock.release()

    def acquire_write(self):
        self.resource_lock.acquire()

    def release_write(self):
        self.resource_lock.release()


# Uso con context managers
class ReadContext:
    def __init__(self, rwlock): self.rwlock = rwlock
    def __enter__(self): self.rwlock.acquire_read()
    def __exit__(self, *args): self.rwlock.release_read()

class WriteContext:
    def __init__(self, rwlock): self.rwlock = rwlock
    def __enter__(self): self.rwlock.acquire_write()
    def __exit__(self, *args): self.rwlock.release_write()


rwlock = ReadWriteLock()
datos = {"valor": 0}

def lector(id):
    for _ in range(3):
        with ReadContext(rwlock):
            print(f"[Lector {id}] leyendo: {datos}")
            time.sleep(0.1)
        time.sleep(random.uniform(0.1, 0.3))

def escritor(id):
    for i in range(3):
        with WriteContext(rwlock):
            datos["valor"] = i * 100 + id
            print(f"[Escritor {id}] escribió: {datos}")
            time.sleep(0.2)
        time.sleep(random.uniform(0.2, 0.5))


hilos = (
    [threading.Thread(target=lector, args=(i,)) for i in range(3)] +
    [threading.Thread(target=escritor, args=(i,)) for i in range(2)]
)
for t in hilos: t.start()
for t in hilos: t.join()
```

> **Atención**: esta implementación favorece a los lectores (writer starvation posible). Variantes más justas existen pero son más complejas.

### Double-checked locking

Para inicialización lazy thread-safe (típico en singletons):

```python
import threading

class Singleton:
    _instance = None
    _lock = threading.Lock()

    @classmethod
    def get_instance(cls):
        if cls._instance is None:           # primera comprobación SIN lock (rápido)
            with cls._lock:
                if cls._instance is None:   # segunda comprobación CON lock (correcto)
                    cls._instance = cls()
        return cls._instance

# Uso desde múltiples threads
import threading
def crear():
    s = Singleton.get_instance()
    print(f"{threading.current_thread().name}: instancia = {id(s)}")

hilos = [threading.Thread(target=crear) for _ in range(5)]
for t in hilos: t.start()
for t in hilos: t.join()
# Todos ven el mismo id() (misma instancia)
```

---

## Comparación de primitivos

| Primitivo | Uso principal | Comportamiento |
|-----------|---------------|----------------|
| `Lock` | Exclusión mutua básica | Un thread a la vez |
| `RLock` | Exclusión mutua reentrante | Mismo thread puede readquirir |
| `Semaphore` | Limitar acceso concurrente | N threads simultáneos |
| `BoundedSemaphore` | Como Semaphore, con chequeo | Lanza error si se libera demás |
| `Condition` | Esperar condiciones | `wait`/`notify` pattern |
| `Event` | Señalización simple | Flag compartido |
| `Barrier` | Punto de sincronización | Esperar a N threads |

### Cuándo usar cada uno

- **Lock**: proteger modificación de datos compartidos
- **RLock**: cuando métodos que usan lock llaman a otros métodos que también lo usan
- **Semaphore**: pool de recursos, rate limiting
- **Condition**: productor-consumidor, esperar estados específicos
- **Event**: start/stop signals, one-time notifications
- **Barrier**: algoritmos por fases, sincronización de grupo

---

## Conceptos clave

1. **Siempre usar `with` para locks**: garantiza release incluso con excepciones
2. **Minimizar secciones críticas**: menos tiempo con lock = mejor concurrencia
3. **Evitar locks anidados**: principal causa de deadlocks
4. **Orden consistente**: si necesitás múltiples locks, siempre en el mismo orden
5. **Preferir Queue para comunicación**: es thread-safe y más simple
6. **`wait()` siempre en un loop `while`**: las condiciones pueden cambiar entre notify y wake (spurious wakeups)

---

## Preparación para la próxima clase

En la **clase 12 (Sincronización II)** vamos a aplicar todas estas primitivas a problemas clásicos de concurrencia: productor-consumidor con buffer acotado, filósofos comensales (deadlock y soluciones), lectores-escritores y patrones de sincronización por fases.

---

*Computación II - 2026 - Clase 11*
