# Clase 5: Pipes y Redirección - Extra Manijas

Material opcional para profundizar.

---

## Internals de los file descriptors

### La estructura del kernel

Cada proceso tiene una tabla de file descriptors (en el `task_struct` del kernel). Cada entrada apunta a una estructura `file` que contiene:

- Posición actual (offset) para lectura/escritura
- Modo de apertura (lectura, escritura, append)
- Puntero al inodo (o estructura equivalente para pipes/sockets)
- Contador de referencias

```
Proceso A                    Kernel                        Disco
+--------+                 +--------+                   +--------+
| fd 0 --|---------------->| file   |------------------>| inodo  |
| fd 1 --|---+             | offset |                   | datos  |
| fd 3 --|   |             +--------+                   +--------+
+--------+   |
             |             +--------+
             +------------>| file   |------> pipe buffer
                           | flags  |
                           +--------+
```

### dup vs dup2

```c
int dup(int oldfd);        // Retorna el menor fd disponible
int dup2(int oldfd, int newfd);  // Usa específicamente newfd
```

`dup` es más simple pero menos controlable. `dup2` es esencial para redirección porque necesitás controlar exactamente qué fd reemplazás.

```python
import os

# dup: el kernel elige el fd
nuevo_fd = os.dup(1)  # Podría ser 3, 4, etc.

# dup2: vos elegís el fd
os.dup2(1, 10)  # fd 10 ahora apunta a donde apunta 1
```

### fcntl y control de file descriptors

`fcntl` permite manipular propiedades de los file descriptors:

```python
import os
import fcntl

fd = os.open("/tmp/test.txt", os.O_RDWR | os.O_CREAT, 0o644)

# Ver flags actuales
flags = fcntl.fcntl(fd, fcntl.F_GETFL)
print(f"Flags: {flags}")

# Hacer non-blocking
fcntl.fcntl(fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)

# Close-on-exec: cerrar automáticamente en exec()
fcntl.fcntl(fd, fcntl.F_SETFD, fcntl.FD_CLOEXEC)
```

---

## Pipes a fondo

### El buffer del pipe

En Linux, el buffer del pipe tiene un tamaño por defecto (usualmente 64KB) pero puede modificarse:

```python
import os
import fcntl

r, w = os.pipe()

# Ver tamaño actual del buffer
F_GETPIPE_SZ = 1032
size = fcntl.fcntl(r, F_GETPIPE_SZ)
print(f"Tamaño del buffer: {size} bytes")

# Modificar tamaño (requiere root para valores > /proc/sys/fs/pipe-max-size)
F_SETPIPE_SZ = 1031
try:
    fcntl.fcntl(r, F_SETPIPE_SZ, 1024*1024)  # 1MB
    new_size = fcntl.fcntl(r, F_GETPIPE_SZ)
    print(f"Nuevo tamaño: {new_size} bytes")
except OSError as e:
    print(f"No se pudo cambiar: {e}")

os.close(r)
os.close(w)
```

### Atomicidad de escritura

POSIX garantiza que escrituras de hasta `PIPE_BUF` bytes (usualmente 4KB) son atómicas - no se entremezclarán con escrituras de otros procesos.

```python
import os

# PIPE_BUF está en os.fpathconf o hardcodeado
PIPE_BUF = 4096  # Típico en Linux

# Escrituras menores a PIPE_BUF son atómicas
# Escrituras mayores pueden fragmentarse
```

### Non-blocking I/O en pipes

Por defecto, read/write en pipes bloquean. Podemos cambiar esto:

```python
import os
import fcntl
import errno

r, w = os.pipe()

# Hacer el lado de lectura non-blocking
flags = fcntl.fcntl(r, fcntl.F_GETFL)
fcntl.fcntl(r, fcntl.F_SETFL, flags | os.O_NONBLOCK)

# Ahora read no bloquea, retorna error si está vacío
try:
    datos = os.read(r, 1024)
except BlockingIOError:
    print("Pipe vacío, no hay datos disponibles")

# Escribir algo
os.write(w, b"hola")

# Ahora sí hay datos
datos = os.read(r, 1024)
print(f"Leído: {datos}")

os.close(r)
os.close(w)
```

---

## Pipes y select/poll/epoll

Para manejar múltiples pipes (o sockets) sin bloquear, usamos mecanismos de multiplexación de I/O.

### select

