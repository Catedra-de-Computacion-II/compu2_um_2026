# Clase 9: Threads - Concurrencia dentro del Proceso

## Introducción: otra forma de hacer varias cosas a la vez

En las clases 7 y 8 vimos `multiprocessing`: crear procesos separados, cada uno con su propia memoria, comunicándose por colas, pipes o memoria compartida. La separación es buena para aislamiento pero costosa: crear un proceso es caro, y comunicar datos requiere mecanismos explícitos.

Los **threads** (hilos de ejecución) ofrecen una alternativa. Múltiples threads dentro del mismo proceso comparten memoria, comparten file descriptors, comparten casi todo. Esto hace que la comunicación sea trivial (simplemente accedés a las mismas variables), pero introduce nuevos desafíos: si dos threads modifican la misma variable simultáneamente, pueden ocurrir cosas muy malas.

### Objetivos de la clase

- Comprender el modelo de concurrencia basado en hilos
- Conocer el módulo `threading` de Python y sus primitivas básicas
- Entender el GIL (Global Interpreter Lock) y sus implicancias
- Distinguir cuándo conviene `threading` vs `multiprocessing`
- Detectar race conditions y conocer `Lock` como solución básica
- Anticipar las primitivas de sincronización que se ven en detalle en las clases 10 y 11

---

## Threads vs Procesos

### Qué comparten los threads

Threads del mismo proceso comparten:
- Espacio de memoria (variables globales, heap)
- File descriptors abiertos
- Directorio de trabajo actual
- ID de usuario y grupo
- Handlers de señales

Cada thread tiene su propio:
- Stack (variables locales)
- Program counter (dónde está ejecutando)
- Registros del CPU
- ID de thread

```
Proceso con múltiples threads:

┌────────────────────────────────────────────────┐
│                    Proceso                      │
│  ┌─────────────────────────────────────────┐   │
│  │         Memoria compartida              │   │
│  │   (globales, heap, file descriptors)    │   │
│  └─────────────────────────────────────────┘   │
│                                                │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐        │
│  │ Thread 1│  │ Thread 2│  │ Thread 3│        │
│  │ stack   │  │ stack   │  │ stack   │        │
│  │ PC      │  │ PC      │  │ PC      │        │
│  └─────────┘  └─────────┘  └─────────┘        │
└────────────────────────────────────────────────┘
```

### Diferencias clave: Proceso vs Hilo

| Característica     | Proceso             | Hilo               |
|--------------------|---------------------|--------------------|
| Memoria            | Separada (copia)    | Compartida         |
| Comunicación       | IPC (pipes, colas)  | Variables directas |
| Costo de creación  | Alto                | Bajo               |
| Aislamiento        | Alto                | Bajo               |
| Paralelismo real   | Sí (multi-core)     | Limitado por GIL   |

### Ventajas de threads

1. Creación más rápida — no hay que duplicar memoria
2. Comunicación trivial — comparten variables
3. Cambio de contexto más rápido — menos estado que guardar
4. Menor uso de memoria — una copia del código y datos

### Desventajas de threads

1. Sin aislamiento — un thread que crashea puede afectar a todos
2. Bugs de sincronización — race conditions, deadlocks
3. Más difíciles de debuggear — problemas no determinísticos
4. En Python: el GIL — limitación importante que veremos a continuación

---

## Creando threads en Python

### El módulo threading

Python provee el módulo `threading` para trabajar con threads:

```python
import threading
import time

def tarea(nombre, duracion):
    print(f"[{nombre}] Iniciando...")
    time.sleep(duracion)
    print(f"[{nombre}] Terminado!")

# Crear threads
t1 = threading.Thread(target=tarea, args=("Thread-1", 2))
t2 = threading.Thread(target=tarea, args=("Thread-2", 1))

# Iniciar threads
t1.start()
t2.start()

print("[Main] Threads iniciados")

# Esperar a que terminen
t1.join()
t2.join()

print("[Main] Todos los threads terminaron")
```

Salida típica:
```
[Thread-1] Iniciando...
[Thread-2] Iniciando...
[Main] Threads iniciados
[Thread-2] Terminado!
[Thread-1] Terminado!
[Main] Todos los threads terminaron
```

### Thread como clase

También podés crear threads heredando de `Thread`:

