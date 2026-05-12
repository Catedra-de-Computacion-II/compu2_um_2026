# Clase 7: Multiprocessing - Fundamentos

## Introducción

En las clases anteriores vimos cómo crear procesos a bajo nivel con `fork()`, comunicarlos con pipes y señales, y compartir memoria con mmap. Todo eso son las herramientas del sistema operativo expuestas casi tal cual.

Python provee una abstracción de más alto nivel: el módulo **`multiprocessing`**. Te da una API uniforme y portable para crear procesos, sin tener que pelearte con `fork()`, `wait()`, `os._exit()`, etc. Funciona igual en Linux, macOS y Windows (aunque por debajo usen mecanismos distintos).

Esta clase es la introducción al módulo. La clase 8 va a profundizar en sus herramientas avanzadas (`Pool`, `Manager`, patrones).

---

## ¿Por qué multiprocessing?

### Limitaciones del `fork()` puro

Trabajar con `os.fork()` tiene problemas:

- **No es portable**: Windows no tiene `fork()`
- **Manejo manual**: tenés que `wait()`, manejar zombies, IPC a mano
- **Patrones repetitivos**: cada vez que querés un worker, repetís el mismo código
- **Errores comunes**: olvidarse de `os._exit()` en el hijo es un bug clásico

### Lo que aporta multiprocessing

- API uniforme entre plataformas (Linux/Mac/Windows)
- Abstracciones como `Process`, `Queue`, `Pool`
- Sincronización integrada (`Lock`, `Semaphore`, `Event`)
- Memoria compartida como objetos Python (`Value`, `Array`)
- Manejo automático de zombies

Pero ojo: por debajo, en Linux, sigue usando `fork()`. Entender lo que vimos en clases anteriores te da una intuición de **qué hace** y **por qué a veces se rompe**.

---

## `Process`: el bloque básico

### Creación con función target

```python
import multiprocessing
import os
import time

def tarea(nombre):
    print(f"[{nombre}] PID={os.getpid()}, parent={os.getppid()}")
    time.sleep(2)
    print(f"[{nombre}] termino")

if __name__ == "__main__":
    p = multiprocessing.Process(target=tarea, args=("Worker",))
    p.start()         # arranca el proceso
    p.join()          # espera a que termine
    print(f"[Main] PID={os.getpid()}, hijo terminó con exitcode={p.exitcode}")
```

### Por qué el `if __name__ == "__main__":`

En Windows y macOS (con el método `spawn`), el proceso hijo **re-importa el módulo**. Sin el guard, importaría tu script y crearía procesos infinitamente.

En Linux con `fork()` no hace falta, pero como buena práctica siempre se incluye.

### `Process` como clase

```python
import multiprocessing
import time

class MiWorker(multiprocessing.Process):
    def __init__(self, nombre, duracion):
        super().__init__()
        self.nombre = nombre
        self.duracion = duracion

    def run(self):
        """Se ejecuta automáticamente al llamar start()"""
        print(f"[{self.nombre}] arranco")
        time.sleep(self.duracion)
        print(f"[{self.nombre}] termino")

if __name__ == "__main__":
    w = MiWorker("Worker-1", 2)
    w.start()
    w.join()
```

---

## Métodos y atributos importantes

```python
p = multiprocessing.Process(target=tarea, name="MiProceso", daemon=False)

p.start()           # Inicia el proceso (llamar una sola vez)
p.join()            # Espera a que termine
p.join(timeout=5)   # Espera máximo 5 segundos
p.is_alive()        # True si está corriendo
p.terminate()       # Manda SIGTERM
p.kill()            # Manda SIGKILL (no se puede ignorar)

p.pid               # PID del proceso (después de start)
p.name              # Nombre
p.exitcode          # Código de salida (None si sigue corriendo)
p.daemon            # True si es daemon
```

---

## Múltiples procesos

```python
import multiprocessing
import time
import random

def worker(id):
    print(f"[Worker-{id}] arranca")
    time.sleep(random.uniform(0.5, 2))
    print(f"[Worker-{id}] termina")

if __name__ == "__main__":
    procesos = []
    for i in range(5):
        p = multiprocessing.Process(target=worker, args=(i,))
        p.start()
        procesos.append(p)

    for p in procesos:
        p.join()

    print("[Main] todos terminaron")
```

---

## fork vs spawn vs forkserver

`multiprocessing` puede arrancar procesos de tres formas distintas. Para entenderlas, primero hay que aclarar algo importante: **`fork()` no existe en Windows**.

### ¿Qué usa Windows si no tiene fork?

Windows usa una syscall llamada **`CreateProcess()`**, con una filosofía completamente distinta:

| | `fork()` (Linux/Mac) | `CreateProcess()` (Windows) |
|-|-|-|
| Modelo | "Cloname y después decidí qué hacer" | "Arrancame este ejecutable desde cero" |
| Argumentos | Ninguno (copia todo del padre) | Path al ejecutable + argumentos |
| Memoria | Hereda del padre (copy-on-write) | Espacio completamente nuevo |
| File descriptors | Hereda todos | Solo los que vos elijas explícitamente |
| Velocidad | Muy rápido | Lento (carga ejecutable, inicializa todo) |
| Estado inicial | "Vivo" en el medio de tu programa | "Vivo" desde el `main()` del ejecutable |