```python
import os
import select

# Crear varios pipes
pipes = []
for i in range(3):
    r, w = os.pipe()
    pipes.append((r, w))

# Escribir a uno de ellos
os.write(pipes[1][1], b"datos en pipe 1")

# Esperar a que alguno tenga datos listos para leer
read_fds = [p[0] for p in pipes]
readable, _, _ = select.select(read_fds, [], [], 1.0)

print(f"Pipes con datos: {readable}")

for r in readable:
    datos = os.read(r, 1024)
    print(f"fd {r}: {datos}")

# Limpiar
for r, w in pipes:
    os.close(r)
    os.close(w)
```

### poll y epoll

`poll` escala mejor que `select` para muchos file descriptors. `epoll` es aún más eficiente para grandes números de conexiones (usado por servidores web de alto rendimiento).

```python
import os
import select

# Usando poll
r, w = os.pipe()
poll = select.poll()
poll.register(r, select.POLLIN)

# Escribir datos
os.write(w, b"test")

# Poll con timeout de 1 segundo
events = poll.poll(1000)
for fd, event in events:
    if event & select.POLLIN:
        print(f"fd {fd} tiene datos: {os.read(fd, 1024)}")

os.close(r)
os.close(w)
```

---

## Process substitution

Bash tiene una característica llamada process substitution que crea FIFOs temporales automáticamente:

```bash
# <(comando) crea un fd que produce la salida del comando
diff <(ls dir1) <(ls dir2)

# >(comando) crea un fd que alimenta la entrada del comando
tee >(gzip > archivo.gz) >(wc -l) < input.txt
```

Podemos simular esto en Python:

```python
import os
import subprocess
import tempfile

def process_substitution(cmd):
    """Simula <(comando) de bash."""
    # Crear FIFO temporal
    fifo_path = tempfile.mktemp()
    os.mkfifo(fifo_path)

    # Fork proceso que escribe al FIFO
    pid = os.fork()
    if pid == 0:
        with open(fifo_path, 'w') as f:
            resultado = subprocess.run(cmd, stdout=f, shell=True)
        os.unlink(fifo_path)
        os._exit(0)

    return fifo_path, pid

# Uso: diff <(ls /tmp) <(ls /var)
fifo1, pid1 = process_substitution("ls /tmp")
fifo2, pid2 = process_substitution("ls /var")

# diff lee de los FIFOs
subprocess.run(["diff", fifo1, fifo2])

# Limpiar
os.waitpid(pid1, 0)
os.waitpid(pid2, 0)
os.unlink(fifo1)
os.unlink(fifo2)
```

---

## splice, tee y vmsplice

Linux tiene syscalls especializadas para mover datos entre pipes sin copiarlos al userspace:

### splice

Mueve datos entre un fd de archivo y un pipe (o entre dos pipes) sin copiar a userspace:

```c
// C - no disponible directamente en Python
ssize_t splice(int fd_in, off_t *off_in, int fd_out, off_t *off_out,
               size_t len, unsigned int flags);
```

Esto es lo que usa `cat` moderno para ser eficiente.

### tee (syscall, no el comando)

Duplica datos de un pipe a otro sin consumirlos:

```c
ssize_t tee(int fd_in, int fd_out, size_t len, unsigned int flags);
```

### Uso desde Python con ctypes

```python
import ctypes
import os

libc = ctypes.CDLL("libc.so.6", use_errno=True)

# Crear dos pipes
r1, w1 = os.pipe()
r2, w2 = os.pipe()

# Escribir al primer pipe
os.write(w1, b"datos para duplicar")

# tee: copiar de pipe1 a pipe2 sin consumir
SPLICE_F_NONBLOCK = 2
copied = libc.tee(r1, w2, 1024, SPLICE_F_NONBLOCK)
if copied < 0:
    errno = ctypes.get_errno()
    print(f"Error: {os.strerror(errno)}")
else:
    print(f"Copiados {copied} bytes")

    # Ahora ambos pipes tienen los datos
    print(f"Pipe 1: {os.read(r1, 1024)}")
    print(f"Pipe 2: {os.read(r2, 1024)}")

for fd in [r1, w1, r2, w2]:
    os.close(fd)
```

---

## Redirección en el kernel

### La tabla de open files

El kernel mantiene una tabla global de archivos abiertos. Múltiples file descriptors pueden apuntar al mismo archivo:

```
Proceso A          Sistema            Proceso B
  fd 0 ─────────┐                    ┌───── fd 3
  fd 1 ────┐    │    ┌─────────┐     │
           │    └───>│ file 1  │<────┘
           │         │ (pipe)  │
           │         └─────────┘
           │
           │         ┌─────────┐
           └────────>│ file 2  │
                     │ (/dev/  │
                     │  tty)   │
                     └─────────┘
```

### Fork y file descriptors

Después de fork, padre e hijo comparten las estructuras `file` del kernel. Esto significa que comparten:
- La posición (offset) del archivo
- Los locks
- El modo de apertura

