# Clase 11: Sincronización Avanzada - Ejercicios Prácticos

## Ejercicio 1: Detectando race conditions

### 1.1 Cuenta bancaria con race condition

```python
#!/usr/bin/env python3
"""Demostración de race condition en cuenta bancaria."""
import threading
import time
import random

class CuentaInsegura:
    def __init__(self, saldo):
        self.saldo = saldo

    def depositar(self, cantidad):
        actual = self.saldo
        time.sleep(0.001)  # Simula procesamiento
        self.saldo = actual + cantidad

    def retirar(self, cantidad):
        actual = self.saldo
        time.sleep(0.001)
        if actual >= cantidad:
            self.saldo = actual - cantidad
            return True
        return False

# Probar
cuenta = CuentaInsegura(1000)

def operaciones_aleatorias():
    for _ in range(100):
        if random.choice([True, False]):
            cuenta.depositar(10)
        else:
            cuenta.retirar(10)

threads = [threading.Thread(target=operaciones_aleatorias) for _ in range(10)]
for t in threads:
    t.start()
for t in threads:
    t.join()

print(f"Saldo esperado: 1000 (si no hay errores)")
print(f"Saldo obtenido: {cuenta.saldo}")
```

### 1.2 Cuenta bancaria corregida

```python
#!/usr/bin/env python3
"""Cuenta bancaria thread-safe."""
import threading
import time
import random

class CuentaSegura:
    def __init__(self, saldo):
        self.saldo = saldo
        self.lock = threading.Lock()

    def depositar(self, cantidad):
        with self.lock:
            actual = self.saldo
            time.sleep(0.001)
            self.saldo = actual + cantidad

    def retirar(self, cantidad):
        with self.lock:
            actual = self.saldo
            time.sleep(0.001)
            if actual >= cantidad:
                self.saldo = actual - cantidad
                return True
            return False

# TODO: Modificar el test anterior para usar CuentaSegura
# y verificar que el saldo es correcto
```

---

## Ejercicio 2: Productor-Consumidor con Condition

### 2.1 Implementación básica

```python
#!/usr/bin/env python3
"""Productor-consumidor con Condition."""
import threading
import time
import random

class ColaLimitada:
    def __init__(self, maxsize):
        self.maxsize = maxsize
        self.items = []
        self.condition = threading.Condition()

    def put(self, item, timeout=None):
        """Agrega un item. Bloquea si está llena."""
        with self.condition:
            while len(self.items) >= self.maxsize:
                if not self.condition.wait(timeout):
                    raise TimeoutError("Timeout esperando espacio")

            self.items.append(item)
            self.condition.notify()

    def get(self, timeout=None):
        """Obtiene un item. Bloquea si está vacía."""
        with self.condition:
            while len(self.items) == 0:
                if not self.condition.wait(timeout):
                    raise TimeoutError("Timeout esperando item")

            item = self.items.pop(0)
            self.condition.notify()
            return item

    def size(self):
        with self.condition:
            return len(self.items)

# Test
cola = ColaLimitada(5)
terminado = threading.Event()

def productor(id, cantidad):
    for i in range(cantidad):
        item = f"P{id}-{i}"
        cola.put(item)
        print(f"[Prod-{id}] Produjo {item}, cola={cola.size()}")
        time.sleep(random.uniform(0.1, 0.3))
    print(f"[Prod-{id}] Terminó")

def consumidor(id):
    while not (terminado.is_set() and cola.size() == 0):
        try:
            item = cola.get(timeout=0.5)
            print(f"[Cons-{id}] Consumió {item}, cola={cola.size()}")
            time.sleep(random.uniform(0.2, 0.4))
        except TimeoutError:
            pass
    print(f"[Cons-{id}] Terminó")

# Crear threads
threads = []
for i in range(2):
    threads.append(threading.Thread(target=productor, args=(i, 5)))
for i in range(3):
    threads.append(threading.Thread(target=consumidor, args=(i,)))

for t in threads:
    t.start()

# Esperar productores
for t in threads[:2]:
    t.join()

terminado.set()

for t in threads[2:]:
    t.join()

print("Fin del programa")
```

---

## Ejercicio 3: Barrier para procesamiento por fases