Por eso `os.fork()` directamente no funciona en Windows: el modelo del sistema operativo es otro. `multiprocessing` resuelve esto ofreciendo tres "métodos de arranque":

### 1. `fork` (default en Linux)

Es lo que vimos en la clase 3. El padre se duplica y el hijo continúa en otro punto.

- Ventaja: Muy rápido (copy-on-write)
- Ventaja: El hijo hereda todo el estado del padre (variables, módulos importados, conexiones...)
- Desventaja: No funciona en Windows
- Desventaja: Heredar todo el estado puede ser **peligroso**: locks tomados, threads del padre que el hijo "ve" pero no existen, conexiones a base de datos compartidas, etc.

### 2. `spawn` (default en Windows y macOS)

A bajo nivel, `spawn` hace algo muy parecido a lo que hace Windows con `CreateProcess`, pero implementado de forma portable. Los pasos son:

1. El padre arranca un **nuevo intérprete de Python** desde cero (`python -c ...`)
2. Ese nuevo Python re-importa el módulo donde está tu código (por eso necesitás `if __name__ == "__main__":`)
3. El padre le **manda por pipe** (serializados con pickle) la función a ejecutar y sus argumentos
4. El hijo des-serializa y ejecuta

- Ventaja: Funciona igual en todas las plataformas
- Ventaja: Estado limpio (no hay sorpresas heredadas)
- Desventaja: Lento: arrancar un intérprete + re-importar todo cuesta mucho más que un fork
- Desventaja: Solo se pueden pasar objetos **picklables** (lambdas, closures, file handles abiertos: no)

### 3. `forkserver` (solo Linux/Mac, opcional)

Es un híbrido pensado para resolver los problemas del fork puro sin pagar el costo del spawn. Funciona así:

1. La **primera vez** que pedís un proceso, Python lanza un proceso aparte llamado **fork server**. Este server queda corriendo en background, esperando pedidos.
2. Cuando necesitás un proceso hijo, le pedís al fork server que haga **`fork()`** desde sí mismo (no desde tu programa principal).
3. El fork server es un proceso **limpio**: no tiene tus threads, ni tus conexiones, ni tu estado raro. Solo el intérprete Python básico.
4. El hijo "fork-eado" tiene un estado mínimo. Después carga lo que necesite.

- Ventaja: Más rápido que `spawn` (usa fork por debajo)
- Ventaja: Más seguro que `fork` puro (el server no tiene estado problemático)
- Ventaja: Ideal para programas multi-threaded que necesitan crear procesos (problema clásico: `fork after threads` puede deadlockear si un thread tiene un lock tomado al momento del fork)
- Desventaja: Más lento que `fork` directo
- Desventaja: La primera vez que arranca, hay overhead de levantar el server

```python
import multiprocessing

# Cambiar el método (al inicio del programa, antes del primer Process)
multiprocessing.set_start_method('spawn')

# O usar un contexto específico sin cambiar el global
ctx = multiprocessing.get_context('forkserver')
p = ctx.Process(target=tarea)
```

### Tabla resumen

| Método | Plataforma | Velocidad | Hereda estado | Cuándo usarlo |
|--------|-----------|-----------|---------------|---------------|
| `fork` | Linux/Mac | Alta | Sí (todo) | Programa simple, sin threads, sin conexiones raras |
| `spawn` | Todas (default Win/Mac) | Baja | No | Programas con estado complejo o portables |
| `forkserver` | Linux/Mac | Media | No | Programas multi-threaded que también crean procesos |

---

## Daemon processes

Igual que con threads, podés marcar un proceso como `daemon`. Muere automáticamente cuando el padre termina.

```python
p = multiprocessing.Process(target=tarea, daemon=True)
```

### ¿Qué pasa a bajo nivel?

Atención con el nombre: en `multiprocessing` (y `threading`), "daemon" **NO** significa lo mismo que un "daemon process" clásico de Unix (como `sshd`, `cron`, `nginx`). Son dos conceptos distintos que comparten nombre.

**Un daemon clásico de Unix** es un proceso que se desliga totalmente de la terminal:
1. Hace `fork()` y el padre sale → el hijo queda huérfano y `init`/`systemd` lo adopta
2. Llama a `setsid()` para crear una nueva sesión y desligarse del terminal controlador
3. Suele hacer un segundo `fork()` para no ser líder de sesión
4. Cierra `stdin`/`stdout`/`stderr` (los redirige a `/dev/null` o a un archivo de log)
5. Cambia el directorio de trabajo a `/`
6. Llama a `umask(0)` para tener control total de permisos

Después puede vivir indefinidamente, sin importar quién lo arrancó.

