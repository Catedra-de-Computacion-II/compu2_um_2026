# Clase 5: Señales - Comunicación Asíncrona entre Procesos

## Introducción: más allá de los pipes

Los pipes que vimos en la clase anterior son excelentes para transferir datos entre procesos, pero tienen una limitación: requieren que ambos procesos cooperen activamente. El escritor escribe, el lector lee. Es comunicación síncrona - ambos tienen que estar prestando atención.

¿Pero qué pasa si necesitás interrumpir un proceso que está ocupado haciendo otra cosa? ¿O notificarle que algo importante sucedió? Para eso existen las **señales** - notificaciones asíncronas que el kernel puede entregar a un proceso en cualquier momento.

Cuando presionás Ctrl+C para detener un programa, estás enviando una señal. Cuando el sistema se queda sin memoria y necesita matar procesos, usa señales. Cuando un proceso hijo termina, el padre recibe una señal. Las señales son el sistema nervioso de Unix.

---

## ¿Qué es una señal?

Una señal es una notificación de software que se envía a un proceso para informarle que ocurrió algún evento. A diferencia de los datos que fluyen por un pipe, las señales son interrupciones - llegan sin aviso y el proceso debe responder.

Pensalo como las notificaciones de tu teléfono. Podés estar haciendo cualquier cosa, y de repente llega una notificación que demanda tu atención. El proceso puede:

1. **Ignorarla** - Algunas señales se pueden ignorar
2. **Usar la acción por defecto** - Cada señal tiene un comportamiento predeterminado
3. **Manejarla con código propio** - Registrar una función que se ejecuta cuando llega la señal

```python
import signal
import time

def mi_manejador(signum, frame):
    """Esta función se ejecuta cuando llega la señal."""
    print(f"\n¡Recibí la señal {signum}!")
    print("Pero voy a seguir ejecutando...")

# Registrar el manejador para SIGINT (Ctrl+C)
signal.signal(signal.SIGINT, mi_manejador)

print("Presioná Ctrl+C para enviar SIGINT")
print("El programa no terminará porque tenemos un manejador")

while True:
    print(".", end="", flush=True)
    time.sleep(1)
```

---

## Señales estándar

Unix define muchas señales, cada una para un propósito específico. Las más importantes:

### Señales de terminación

| Señal | Número | Tecla | Acción default | Descripción |
|-------|--------|-------|----------------|-------------|
| SIGTERM | 15 | - | Terminar | Terminación "amable", capturable |
| SIGKILL | 9 | - | Terminar | Terminación forzosa, NO capturable |
| SIGINT | 2 | Ctrl+C | Terminar | Interrupción desde terminal |
| SIGQUIT | 3 | Ctrl+\ | Terminar + core | Como SIGINT pero con dump |
| SIGHUP | 1 | - | Terminar | Terminal cerrada |

### Señales de control de proceso

| Señal | Número | Tecla | Acción default | Descripción |
|-------|--------|-------|----------------|-------------|
| SIGSTOP | 19 | - | Detener | Pausa el proceso, NO capturable |
| SIGTSTP | 20 | Ctrl+Z | Detener | Pausa desde terminal, capturable |
| SIGCONT | 18 | - | Continuar | Reanuda proceso detenido |

### Señales de eventos

| Señal | Número | Acción default | Descripción |
|-------|--------|----------------|-------------|
| SIGCHLD | 17 | Ignorar | Un hijo cambió de estado |
| SIGALRM | 14 | Terminar | Timer expiró |
| SIGPIPE | 13 | Terminar | Escribir a pipe sin lectores |
| SIGUSR1 | 10 | Terminar | Definida por el usuario |
| SIGUSR2 | 12 | Terminar | Definida por el usuario |

### Señales de errores

| Señal | Número | Acción default | Descripción |
|-------|--------|----------------|-------------|
| SIGSEGV | 11 | Terminar + core | Violación de segmento |
| SIGFPE | 8 | Terminar + core | Error de punto flotante |
| SIGBUS | 7 | Terminar + core | Error de bus |
| SIGABRT | 6 | Terminar + core | Abort (assert fallido) |

```python
import signal

# Ver todas las señales disponibles
for name in dir(signal):
    if name.startswith("SIG") and not name.startswith("SIG_"):
        signum = getattr(signal, name)
        if isinstance(signum, int):
            print(f"{name:12} = {signum}")
```

---

## Enviando señales

### Desde la terminal

```bash
# Enviar SIGTERM (señal 15) al proceso con PID 1234
kill 1234
kill -15 1234
kill -TERM 1234

# Enviar SIGKILL (señal 9) - terminación forzosa
kill -9 1234
kill -KILL 1234

# Enviar señal a todos los procesos de un grupo
kill -TERM -pgid

# Enviar a todos los procesos con cierto nombre
pkill -TERM python
killall -TERM python
```

