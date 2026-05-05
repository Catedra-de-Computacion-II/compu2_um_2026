# Clase 5: Señales - Extra Manijas

Material opcional para profundizar.

---

## Señales en el kernel

### Cómo funciona la entrega de señales

Cuando enviás una señal a un proceso, el kernel:

1. **Marca la señal como pendiente** en el `task_struct` del proceso
2. **Despierta al proceso** si está bloqueado (sleeping)
3. **Cuando el proceso vuelve a ejecutar**, antes de retornar a userspace, el kernel revisa señales pendientes
4. **Ejecuta el manejador** o la acción por defecto

```
Proceso A                    Kernel                      Proceso B
    │                           │                            │
    │  kill(B, SIGTERM)         │                            │
    │ ─────────────────────────>│                            │
    │                           │  Marcar señal pendiente    │
    │                           │ ──────────────────────────>│
    │                           │                            │ (sleeping)
    │                           │  Despertar proceso         │
    │                           │ ──────────────────────────>│
    │                           │                            │
    │                           │<──────────────────────────│
    │                           │  Proceso ejecuta handler   │
    │                           │ ──────────────────────────>│
```

### Señales pendientes vs bloqueadas

- **Señal pendiente:** La señal fue enviada pero aún no entregada
- **Señal bloqueada:** El proceso indicó que no quiere recibirla (temporalmente)

Una señal bloqueada queda pendiente hasta que se desbloquea.

```python
import signal
import os

# Bloquear SIGUSR1
signal.pthread_sigmask(signal.SIG_BLOCK, [signal.SIGUSR1])

# Enviar señal (quedará pendiente)
os.kill(os.getpid(), signal.SIGUSR1)

# Ver señales pendientes
pendientes = signal.sigpending()
print(f"Señales pendientes: {pendientes}")  # {Signals.SIGUSR1}

# Desbloquear - la señal se entrega
signal.pthread_sigmask(signal.SIG_UNBLOCK, [signal.SIGUSR1])
```

### Señales en tiempo real

Además de las señales estándar, Linux soporta señales de tiempo real (SIGRTMIN a SIGRTMAX):

- **Se pueden encolar:** Múltiples instancias de la misma señal se entregan todas
- **Llevan datos:** Pueden incluir un valor entero o puntero
- **Orden garantizado:** Se entregan en orden FIFO

```python
import signal
import os

# Señales de tiempo real
SIGRT_1 = signal.SIGRTMIN
SIGRT_2 = signal.SIGRTMIN + 1

def handler(sig, frame):
    print(f"Recibí señal de tiempo real: {sig}")

signal.signal(SIGRT_1, handler)

# Enviar con sigqueue (no disponible directamente en Python stdlib)
# Requiere ctypes o extensión C
```

---

## sigaction: control avanzado

La syscall `sigaction` ofrece más control que `signal`:

```c
struct sigaction {
    void (*sa_handler)(int);           // Manejador simple
    void (*sa_sigaction)(int, siginfo_t *, void *);  // Manejador con info
    sigset_t sa_mask;                  // Señales a bloquear durante el handler
    int sa_flags;                      // Flags de comportamiento
};
```

### Flags importantes

- **SA_RESTART:** Reiniciar syscalls interrumpidas automáticamente
- **SA_SIGINFO:** Usar sa_sigaction en lugar de sa_handler
- **SA_NOCLDSTOP:** No recibir SIGCHLD cuando hijo se detiene
- **SA_NOCLDWAIT:** No crear zombies

Python expone esto parcialmente:

```python
import signal

# SA_RESTART está habilitado por defecto en Python
# Para deshabilitarlo:
old_handler = signal.signal(signal.SIGINT, signal.SIG_DFL)
# signal.siginterrupt(signal.SIGINT, True)  # Permitir interrupción

# Para SIGCHLD sin zombies (Python 3.9+)
signal.signal(signal.SIGCHLD, signal.SIG_IGN)  # Automáticamente evita zombies
```

---

## Manejo seguro de señales

### El problema de la reentrancia

```python
import signal

lista_global = []

def handler_peligroso(sig, frame):
    # PELIGRO: modificar estructura de datos global
    lista_global.append("señal")
    print(f"Lista: {lista_global}")  # print tampoco es safe

# Si la señal llega mientras estamos modificando lista_global,
# podemos corromper la estructura de datos
```

### Funciones async-signal-safe

POSIX define una lista de funciones seguras de llamar desde handlers:

