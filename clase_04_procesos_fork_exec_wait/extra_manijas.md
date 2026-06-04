# Clase 4: Procesos - fork, exec, wait — Extra Manijas

> Material opcional de profundización.

---

## 1. `vfork()` y `clone()`

`fork()` no es la única forma de crear un proceso en Linux. La syscall real "debajo" es `clone()`, que permite elegir con bits de flag qué se comparte y qué no.

```c
// Equivalencias aproximadas:
pid_t fork(void)  =  clone(SIGCHLD)          // todo separado, hijo señala al morir
pid_t vfork(void) =  clone(CLONE_VFORK | CLONE_VM | SIGCHLD)  // comparte memoria, padre bloqueado
threads          =  clone(CLONE_VM | CLONE_FS | CLONE_FILES | CLONE_SIGHAND | CLONE_THREAD | ...)
```

- **`vfork()`**: optimización vieja. El padre se bloquea hasta que el hijo haga exec o salga. Hoy se usa poco.
- **`clone()`**: la primitiva real. Threads de Linux son procesos creados con `clone()` compartiendo casi todo.

Pueden ver el código de pthread_create() en glibc y van a ver que llama a clone().

---

## 2. fork bomb (peligroso, no probar sin contenedor)

```python
import os
while True:
    os.fork()
```

Cada fork crea un nuevo proceso. Cada nuevo proceso ejecuta el mismo loop y vuelve a hacer fork. Crecimiento exponencial: rápidamente agotan la tabla de procesos y el sistema se cuelga.

En bash el clásico es:
```bash
:(){ :|:& };:
```

**Cómo defenderse**: el sistema tiene un límite por usuario configurable con `ulimit -u`. Probá:
```bash
ulimit -u 100   # solo 100 procesos para este usuario
```

---

## 3. `posix_spawn()` — el reemplazo moderno

`posix_spawn()` combina fork + exec en una sola syscall, evitando el costo del fork cuando vas a hacer exec inmediato. Es lo que usa `multiprocessing` con el método `spawn` (lo vimos en clase 8).

```c
posix_spawn(&pid, "/bin/ls", NULL, NULL, args, env);
// Equivale a: fork + setup + execve, en una sola llamada
```

Beneficios:
- Más rápido (no copia memoria innecesariamente)
- Más portable (funciona donde fork no, como sistemas embebidos)

---

## 4. Reaping zombies con SIGCHLD

Un patrón clásico: registrar un handler de señal que recoja automáticamente a los hijos cuando terminan.

```python
import signal
import os

def reaper(signum, frame):
    """Recoge zombies sin bloquear."""
    while True:
        try:
            pid, status = os.waitpid(-1, os.WNOHANG)
            if pid == 0:
                break
            print(f"Recogí hijo {pid}, código {os.WEXITSTATUS(status)}")
        except ChildProcessError:
            break

signal.signal(signal.SIGCHLD, reaper)

# Ahora podemos crear hijos sin preocuparnos por hacer wait():
for _ in range(5):
    if os.fork() == 0:
        os._exit(0)

# El reaper se llama automáticamente cuando los hijos terminan
import time; time.sleep(2)
```

Esto se va a ver en detalle en la **clase 6 (Señales)**.

---

## 5. Procesos huérfanos y init

Cuando un padre termina antes que sus hijos, los hijos no mueren — quedan **huérfanos**. El kernel los re-asigna como hijos de init (PID 1, o systemd hoy).

```python
import os
import time

if os.fork() == 0:
    # Hijo: vive más que el padre
    time.sleep(10)
    print(f"Mi padre ahora es: {os.getppid()}")
    # Va a imprimir 1 (init/systemd)
    os._exit(0)
else:
    # Padre: muere inmediatamente
    print("Padre muriendo")
    os._exit(0)
```

Ejecutalo y vas a ver que el hijo después de 10 segundos reporta `os.getppid() == 1`. init recoge automáticamente a los huérfanos cuando terminan.

---

## 6. Containers: namespaces y `unshare()`

Cuando Docker crea un contenedor, lo que hace por debajo es:

```c
clone(CLONE_NEWPID | CLONE_NEWNET | CLONE_NEWNS | CLONE_NEWUTS | ...)
```

Esos flags crean **namespaces** separados: el contenedor cree que es PID 1, tiene su propia red, sus propios mounts, etc. — pero técnicamente es solo un proceso del host con flags especiales.

Comando útil:
```bash
unshare --pid --fork --mount-proc bash
# Ahora estás en un namespace PID nuevo; ps muestra solo este shell
```

---

## 7. Lecturas recomendadas

- **Advanced Programming in the UNIX Environment** (Stevens & Rago) — capítulos 8 y 9 son el oro absoluto sobre procesos
- **The Linux Programming Interface** (Kerrisk) — más moderno, también imprescindible
- **man fork(2)**, **man execve(2)**, **man wait(2)** — la doc oficial es buena
- **man clone(2)** — para entender cómo funciona realmente fork

---

*Computación II - 2026 - Clase 4 — Material opcional*