```python
#!/usr/bin/env python3
"""Procesamiento paralelo por fases con Barrier."""
import threading
import time
import random

NUM_WORKERS = 4
datos = [0] * NUM_WORKERS
resultados_fase1 = [0] * NUM_WORKERS
resultados_fase2 = [0] * NUM_WORKERS

def imprimir_estado():
    print(f"  Resultados fase 1: {resultados_fase1}")
    print(f"  Resultados fase 2: {resultados_fase2}")

barrera = threading.Barrier(NUM_WORKERS, action=imprimir_estado)

def worker(id):
    global datos, resultados_fase1, resultados_fase2

    # Fase 1: procesar datos locales
    print(f"[Worker {id}] Fase 1: procesando...")
    time.sleep(random.uniform(0.5, 1.5))
    resultados_fase1[id] = datos[id] * 2
    print(f"[Worker {id}] Fase 1: completada")

    barrera.wait()  # Sincronizar

    # Fase 2: combinar con vecinos
    print(f"[Worker {id}] Fase 2: combinando...")
    time.sleep(random.uniform(0.3, 0.8))
    vecino = (id + 1) % NUM_WORKERS
    resultados_fase2[id] = resultados_fase1[id] + resultados_fase1[vecino]
    print(f"[Worker {id}] Fase 2: completada")

    barrera.wait()  # Sincronizar

    print(f"[Worker {id}] Procesamiento completo!")

# Inicializar datos
datos = [i * 10 for i in range(NUM_WORKERS)]
print(f"Datos iniciales: {datos}\n")

threads = [threading.Thread(target=worker, args=(i,)) for i in range(NUM_WORKERS)]
for t in threads:
    t.start()
for t in threads:
    t.join()

print(f"\nResultados finales: {resultados_fase2}")
```

---

## Ejercicio 4: Semáforo para pool de recursos

```python
#!/usr/bin/env python3
"""Pool de conexiones con Semaphore."""
import threading
import time
import random

class ConnectionPool:
    def __init__(self, size):
        self.size = size
        self.semaforo = threading.Semaphore(size)
        self.conexiones_disponibles = list(range(size))
        self.lock = threading.Lock()
        self.estadisticas = {
            "total_requests": 0,
            "esperas": 0,
            "tiempo_total_espera": 0
        }

    def obtener(self, timeout=None):
        inicio = time.time()
        if self.semaforo.acquire(timeout=timeout):
            tiempo_espera = time.time() - inicio
            with self.lock:
                conn_id = self.conexiones_disponibles.pop(0)
                self.estadisticas["total_requests"] += 1
                if tiempo_espera > 0.01:
                    self.estadisticas["esperas"] += 1
                    self.estadisticas["tiempo_total_espera"] += tiempo_espera
            return conn_id
        return None

    def liberar(self, conn_id):
        with self.lock:
            self.conexiones_disponibles.append(conn_id)
        self.semaforo.release()

    def mostrar_estadisticas(self):
        print(f"\n=== Estadísticas del pool ===")
        print(f"Total requests: {self.estadisticas['total_requests']}")
        print(f"Requests que esperaron: {self.estadisticas['esperas']}")
        if self.estadisticas['esperas'] > 0:
            prom = self.estadisticas['tiempo_total_espera'] / self.estadisticas['esperas']
            print(f"Tiempo promedio espera: {prom:.3f}s")

# Pool de 3 conexiones
pool = ConnectionPool(3)

def cliente(id):
    for _ in range(3):
        conn = pool.obtener(timeout=5)
        if conn is not None:
            print(f"[Cliente {id}] Obtuvo conexión {conn}")
            time.sleep(random.uniform(0.5, 1.5))  # Usar conexión
            pool.liberar(conn)
            print(f"[Cliente {id}] Liberó conexión {conn}")
        else:
            print(f"[Cliente {id}] Timeout esperando conexión")
        time.sleep(random.uniform(0.1, 0.3))

# 10 clientes
threads = [threading.Thread(target=cliente, args=(i,)) for i in range(10)]
for t in threads:
    t.start()
for t in threads:
    t.join()

pool.mostrar_estadisticas()
```

---

## Ejercicio 5: Readers-Writers (Obligatorio)

### Objetivo

Implementar un lock de lectores-escritores que permita múltiples lectores simultáneos pero solo un escritor a la vez.

### Especificación