```
_Exit, _exit, abort, accept, access, aio_error, aio_return, aio_suspend,
alarm, bind, cfgetispeed, cfgetospeed, cfsetispeed, cfsetospeed, chdir,
chmod, chown, clock_gettime, close, connect, creat, dup, dup2, execle,
execve, fchmod, fchown, fcntl, fdatasync, fork, fstat, fsync, ftruncate,
getegid, geteuid, getgid, getgroups, getpeername, getpgrp, getpid,
getppid, getsockname, getsockopt, getuid, kill, link, listen, lseek,
lstat, mkdir, mkfifo, open, pause, pipe, poll, posix_trace_event, pselect,
raise, read, readlink, recv, recvfrom, recvmsg, rename, rmdir, select,
sem_post, send, sendmsg, sendto, setgid, setpgid, setsid, setsockopt,
setuid, shutdown, sigaction, sigaddset, sigdelset, sigemptyset,
sigfillset, sigismember, signal, sigpause, sigpending, sigprocmask,
sigqueue, sigset, sigsuspend, sleep, socket, socketpair, stat, symlink,
sysconf, tcdrain, tcflow, tcflush, tcgetattr, tcgetpgrp, tcsendbreak,
tcsetattr, tcsetpgrp, time, timer_getoverrun, timer_gettime,
timer_settime, times, umask, uname, unlink, utime, wait, waitpid, write
```

### El patrón self-pipe en detalle

```python
import os
import signal
import select
import fcntl
import errno

class SignalHandler:
    """Manejador de señales seguro usando self-pipe."""

    def __init__(self):
        # Crear pipe para notificaciones
        self.read_fd, self.write_fd = os.pipe()

        # Hacer non-blocking
        for fd in (self.read_fd, self.write_fd):
            flags = fcntl.fcntl(fd, fcntl.F_GETFL)
            fcntl.fcntl(fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)

        # Cerrar en exec
        fcntl.fcntl(self.read_fd, fcntl.F_SETFD, fcntl.FD_CLOEXEC)
        fcntl.fcntl(self.write_fd, fcntl.F_SETFD, fcntl.FD_CLOEXEC)

        self.signal_queue = []

    def _raw_handler(self, sig, frame):
        """Handler que solo escribe al pipe."""
        # Guardar señal en queue (atómico para enteros)
        self.signal_queue.append(sig)

        # Notificar via pipe
        try:
            os.write(self.write_fd, b'\x00')
        except (BlockingIOError, InterruptedError):
            pass

    def register(self, signum):
        """Registrar una señal para manejar."""
        signal.signal(signum, self._raw_handler)

    def wait(self, timeout=None):
        """Esperar señales de forma segura."""
        readable, _, _ = select.select([self.read_fd], [], [], timeout)

        if self.read_fd in readable:
            # Drenar el pipe
            try:
                while os.read(self.read_fd, 1024):
                    pass
            except BlockingIOError:
                pass

        # Retornar señales pendientes
        signals = self.signal_queue[:]
        self.signal_queue.clear()
        return signals

# Uso
handler = SignalHandler()
handler.register(signal.SIGINT)
handler.register(signal.SIGTERM)

print("Esperando señales...")
while True:
    signals = handler.wait(timeout=1.0)
    if signals:
        for sig in signals:
            print(f"Procesando señal {sig} de forma segura")
            if sig in (signal.SIGINT, signal.SIGTERM):
                print("Saliendo...")
                exit(0)
    print("tick")
```

---

## signalfd: señales como file descriptors

Linux permite recibir señales como eventos de archivo con `signalfd`:

```python
import os
import signal
import struct
import select

# Bloquear las señales que queremos manejar via signalfd
mask = {signal.SIGINT, signal.SIGTERM, signal.SIGUSR1}
signal.pthread_sigmask(signal.SIG_BLOCK, mask)

# Crear signalfd (requiere ctypes en Python)
import ctypes

# Constantes
SFD_NONBLOCK = 0o4000
SFD_CLOEXEC = 0o2000000

libc = ctypes.CDLL("libc.so.6", use_errno=True)

# sigset_t es complejo, simplificamos con SIGUSR1
# En producción usarías una estructura sigset_t apropiada

# Crear signalfd
# sfd = libc.signalfd(-1, sigset, flags)

# Alternativa más simple: usar pselect o sigwait
sigset = {signal.SIGINT, signal.SIGTERM}
signal.pthread_sigmask(signal.SIG_BLOCK, sigset)

print("Esperando señales con sigwait...")
while True:
    sig = signal.sigwait(sigset)
    print(f"Recibí señal: {sig}")
    if sig == signal.SIGTERM:
        break
```

---

## Señales y threads en detalle

### Modelo de señales POSIX

En un proceso multi-threaded:
- Las señales dirigidas al proceso pueden entregarse a cualquier thread que no la tenga bloqueada
- Las señales dirigidas a un thread específico se entregan a ese thread
- Cada thread tiene su propia máscara de señales bloqueadas
- Los manejadores son compartidos por todos los threads