**Un daemon de `multiprocessing`** no hace nada de eso. Lo único que hace es:

1. Cuando el proceso padre se va a terminar, Python ejecuta un *cleanup handler* (registrado con el módulo `atexit`)
2. Ese handler recorre la lista de hijos marcados como `daemon=True` y les manda **`SIGTERM`**
3. Si no terminan en unos segundos, los mata con **`SIGKILL`**

O sea: el "daemon" de Python es más bien un "**hijo desechable**" — uno que no merece esperar. Sirve para tareas auxiliares (monitoreo, heartbeats, logging) que no son críticas y deben morir con el programa principal.

### Restricciones

```python
p = multiprocessing.Process(target=tarea, daemon=True)
p.start()

# Dentro de tarea(), esto NO funciona:
hijo_del_daemon = multiprocessing.Process(target=otra_cosa)
hijo_del_daemon.start()   # AssertionError: daemonic processes are not allowed to have children
```

Esta restricción existe porque, si un daemon pudiera tener hijos, esos nietos quedarían huérfanos sin que nadie los limpie cuando el daemon muere abruptamente. Para evitar el desorden, Python lo prohíbe.

### Casos de uso típicos

**Sirve para:**
- Monitor que reporta uso de CPU/memoria cada N segundos
- Worker de logging en background
- Heartbeat a un servicio externo

**No usar para:**
- Operaciones críticas (transacciones, escritura a base de datos): podrían interrumpirse en medio
- Cualquier proceso que necesite ejecutar sus propios hijos

---

## Pasar datos al proceso

### Por argumentos (al crearlo)

```python
def worker(datos):
    print(f"Recibí: {datos}")

p = multiprocessing.Process(target=worker, args=({"key": "value"},))
```

Los datos se **serializan con pickle** y se pasan al hijo. Es una **copia**, no una referencia: si el hijo modifica los datos, el padre no se entera.

### Variables globales (con fork)

Si usás `fork` en Linux, el hijo ve las variables globales que el padre tenía al momento del fork. **Pero son copias** (copy-on-write).

```python
config = {"modo": "produccion"}

def worker():
    print(f"Hijo ve config: {config}")
    config["modo"] = "test"   # solo afecta al hijo

if __name__ == "__main__":
    p = multiprocessing.Process(target=worker)
    p.start(); p.join()
    print(f"Padre ve config: {config}")  # original, sin cambios
```

---

## Comunicación básica: Queue

`multiprocessing.Queue` es como `queue.Queue` pero entre procesos. Funciona como un pipe en el fondo, pero la API es mucho más linda.

```python
import multiprocessing
import time

def productor(q):
    for i in range(5):
        q.put(f"item-{i}")
        time.sleep(0.1)
    q.put(None)  # señal de fin

def consumidor(q):
    while True:
        item = q.get()
        if item is None:
            break
        print(f"Consumió: {item}")

if __name__ == "__main__":
    q = multiprocessing.Queue()

    p1 = multiprocessing.Process(target=productor, args=(q,))
    p2 = multiprocessing.Process(target=consumidor, args=(q,))

    p1.start(); p2.start()
    p1.join(); p2.join()
```

> Los objetos que pasés por la Queue se serializan con pickle. Tienen que ser picklables (lambdas y closures no funcionan).

---

## Comunicación básica: Pipe

`multiprocessing.Pipe()` devuelve **dos extremos conectados**. Cada extremo puede enviar y recibir.

```python
import multiprocessing

def hijo(conn):
    conn.send("Hola padre")
    print(f"Hijo recibió: {conn.recv()}")
    conn.close()

if __name__ == "__main__":
    padre_conn, hijo_conn = multiprocessing.Pipe()

    p = multiprocessing.Process(target=hijo, args=(hijo_conn,))
    p.start()

    print(f"Padre recibió: {padre_conn.recv()}")
    padre_conn.send("Hola hijo")
    p.join()
```

A diferencia del pipe a bajo nivel (clase 4), `Pipe()` de multiprocessing es **bidireccional por defecto**.

---

## Conceptos clave

1. **`multiprocessing` envuelve `fork`** pero con API portable y de alto nivel
2. **El guard `if __name__ == "__main__":`** es obligatorio si el módulo puede ejecutarse con `spawn`
3. **Los datos se copian entre procesos** (vía pickle) — no comparten memoria por defecto
4. **`Queue` y `Pipe`** son las formas básicas de comunicación
5. **`fork` vs `spawn` vs `forkserver`** afectan velocidad y semántica

---

## Preparación para la próxima clase

En la **clase 8 (Multiprocessing Avanzado)** vamos a ver las herramientas potentes:

- `Pool` y `ProcessPoolExecutor` para paralelizar tareas masivamente
- `Manager` para compartir objetos Python complejos (dict, list)
- `Value` y `Array` para compartir memoria de forma segura
- Sincronización entre procesos (Lock, Semaphore, Event)
- Patrones: Map-Reduce, pipeline de procesos

---

*Computación II - 2026 - Clase 7*