```python
import os

# Abrir archivo
f = open("/tmp/test.txt", "w")

pid = os.fork()

if pid == 0:
    # Hijo escribe
    f.write("Hijo escribe primero\n")
    f.flush()
    os._exit(0)
else:
    os.wait()
    # Padre escribe después - posición actualizada por el hijo
    f.write("Padre escribe después\n")
    f.close()

# El archivo contiene ambas líneas porque comparten el offset
```

---

## Implementando redirección como bash

### El orden importa

En bash, `2>&1 > archivo` y `> archivo 2>&1` son diferentes:

```bash
# Primero: stderr va a donde va stdout (terminal)
# Después: stdout va a archivo
# Resultado: stdout a archivo, stderr a terminal
comando 2>&1 > archivo

# Primero: stdout va a archivo
# Después: stderr va a donde va stdout (archivo)
# Resultado: ambos a archivo
comando > archivo 2>&1
```

### Implementación

```python
import os

def configurar_redirecciones(redirecciones):
    """
    Configura redirecciones.
    redirecciones es una lista de tuplas: (operacion, args)
    Operaciones: '>' (stdout a archivo), '2>' (stderr a archivo),
                 '>>' (append), '2>&1' (stderr a stdout)
    """
    for op, arg in redirecciones:
        if op == '>':
            fd = os.open(arg, os.O_CREAT | os.O_WRONLY | os.O_TRUNC, 0o644)
            os.dup2(fd, 1)
            os.close(fd)
        elif op == '>>':
            fd = os.open(arg, os.O_CREAT | os.O_WRONLY | os.O_APPEND, 0o644)
            os.dup2(fd, 1)
            os.close(fd)
        elif op == '2>':
            fd = os.open(arg, os.O_CREAT | os.O_WRONLY | os.O_TRUNC, 0o644)
            os.dup2(fd, 2)
            os.close(fd)
        elif op == '2>&1':
            os.dup2(1, 2)  # stderr -> donde apunte stdout
        elif op == '&>':
            # stdout y stderr al mismo archivo
            fd = os.open(arg, os.O_CREAT | os.O_WRONLY | os.O_TRUNC, 0o644)
            os.dup2(fd, 1)
            os.dup2(fd, 2)
            os.close(fd)
        elif op == '<':
            fd = os.open(arg, os.O_RDONLY)
            os.dup2(fd, 0)
            os.close(fd)
```

---

## Coprocesses

Un coproceso es un proceso que corre en paralelo con comunicación bidireccional via pipes.

```python
import os

def crear_coproceso(cmd, args):
    """
    Crea un coproceso.
    Retorna (pid, stdin_write, stdout_read)
    """
    # Pipe para stdin del coproceso
    stdin_read, stdin_write = os.pipe()

    # Pipe para stdout del coproceso
    stdout_read, stdout_write = os.pipe()

    pid = os.fork()
    if pid == 0:
        # Coproceso
        os.close(stdin_write)
        os.close(stdout_read)

        os.dup2(stdin_read, 0)   # stdin <- pipe
        os.dup2(stdout_write, 1) # stdout -> pipe

        os.close(stdin_read)
        os.close(stdout_write)

        os.execvp(cmd, [cmd] + args)
        os._exit(1)

    # Proceso principal
    os.close(stdin_read)
    os.close(stdout_write)

    return pid, stdin_write, stdout_read


# Ejemplo: coproceso con bc (calculadora)
pid, to_bc, from_bc = crear_coproceso("bc", ["-l"])

# Enviar expresiones a bc
os.write(to_bc, b"2 + 2\n")
os.write(to_bc, b"sqrt(2)\n")
os.write(to_bc, b"quit\n")
os.close(to_bc)

# Leer resultados
import select
while True:
    ready, _, _ = select.select([from_bc], [], [], 0.1)
    if ready:
        data = os.read(from_bc, 1024)
        if not data:
            break
        print(f"bc dice: {data.decode().strip()}")
    else:
        break

os.close(from_bc)
os.waitpid(pid, 0)
```

---

## Recursos adicionales

- [pipe(7) man page](https://man7.org/linux/man-pages/man7/pipe.7.html) - Documentación completa de pipes
- [The Linux Programming Interface - Caps. 44-46](https://man7.org/tlpi/) - Pipes, FIFOs y más
- [Advanced Programming in the UNIX Environment](https://www.apuebook.com/) - Stevens, clásico
- [Beej's Guide to Unix IPC](https://beej.us/guide/bgipc/) - Tutorial gratuito excelente

---

*Computación II - 2026 - Clase 5 - Material opcional*