### Desde Python

```python
import os
import signal

# Enviar señal a un proceso específico
os.kill(pid, signal.SIGTERM)

# Enviar señal a un grupo de procesos
os.killpg(pgid, signal.SIGTERM)

# Enviarse una señal a sí mismo
os.kill(os.getpid(), signal.SIGUSR1)

# También existe signal.raise_signal (Python 3.8+)
signal.raise_signal(signal.SIGUSR1)
```

### Señales entre padre e hijo

```python
import os
import signal
import time

pid = os.fork()

if pid == 0:
    # Hijo
    def manejador(sig, frame):
        print(f"[HIJO] Recibí señal {sig}")

    signal.signal(signal.SIGUSR1, manejador)

    print(f"[HIJO] PID {os.getpid()}, esperando señales...")
    while True:
        signal.pause()  # Esperar hasta recibir una señal

else:
    # Padre
    time.sleep(1)  # Dar tiempo al hijo de configurar su manejador

    print(f"[PADRE] Enviando SIGUSR1 al hijo {pid}")
    os.kill(pid, signal.SIGUSR1)

    time.sleep(1)

    print(f"[PADRE] Enviando SIGTERM al hijo")
    os.kill(pid, signal.SIGTERM)

    os.wait()
    print("[PADRE] Hijo terminado")
```

---

## Manejando señales

### signal.signal()

Para registrar un manejador de señal usamos `signal.signal(signum, handler)`:

```python
import signal

def mi_manejador(signum, frame):
    """
    Función manejador de señal.

    Args:
        signum: número de la señal recibida
        frame: frame del stack donde se interrumpió (para debugging)
    """
    print(f"Recibí señal {signum}")

# Registrar el manejador
signal.signal(signal.SIGTERM, mi_manejador)

# También podemos usar constantes especiales:
signal.signal(signal.SIGUSR1, signal.SIG_IGN)  # Ignorar la señal
signal.signal(signal.SIGUSR2, signal.SIG_DFL)  # Restaurar acción por defecto
```

### Manejadores comunes

#### Ctrl+C amigable

```python
import signal
import sys

def salir_limpiamente(sig, frame):
    print("\nRecibí Ctrl+C, limpiando...")
    # Aquí podés cerrar archivos, conexiones, etc.
    sys.exit(0)

signal.signal(signal.SIGINT, salir_limpiamente)

print("Presioná Ctrl+C para salir limpiamente")
while True:
    pass
```

#### Recargar configuración con SIGHUP

```python
import signal
import time

config = {"valor": "inicial"}

def recargar_config(sig, frame):
    global config
    print("Recargando configuración...")
    # En la vida real, leerías de un archivo
    config["valor"] = f"recargado a las {time.ctime()}"
    print(f"Nueva configuración: {config}")

signal.signal(signal.SIGHUP, recargar_config)

print(f"PID: {os.getpid()}")
print("Enviá 'kill -HUP <pid>' para recargar config")

while True:
    print(f"Config actual: {config['valor']}")
    time.sleep(5)
```

#### Terminar limpiamente con SIGTERM

```python
import signal
import sys
import time

ejecutando = True

def terminar(sig, frame):
    global ejecutando
    print("\nRecibí SIGTERM, terminando limpiamente...")
    ejecutando = False

signal.signal(signal.SIGTERM, terminar)

print(f"PID: {os.getpid()}")
print("Enviá 'kill <pid>' para terminar")

while ejecutando:
    print("Trabajando...")
    time.sleep(1)

print("Limpieza final completada")
sys.exit(0)
```

---

## SIGCHLD: saber cuando terminan los hijos

Cuando un proceso hijo termina (o cambia de estado), el kernel envía SIGCHLD al padre. Esto permite que el padre sepa que debe llamar a wait() sin tener que bloquearse esperando.

```python
import os
import signal
import time

hijos_terminados = []

def manejador_sigchld(sig, frame):
    """Recoge hijos terminados de forma no bloqueante."""
    while True:
        try:
            pid, status = os.waitpid(-1, os.WNOHANG)
            if pid == 0:
                break  # No hay más hijos terminados
            codigo = os.WEXITSTATUS(status) if os.WIFEXITED(status) else -1
            hijos_terminados.append((pid, codigo))
            print(f"[SIGCHLD] Hijo {pid} terminó con código {codigo}")
        except ChildProcessError:
            break  # No hay hijos

signal.signal(signal.SIGCHLD, manejador_sigchld)

# Crear varios hijos que terminan en diferentes momentos
for i in range(3):
    pid = os.fork()
    if pid == 0:
        time.sleep(i + 1)  # Cada hijo duerme diferente tiempo
        print(f"[HIJO {i}] Terminando...")
        os._exit(i)

# El padre hace otras cosas mientras los hijos trabajan
print("[PADRE] Haciendo trabajo...")
for _ in range(5):
    print(f"[PADRE] Hijos terminados hasta ahora: {len(hijos_terminados)}")
    time.sleep(1)

print(f"[PADRE] Resumen final: {hijos_terminados}")
```