```python
import threading
import time

class MiThread(threading.Thread):
    def __init__(self, nombre, duracion):
        super().__init__()
        self.nombre = nombre
        self.duracion = duracion
        self.resultado = None

    def run(self):
        """Este método se ejecuta cuando llamás start()."""
        print(f"[{self.nombre}] Trabajando...")
        time.sleep(self.duracion)
        self.resultado = f"Completado en {self.duracion}s"
        print(f"[{self.nombre}] {self.resultado}")

# Crear y ejecutar
t = MiThread("Worker", 2)
t.start()
t.join()
print(f"Resultado: {t.resultado}")
```

### Atributos y métodos importantes

```python
import threading

h = threading.Thread(target=mi_funcion, name="mi-hilo", daemon=True)

h.start()           # Iniciar el hilo
h.join()            # Esperar a que termine
h.join(timeout=5)   # Esperar máximo 5 segundos
h.is_alive()        # True si el hilo está corriendo
h.name              # Nombre del hilo
h.ident             # ID del hilo (asignado tras start())
h.daemon            # True si es daemon

# Hilo actual
threading.current_thread()        # Objeto del hilo actual
threading.main_thread()           # Objeto del hilo principal
threading.active_count()          # Cantidad de hilos activos
threading.enumerate()             # Lista de hilos activos
```

### Identificando threads

```python
import threading

def mostrar_info():
    thread_actual = threading.current_thread()
    print(f"Nombre: {thread_actual.name}")
    print(f"ID: {thread_actual.ident}")
    print(f"Daemon: {thread_actual.daemon}")

# Thread principal
print("=== Main thread ===")
mostrar_info()

# En un thread secundario
print("\n=== Thread secundario ===")
t = threading.Thread(target=mostrar_info, name="MiThread")
t.start()
t.join()

# Listar todos los threads activos
print(f"\nThreads activos: {threading.active_count()}")
for t in threading.enumerate():
    print(f"  - {t.name}")
```

---

## El GIL: Global Interpreter Lock

### ¿Qué es el GIL?

El GIL es un mutex que protege el acceso a objetos de Python, impidiendo que múltiples threads ejecuten bytecode Python simultáneamente. En la práctica, esto significa que **los threads de Python no aprovechan múltiples CPUs para código Python**.

```
Sin GIL (ideal):                Con GIL (Python tradicional):
Núcleo 1: [T1][T1][T1][T1]      Núcleo 1: [T1][T2][T1][T2]
Núcleo 2: [T2][T2][T2][T2]      Núcleo 2: [--][--][--][--]
```

```python
import threading
import time

def contar(n):
    """Tarea CPU-bound."""
    total = 0
    for i in range(n):
        total += i
    return total

N = 50_000_000

# Secuencial
inicio = time.time()
contar(N)
contar(N)
print(f"Secuencial: {time.time() - inicio:.2f}s")

# Con threads (NO es más rápido por el GIL!)
inicio = time.time()
t1 = threading.Thread(target=contar, args=(N,))
t2 = threading.Thread(target=contar, args=(N,))
t1.start()
t2.start()
t1.join()
t2.join()
print(f"Threads: {time.time() - inicio:.2f}s")
```

Resultado sorprendente: ¡los threads tardan lo mismo o más que la versión secuencial!

### ¿Cuándo sirven los threads entonces?

Los threads en Python sí son útiles para tareas **I/O-bound**:

```python
import threading
import time
import urllib.request

def descargar(url):
    """Tarea I/O-bound."""
    print(f"Descargando {url}...")
    response = urllib.request.urlopen(url)
    data = response.read()
    print(f"Descargado {url}: {len(data)} bytes")

urls = [
    "https://www.python.org",
    "https://docs.python.org",
    "https://pypi.org",
]

# Secuencial
inicio = time.time()
for url in urls:
    descargar(url)
print(f"Secuencial: {time.time() - inicio:.2f}s\n")

# Con threads (SÍ es más rápido!)
inicio = time.time()
threads = []
for url in urls:
    t = threading.Thread(target=descargar, args=(url,))
    t.start()
    threads.append(t)

for t in threads:
    t.join()
print(f"Threads: {time.time() - inicio:.2f}s")
```