```python
import signal
import threading
import os
import time

def thread_worker(thread_id):
    # Bloquear SIGINT en este thread
    signal.pthread_sigmask(signal.SIG_BLOCK, [signal.SIGINT])

    print(f"Thread {thread_id}: SIGINT bloqueado")
    for i in range(10):
        print(f"Thread {thread_id}: trabajando {i}")
        time.sleep(0.5)

def main_thread_handler(sig, frame):
    print(f"\n[MAIN] Recibí SIGINT")

signal.signal(signal.SIGINT, main_thread_handler)

# Crear threads que bloquean SIGINT
threads = []
for i in range(2):
    t = threading.Thread(target=thread_worker, args=(i,))
    t.start()
    threads.append(t)

print("[MAIN] Presioná Ctrl+C - solo el main thread la recibirá")

for t in threads:
    t.join()
```

### pthread_kill

Podés enviar señales a threads específicos:

```python
import signal
import threading
import ctypes
import time

libc = ctypes.CDLL("libc.so.6")

def thread_handler(sig, frame):
    print(f"Thread {threading.current_thread().name} recibió señal {sig}")

signal.signal(signal.SIGUSR1, thread_handler)

def worker():
    print(f"Worker {threading.current_thread().name} iniciado")
    time.sleep(5)
    print(f"Worker terminado")

t = threading.Thread(target=worker, name="MiWorker")
t.start()

time.sleep(1)

# Enviar señal al thread específico
# pthread_kill(pthread_t thread, int sig)
# Necesitamos el pthread_t del thread, que es complejo de obtener en Python

# Alternativa: usar threading.main_thread()._ident
# Pero esto es implementation-specific

t.join()
```

---

## Señales y procesos daemon

### Double fork para daemons

```python
import os
import sys
import signal

def daemonize():
    """Proceso de daemonización completo."""

    # Primer fork
    pid = os.fork()
    if pid > 0:
        sys.exit(0)  # Padre termina

    # Crear nueva sesión
    os.setsid()

    # Ignorar SIGHUP (evitar terminar cuando el líder de sesión muere)
    signal.signal(signal.SIGHUP, signal.SIG_IGN)

    # Segundo fork (prevenir readquirir terminal)
    pid = os.fork()
    if pid > 0:
        sys.exit(0)

    # Cambiar directorio
    os.chdir("/")

    # Resetear umask
    os.umask(0)

    # Cerrar file descriptors
    for fd in range(0, 1024):
        try:
            os.close(fd)
        except OSError:
            pass

    # Abrir /dev/null para stdin/stdout/stderr
    os.open("/dev/null", os.O_RDWR)  # stdin (fd 0)
    os.dup2(0, 1)  # stdout
    os.dup2(0, 2)  # stderr

def daemon_main():
    """Código principal del daemon."""
    # Escribir PID file
    with open("/tmp/mydaemon.pid", "w") as f:
        f.write(str(os.getpid()))

    # Setup señales
    running = [True]

    def shutdown(sig, frame):
        running[0] = False

    signal.signal(signal.SIGTERM, shutdown)

    # Loop principal
    import time
    while running[0]:
        with open("/tmp/mydaemon.log", "a") as f:
            f.write(f"Daemon alive at {time.ctime()}\n")
        time.sleep(10)

    # Cleanup
    os.unlink("/tmp/mydaemon.pid")

if __name__ == "__main__":
    daemonize()
    daemon_main()
```

---

## Herramientas de diagnóstico

### strace para señales

```bash
# Ver señales que recibe un proceso
strace -e trace=signal ./programa

# Filtrar solo delivery de señales
strace -e signal=SIGINT,SIGTERM ./programa

# Ver señales de proceso existente
strace -p <pid> -e trace=signal
```

### /proc/[pid]/status

```bash
# Ver señales pendientes, bloqueadas, etc.
cat /proc/$$/status | grep -i sig

# SigQ: señales en queue / límite
# SigPnd: señales pendientes para el thread
# ShdPnd: señales pendientes para el proceso
# SigBlk: señales bloqueadas
# SigIgn: señales ignoradas
# SigCgt: señales con handler
```

### kill -0: verificar si proceso existe

```bash
# No envía señal, solo verifica que el proceso existe
kill -0 <pid>
echo $?  # 0 si existe, 1 si no
```

---

## Recursos adicionales

- [signal(7) man page](https://man7.org/linux/man-pages/man7/signal.7.html) - Documentación completa
- [Linux Programming Interface Cap. 20-22](https://man7.org/tlpi/) - Tratamiento exhaustivo de señales
- [Python signal module docs](https://docs.python.org/3/library/signal.html) - Referencia de Python
- [Async-Signal-Safe Functions](https://man7.org/linux/man-pages/man7/signal-safety.7.html) - Lista de funciones seguras

---

*Computación II - 2026 - Clase 5 - Material opcional*