---

## Señales y el problema de la reentrancia

Un manejador de señal puede interrumpir tu código en cualquier momento - incluso en medio de una función. Esto crea problemas de reentrancia: ¿qué pasa si la señal llega mientras estás modificando una estructura de datos?

### Funciones async-signal-safe

Solo ciertas funciones son seguras de llamar desde un manejador de señal. En general, evitá:

- `print()` (usa buffers internos)
- `malloc()` / `new` (modifica estructuras globales)
- Operaciones de archivo con buffering
- Logging
- Cualquier cosa que tome locks

```python
import signal
import os

# MAL: print no es async-signal-safe
def manejador_malo(sig, frame):
    print("Esto puede causar problemas!")  # Peligroso

# MEJOR: usar write directo
def manejador_bueno(sig, frame):
    os.write(1, b"Señal recibida\n")  # Más seguro

# MEJOR AÚN: solo setear un flag
señal_recibida = False

def manejador_con_flag(sig, frame):
    global señal_recibida
    señal_recibida = True  # Solo setear flag, procesar después

signal.signal(signal.SIGINT, manejador_con_flag)

while True:
    if señal_recibida:
        print("Procesando señal de forma segura...")
        señal_recibida = False
        break
```

### El patrón self-pipe

Una técnica común es usar un pipe para convertir señales en eventos legibles:

```python
import os
import signal
import select

# Crear pipe para notificaciones de señales
signal_read, signal_write = os.pipe()

# Hacer write non-blocking
import fcntl
flags = fcntl.fcntl(signal_write, fcntl.F_GETFL)
fcntl.fcntl(signal_write, fcntl.F_SETFL, flags | os.O_NONBLOCK)

def manejador(sig, frame):
    # Solo escribir un byte al pipe (async-signal-safe)
    try:
        os.write(signal_write, b"x")
    except BlockingIOError:
        pass  # Pipe lleno, no importa

signal.signal(signal.SIGINT, manejador)
signal.signal(signal.SIGTERM, manejador)

print("Esperando señales o eventos...")
print(f"PID: {os.getpid()}")

while True:
    # select espera en el pipe (y otros fds si los hubiera)
    readable, _, _ = select.select([signal_read], [], [], 1.0)

    if signal_read in readable:
        os.read(signal_read, 1024)  # Consumir los bytes
        print("Señal detectada! Procesando de forma segura...")
        break

    print("Tick...")

print("Terminando limpiamente")
```

---

## Alarmas y temporizadores

SIGALRM permite implementar timeouts:

```python
import signal

class TimeoutError(Exception):
    pass

def timeout_handler(sig, frame):
    raise TimeoutError("Operación excedió el tiempo límite")

def con_timeout(funcion, timeout_segundos, *args, **kwargs):
    """Ejecuta una función con timeout."""
    # Guardar manejador anterior
    old_handler = signal.signal(signal.SIGALRM, timeout_handler)

    # Programar alarma
    signal.alarm(timeout_segundos)

    try:
        resultado = funcion(*args, **kwargs)
    finally:
        # Cancelar alarma y restaurar manejador
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)

    return resultado

# Uso
def operacion_lenta():
    import time
    print("Iniciando operación lenta...")
    time.sleep(10)
    return "completado"

try:
    resultado = con_timeout(operacion_lenta, 3)
    print(f"Resultado: {resultado}")
except TimeoutError as e:
    print(f"Timeout: {e}")
```

### Alarmas periódicas con setitimer

Para alarmas más precisas o repetidas, usá `setitimer`:

```python
import signal
import time

contador = 0

def alarma_periodica(sig, frame):
    global contador
    contador += 1
    print(f"Tick #{contador}")

signal.signal(signal.SIGALRM, alarma_periodica)

# setitimer(ITIMER_REAL, interval, initial)
# Dispara cada 0.5 segundos, empezando en 0.5 segundos
signal.setitimer(signal.ITIMER_REAL, 0.5, 0.5)

print("Alarma configurada cada 0.5 segundos")
print("Presioná Ctrl+C para salir")

try:
    while True:
        time.sleep(0.1)
except KeyboardInterrupt:
    signal.setitimer(signal.ITIMER_REAL, 0)  # Cancelar timer
    print(f"\nTerminando. Total de ticks: {contador}")
```