```python
#!/usr/bin/env python3
"""
Implementación de Readers-Writers Lock.

Reglas:
- Múltiples lectores pueden leer simultáneamente
- Solo un escritor puede escribir a la vez
- Mientras hay escritor, no pueden haber lectores
- Mientras hay lectores, no pueden haber escritores
"""
import threading
import time
import random

class ReadWriteLock:
    def __init__(self):
        self.readers = 0
        self.writers = 0
        self.lock = threading.Lock()
        self.can_read = threading.Condition(self.lock)
        self.can_write = threading.Condition(self.lock)

    def acquire_read(self):
        """Adquirir lock para lectura."""
        with self.lock:
            while self.writers > 0:
                self.can_read.wait()
            self.readers += 1

    def release_read(self):
        """Liberar lock de lectura."""
        with self.lock:
            self.readers -= 1
            if self.readers == 0:
                self.can_write.notify()

    def acquire_write(self):
        """Adquirir lock para escritura."""
        with self.lock:
            while self.readers > 0 or self.writers > 0:
                self.can_write.wait()
            self.writers += 1

    def release_write(self):
        """Liberar lock de escritura."""
        with self.lock:
            self.writers -= 1
            self.can_read.notify_all()
            self.can_write.notify()

# Context managers para uso más simple
class ReadLock:
    def __init__(self, rwlock):
        self.rwlock = rwlock

    def __enter__(self):
        self.rwlock.acquire_read()

    def __exit__(self, *args):
        self.rwlock.release_read()

class WriteLock:
    def __init__(self, rwlock):
        self.rwlock = rwlock

    def __enter__(self):
        self.rwlock.acquire_write()

    def __exit__(self, *args):
        self.rwlock.release_write()

# Test
rwlock = ReadWriteLock()
datos = {"valor": 0, "lecturas": 0, "escrituras": 0}

def lector(id):
    for _ in range(5):
        with ReadLock(rwlock):
            valor = datos["valor"]
            datos["lecturas"] += 1
            print(f"[Lector {id}] Leyó valor={valor}")
            time.sleep(random.uniform(0.05, 0.15))
        time.sleep(random.uniform(0.1, 0.2))

def escritor(id):
    for i in range(3):
        with WriteLock(rwlock):
            datos["valor"] = id * 100 + i
            datos["escrituras"] += 1
            print(f"[Escritor {id}] Escribió valor={datos['valor']}")
            time.sleep(random.uniform(0.1, 0.2))
        time.sleep(random.uniform(0.2, 0.4))

# Crear threads
threads = []
for i in range(5):
    threads.append(threading.Thread(target=lector, args=(i,)))
for i in range(2):
    threads.append(threading.Thread(target=escritor, args=(i,)))

random.shuffle(threads)  # Mezclar orden de inicio

for t in threads:
    t.start()
for t in threads:
    t.join()

print(f"\nEstadísticas finales:")
print(f"  Valor final: {datos['valor']}")
print(f"  Total lecturas: {datos['lecturas']}")
print(f"  Total escrituras: {datos['escrituras']}")
```

---

## Ejercicio 6: Deadlock detector

```python
#!/usr/bin/env python3
"""Demostración y prevención de deadlock."""
import threading
import time

# Versión con deadlock potencial
def demostrar_deadlock():
    lock_a = threading.Lock()
    lock_b = threading.Lock()

    def thread_1():
        with lock_a:
            print("Thread 1: tiene A")
            time.sleep(0.1)
            with lock_b:
                print("Thread 1: tiene A y B")

    def thread_2():
        with lock_b:
            print("Thread 2: tiene B")
            time.sleep(0.1)
            with lock_a:
                print("Thread 2: tiene B y A")

    t1 = threading.Thread(target=thread_1)
    t2 = threading.Thread(target=thread_2)

    t1.start()
    t2.start()

    # Timeout para detectar deadlock
    t1.join(timeout=2)
    t2.join(timeout=2)

    if t1.is_alive() or t2.is_alive():
        print("¡DEADLOCK DETECTADO!")
        return False
    return True

# Versión corregida: orden consistente
def version_corregida():
    lock_a = threading.Lock()
    lock_b = threading.Lock()

    def thread_ordenado(nombre):
        with lock_a:  # Siempre A primero
            print(f"{nombre}: tiene A")
            with lock_b:  # Luego B
                print(f"{nombre}: tiene A y B")
                time.sleep(0.1)

    t1 = threading.Thread(target=thread_ordenado, args=("Thread 1",))
    t2 = threading.Thread(target=thread_ordenado, args=("Thread 2",))

    t1.start()
    t2.start()
    t1.join()
    t2.join()

    print("¡Completado sin deadlock!")

print("=== Versión con deadlock ===")
demostrar_deadlock()

print("\n=== Versión corregida ===")
version_corregida()
```

---

## Verificación del ejercicio obligatorio

### Ejercicio 5: Readers-Writers Lock

Tu implementación debe:

- [ ] Permitir múltiples lectores simultáneos
- [ ] Bloquear escritores mientras hay lectores
- [ ] Bloquear lectores mientras hay escritor
- [ ] Solo permitir un escritor a la vez
- [ ] Usar Condition para la espera
- [ ] Implementar context managers para uso fácil
- [ ] No causar deadlocks ni starvation evidente

---

## Ejercicios adicionales

### Monitor de recursos

Implementá un monitor que muestre el estado de locks/semáforos en tiempo real.

### Dining philosophers

Implementá el problema clásico de los filósofos cenando con prevención de deadlock.

### Rate limiter thread-safe

Implementá un limitador de rate que permita máximo N operaciones por segundo.

---

*Computación II - 2026 - Clase 11*