El GIL se libera durante operaciones de I/O, permitiendo que otros threads ejecuten.

### Resumen del GIL

| Tipo de tarea | ¿Threads ayudan? | Alternativa |
|---------------|------------------|-------------|
| I/O-bound (red, disco) | Sí | asyncio |
| CPU-bound (cálculos) | No (con GIL) | multiprocessing |
| Mixta | Depende | Evaluar caso por caso |

### Casos de uso típicos

Sirve threads para:
- Descargar múltiples archivos de internet
- Leer/escribir múltiples archivos en paralelo
- Servidores que esperan conexiones
- Interfaces de usuario que no deben bloquearse

No sirve threads para:
- Comprimir/descomprimir archivos (CPU-bound)
- Procesamiento de imágenes (CPU-bound)
- Cálculos numéricos pesados (CPU-bound)

### Novedad importante: el GIL ya es opcional (Python 3.13+)

Lo que vimos hasta acá describe el comportamiento **tradicional** de CPython. Pero el panorama cambió en los últimos años, y es importante que lo conozcan porque está reconfigurando cómo se piensa la concurrencia en Python.

**Línea de tiempo:**

- **2023 (julio)**: el Steering Council de Python acepta la [PEP 703 — Making the Global Interpreter Lock Optional in CPython](https://peps.python.org/pep-0703/). La propuesta plantea que se pueda compilar Python sin GIL.
- **Python 3.13 (octubre 2024)**: aparece el **build experimental "free-threaded"** (también llamado "no-GIL" o `nogil`). Es un binario alternativo que se baja aparte; el default sigue siendo el clásico con GIL.
- **Python 3.14 (octubre 2025)**: con la [PEP 779](https://peps.python.org/pep-0779/), el free-threaded build deja de ser "experimental" y pasa a "soportado". Sigue siendo opcional (no es el default), pero el camino está trazado.
- **Futuro**: Phase III del plan es que el free-threaded build sea el default y, eventualmente, el único.

**¿Qué cambia en la práctica?**

Si compilás Python con `--disable-gil` o usás el binario free-threaded, los threads **sí escalan en CPU-bound**:

```python
# En free-threaded Python (3.13+ con --disable-gil)
# Esto AHORA aprovecha múltiples cores
t1 = threading.Thread(target=contar, args=(N,))
t2 = threading.Thread(target=contar, args=(N,))
# en una máquina con 4+ cores, esto puede ser ~2x más rápido
```

**El costo del free-threaded**:
- Hay una **penalización de ~5-10%** en código single-threaded (porque hay que reemplazar el GIL con locks más finos en cada objeto)
- Algunas extensiones C (numpy viejo, librerías de C) **pueden no funcionar** o necesitar adaptación
- El reference counting se hizo atómico y más complejo

**¿Esto significa que ya no importa el GIL?**

No tan rápido. En 2026:
- El binario default todavía es **con GIL**
- La mayoría de usuarios y librerías siguen usando el binario tradicional
- Los problemas que aprendiste sobre el GIL **siguen aplicando** al Python que la mayoría usa
- Pero ya no es "una limitación inevitable de Python", sino "una limitación del build default"

**Para esta materia**, asumimos el comportamiento clásico con GIL: threads para I/O-bound, multiprocessing para CPU-bound. Pero es importante que sepan que esto está cambiando, porque en los próximos años el panorama de concurrencia en Python va a verse muy distinto.

Si querés probar el free-threaded:
```bash
# Verificar si tu Python tiene GIL
python -c "import sys; print('GIL activo' if sys._is_gil_enabled() else 'sin GIL')"

# Bajar el build free-threaded oficial:
# Linux/Mac: python.org → versión "freethreaded"
# O compilar: ./configure --disable-gil
```

---

## Problemas de concurrencia

### Race conditions

Cuando dos threads acceden a la misma variable sin sincronización:

```python
import threading

contador = 0

def incrementar():
    global contador
    for _ in range(1_000_000):
        contador += 1  # ¡NO es atómico!

t1 = threading.Thread(target=incrementar)
t2 = threading.Thread(target=incrementar)

t1.start()
t2.start()
t1.join()
t2.join()

print(f"Esperado: 2,000,000")
print(f"Obtenido: {contador}")  # ¡Probablemente menos!
```

¿Por qué pasa esto? `contador += 1` no es atómico — internamente es:
1. Leer contador
2. Sumar 1
3. Escribir contador

Si dos threads hacen esto simultáneamente, pueden perderse incrementos.

### Deadlocks (avance)

Cuando dos threads esperan recursos que el otro tiene, se cuelgan mutuamente. Este es un problema que veremos en detalle en las clases 10 y 11. Por ahora basta con saber que existe:

```python
import threading
import time

lock_a = threading.Lock()
lock_b = threading.Lock()

def thread_1():
    with lock_a:
        time.sleep(0.1)
        with lock_b:  # ¡Deadlock si thread_2 ya tomó lock_b!
            pass

def thread_2():
    with lock_b:
        time.sleep(0.1)
        with lock_a:  # ¡Deadlock si thread_1 ya tomó lock_a!
            pass
```

La solución (adquirir locks siempre en el mismo orden) y otros problemas clásicos los veremos en la clase 11.

---

## Sincronización básica: Lock

Las race conditions se previenen con **primitivas de sincronización**. El módulo `threading` ofrece varias (`Lock`, `RLock`, `Condition`, `Event`, `Semaphore`, `Barrier`). Las vamos a estudiar en profundidad en las clases 10 y 11.

Para esta clase nos basta con la más simple: **`Lock`**. Sirve para garantizar que solo un thread por vez ejecute una sección de código crítica.

```python
import threading

contador = 0
lock = threading.Lock()

def incrementar_seguro():
    global contador
    for _ in range(1_000_000):
        with lock:               # solo un thread entra acá a la vez
            contador += 1        # operación protegida

t1 = threading.Thread(target=incrementar_seguro)
t2 = threading.Thread(target=incrementar_seguro)

t1.start()
t2.start()
t1.join()
t2.join()

print(f"Esperado: 2,000,000")
print(f"Obtenido: {contador}")   # ahora sí, exactamente 2,000,000
```

El `with lock:` adquiere el lock al entrar y lo libera al salir (incluso si hay una excepción). Esa es la forma idiomática en Python.

> Las demás primitivas (`RLock`, `Condition`, `Event`, `Semaphore`, `Barrier`) y los patrones clásicos (productor-consumidor, lectores-escritores, filósofos) los vemos formalmente en las **clases 10 y 11**.

---

## Variables locales por hilo: `threading.local()`

Permite que cada hilo tenga su **propia copia** de una variable, sin necesidad de locks ni de pasarla como argumento.

```python
import threading

datos_locales = threading.local()

def procesar(nombre, valor):
    datos_locales.nombre = nombre
    datos_locales.valor = valor
    import time; time.sleep(0.1)
    # Cada hilo lee SU propia copia
    print(f"Hilo {threading.current_thread().name}: {datos_locales.nombre} = {datos_locales.valor}")

hilos = [
    threading.Thread(target=procesar, args=(f"var_{i}", i * 10), name=f"Worker-{i}")
    for i in range(5)
]
for h in hilos: h.start()
for h in hilos: h.join()
```

Casos de uso típicos:
- Conexiones a base de datos (cada hilo necesita su propia conexión)
- Contexto de request en servidores web (cada hilo atiende un request diferente)
- Identificadores de sesión por hilo
- Buffers locales que no deben mezclarse

---

## Queue: comunicación entre threads

`queue.Queue` es thread-safe y la forma recomendada de comunicar threads. Evita la mayor parte de los bugs de sincronización porque encapsula los locks por vos.

```python
import threading
import queue
import time
import random

def productor(q, id):
    for i in range(5):
        item = f"item-{id}-{i}"
        q.put(item)
        print(f"[Productor {id}] Produjo: {item}")
        time.sleep(random.uniform(0.1, 0.3))
    q.put(None)  # Señal de fin

def consumidor(q, num_productores):
    fins_recibidos = 0
    while fins_recibidos < num_productores:
        item = q.get()
        if item is None:
            fins_recibidos += 1
            print(f"[Consumidor] Fin de productor recibido ({fins_recibidos}/{num_productores})")
        else:
            print(f"[Consumidor] Consumió: {item}")
            time.sleep(random.uniform(0.05, 0.1))
        q.task_done()

q = queue.Queue()
num_productores = 3

# Crear productores
threads = []
for i in range(num_productores):
    t = threading.Thread(target=productor, args=(q, i))
    t.start()
    threads.append(t)

# Crear consumidor
t = threading.Thread(target=consumidor, args=(q, num_productores))
t.start()
threads.append(t)

for t in threads:
    t.join()

print("Todos terminaron")
```

### Tipos de Queue

```python
import queue

# FIFO (First In, First Out) - por defecto
q = queue.Queue()

# LIFO (Last In, First Out) - stack
q = queue.LifoQueue()

# Prioridad (menor valor primero)
q = queue.PriorityQueue()
q.put((3, "baja prioridad"))
q.put((1, "alta prioridad"))
q.put((2, "media prioridad"))

while not q.empty():
    print(q.get())  # Sale en orden de prioridad
```

---

## Daemon threads

Un thread daemon se termina automáticamente cuando el programa principal termina, sin importar si terminó su trabajo. Útil para tareas de soporte (logging, monitoreo, heartbeats).

```python
import threading
import time

def daemon_task():
    while True:
        print("Daemon trabajando...")
        time.sleep(1)

def normal_task():
    for i in range(3):
        print(f"Normal: {i}")
        time.sleep(1)

# Thread normal - el programa espera a que termine
t_normal = threading.Thread(target=normal_task)

# Thread daemon - se mata cuando main termina
t_daemon = threading.Thread(target=daemon_task, daemon=True)

t_normal.start()
t_daemon.start()

t_normal.join()
print("Main terminando - daemon será terminado automáticamente")
```

> **Atención**: no usar daemon para tareas críticas (transacciones, escritura a base de datos). Pueden interrumpirse en estado inconsistente.

---

## Debugging de threads

### Listar threads activos

```python
import threading

# Ver todos los hilos activos
for hilo in threading.enumerate():
    print(f"  {hilo.name} | daemon={hilo.daemon} | alive={hilo.is_alive()}")
```

### Stack trace de todos los threads (detectar deadlocks)

```python
import sys
import traceback

for hilo_id, frame in sys._current_frames().items():
    print(f"\nHilo ID: {hilo_id}")
    traceback.print_stack(frame)
```

Es muy útil cuando un programa se cuelga: te muestra exactamente en qué línea está bloqueado cada thread.

### `faulthandler` para crashes

```python
import faulthandler
faulthandler.enable()

# Si el programa crashea (o se cuelga y le mandás SIGABRT),
# faulthandler te dumpea el stack de todos los threads.
```

---

## Conceptos clave

1. **Threads comparten memoria** — comunicación fácil pero riesgosa
2. **El GIL limita threads para CPU-bound** — usá `multiprocessing` para cálculos intensivos
3. **Threads son útiles para I/O-bound** — red, disco, bases de datos
4. **Race conditions son reales** — `Lock` es la forma más simple de prevenirlas
5. **`Queue` es thread-safe** — preferilo para comunicación entre threads
6. **`threading.local()`** sirve para variables privadas por hilo
7. **El GIL ya es opcional** en Python 3.13+ — pero el panorama todavía está en transición

---

## Preparación para la próxima clase

En la **clase 10 (Sincronización I)** vamos a profundizar en los primitivos de sincronización que solo mencionamos acá:

- `RLock` para locks reentrantes
- `Condition` para esperar/notificar condiciones complejas
- `Event` para señalización
- `Semaphore` para acceso concurrente limitado a N
- `Barrier` para sincronización por fases

Y en la **clase 11 (Sincronización II)** vamos a aplicar todo eso a problemas clásicos: productor-consumidor, filósofos comensales, lectores-escritores.

---

## Referencias

- [Documentación oficial threading](https://docs.python.org/3/library/threading.html)
- [Documentación oficial queue](https://docs.python.org/3/library/queue.html)
- [PEP 703 - Making the GIL Optional](https://peps.python.org/pep-0703/)
- [PEP 779 - Supported status for free-threaded Python](https://peps.python.org/pep-0779/)
- [Python 3.14 What's New - free-threading](https://docs.python.org/3/whatsnew/3.14.html)
- [py-free-threading.github.io](https://py-free-threading.github.io/)

---

*Computación II - 2026 - Clase 9*