---

## Señales en programas multi-threaded

Las señales y los threads tienen una relación complicada. En Python, las señales solo se entregan al thread principal.

```python
import signal
import threading
import time

def manejador(sig, frame):
    print(f"Señal recibida en thread {threading.current_thread().name}")

signal.signal(signal.SIGINT, manejador)

def worker():
    while True:
        print(f"Worker {threading.current_thread().name} trabajando")
        time.sleep(1)

# Crear threads
threads = []
for i in range(2):
    t = threading.Thread(target=worker, name=f"Worker-{i}")
    t.daemon = True
    t.start()
    threads.append(t)

print("Threads creados. Ctrl+C para enviar señal.")
print("Observá que la señal llega al thread principal")

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("Saliendo...")
```

### signal.pthread_sigmask

Podés bloquear señales en threads específicos:

```python
import signal
import threading

def thread_sin_signals():
    # Bloquear todas las señales en este thread
    signal.pthread_sigmask(signal.SIG_BLOCK, {signal.SIGINT, signal.SIGTERM})

    while True:
        print("Thread trabajando (señales bloqueadas)")
        time.sleep(1)
```

---

## Patrones comunes

### Servidor que se apaga limpiamente

```python
import signal
import sys
import time

class Servidor:
    def __init__(self):
        self.ejecutando = True
        self.conexiones = []

        # Registrar manejadores
        signal.signal(signal.SIGTERM, self._manejar_shutdown)
        signal.signal(signal.SIGINT, self._manejar_shutdown)
        signal.signal(signal.SIGHUP, self._manejar_reload)

    def _manejar_shutdown(self, sig, frame):
        print(f"\nRecibí {signal.Signals(sig).name}, iniciando shutdown...")
        self.ejecutando = False

    def _manejar_reload(self, sig, frame):
        print("Recargando configuración...")
        # Recargar config aquí

    def cerrar_conexiones(self):
        print(f"Cerrando {len(self.conexiones)} conexiones...")
        # Cerrar conexiones aquí

    def ejecutar(self):
        print(f"Servidor iniciado (PID {os.getpid()})")

        while self.ejecutando:
            print("Procesando...")
            time.sleep(1)

        self.cerrar_conexiones()
        print("Servidor terminado limpiamente")

if __name__ == "__main__":
    servidor = Servidor()
    servidor.ejecutar()
```

### Pool de workers con señales

```python
import os
import signal
import time

workers = []
ejecutando = True

def terminar_workers(sig, frame):
    global ejecutando
    print("\nTerminando workers...")
    ejecutando = False
    for pid in workers:
        os.kill(pid, signal.SIGTERM)

signal.signal(signal.SIGINT, terminar_workers)
signal.signal(signal.SIGTERM, terminar_workers)

# Crear workers
for i in range(3):
    pid = os.fork()
    if pid == 0:
        # Worker
        while True:
            print(f"[Worker {os.getpid()}] trabajando")
            time.sleep(1)
    else:
        workers.append(pid)

# Supervisor
print(f"Supervisor PID: {os.getpid()}")
print(f"Workers: {workers}")

while ejecutando and workers:
    # Recoger workers terminados
    try:
        pid, status = os.waitpid(-1, os.WNOHANG)
        if pid > 0:
            workers.remove(pid)
            print(f"Worker {pid} terminó")
    except ChildProcessError:
        break
    time.sleep(0.5)

# Esperar a todos
for pid in workers:
    os.waitpid(pid, 0)

print("Todos los workers terminados")
```

---

## Conceptos clave

1. **Las señales son asíncronas** - pueden llegar en cualquier momento, interrumpiendo tu código.

2. **SIGKILL y SIGSTOP no se pueden capturar** - siempre hacen su acción por defecto.

3. **SIGTERM es la señal "amable"** - permite que el proceso haga cleanup. `kill` sin argumentos envía SIGTERM.

4. **SIGINT viene de Ctrl+C** - es la forma estándar de interrumpir un programa interactivo.

5. **Los manejadores deben ser rápidos** y usar solo funciones async-signal-safe.

6. **El patrón del flag** es el más seguro: el manejador solo setea un flag, el procesamiento real ocurre en el loop principal.

7. **SIGCHLD notifica cuando los hijos cambian de estado** - útil para evitar zombies sin bloquear.

---

## Preparación para la próxima clase

En la clase 6 veremos **threads** - otra forma de ejecutar código concurrentemente, pero dentro del mismo proceso. A diferencia de fork donde cada proceso tiene su propia memoria, los threads comparten memoria, lo que trae ventajas de comunicación pero también desafíos de sincronización.

---

*Computación II - 2026 - Clase 5*
