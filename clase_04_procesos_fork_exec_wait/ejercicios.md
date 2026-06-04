# Clase 4: Procesos - fork, exec, wait — Ejercicios

> Estos ejercicios cubren `fork()`, `exec()`, `wait()` y el patrón fork-exec.
> Los ejercicios sobre **anatomía del proceso** (memoria, FDs, jerarquía) están en la clase 3.

---

## Ejercicio 1: Primer fork

**Objetivo:** Hacer tu primer `os.fork()` y entender el doble flujo de ejecución.

**Consigna:** escribí un programa que haga `fork()` y luego cada uno (padre e hijo) imprima su PID y el PID del padre. El padre debe esperar al hijo antes de imprimir "Programa terminado".

<details>
<summary>Ver solución</summary>

```python
import os

pid = os.fork()

if pid == 0:
    print(f"Soy el hijo: PID={os.getpid()}, padre={os.getppid()}")
    os._exit(0)
else:
    print(f"Soy el padre: PID={os.getpid()}, hijo={pid}")
    os.wait()
    print("Programa terminado")
```
</details>

---

## Ejercicio 2: Crear N hijos

**Objetivo:** Crear varios hijos en un loop, cada uno con un ID distinto, y esperarlos a todos.

**Consigna:** creá un programa que haga fork 5 veces. Cada hijo debe imprimir su número (0 a 4), dormir un tiempo aleatorio entre 0.5 y 2 segundos y terminar con un código de salida igual a su número. El padre debe esperar a todos los hijos y mostrar el código de salida de cada uno.

<details>
<summary>Ver solución</summary>

```python
import os
import time
import random

hijos = []
for i in range(5):
    pid = os.fork()
    if pid == 0:
        duracion = random.uniform(0.5, 2)
        print(f"[Hijo {i}] PID={os.getpid()}, dormiré {duracion:.1f}s")
        time.sleep(duracion)
        os._exit(i)
    else:
        hijos.append((pid, i))

for pid, i in hijos:
    _, status = os.waitpid(pid, 0)
    codigo = os.WEXITSTATUS(status)
    print(f"Hijo {i} (PID {pid}) terminó con código {codigo}")
```
</details>

---

## Ejercicio 3: Patrón fork-exec

**Objetivo:** Reemplazar el programa del hijo con `exec`.

**Consigna:** implementá un mini-launcher que ejecute un comando externo (ej: `ls -la /tmp`). El padre debe esperar al hijo y reportar su código de salida.

<details>
<summary>Ver solución</summary>

```python
import os
import sys

def lanzar(comando, args):
    pid = os.fork()
    if pid == 0:
        os.execvp(comando, [comando] + args)
        # Si llegamos aquí, exec falló
        print(f"Error: no se pudo ejecutar {comando}", file=sys.stderr)
        os._exit(127)
    else:
        _, status = os.waitpid(pid, 0)
        return os.WEXITSTATUS(status)

codigo = lanzar("ls", ["-la", "/tmp"])
print(f"Comando terminó con código {codigo}")
```
</details>

---

## Ejercicio 4: Zombies

**Objetivo:** Crear (y después limpiar) un proceso zombie.

**Consigna:** escribí un programa donde el padre haga fork, el hijo termine inmediatamente y el padre se quede vivo 30 segundos sin hacer `wait()`. En otra terminal, ejecutá `ps aux | grep -E 'Z|defunct'` para verlo. Después, modificá el código para que el padre haga `wait()` y verificá que el zombie desaparece.

<details>
<summary>Ver solución</summary>

```python
import os
import time

pid = os.fork()

if pid == 0:
    print(f"[Hijo PID={os.getpid()}] termino inmediatamente")
    os._exit(0)
else:
    print(f"[Padre PID={os.getpid()}] creé hijo {pid}, no lo voy a esperar")
    print("Mirá con: ps aux | grep -E 'Z|defunct'")
    time.sleep(30)
    # Para limpiar: descomentar
    # os.wait()
    # print("Hijo recogido, ya no es zombie")
```
</details>

---

## Ejercicio 5: Mini-shell (Obligatorio)

**Objetivo:** Implementar un shell minimalista que use el patrón fork-exec.

**Consigna:** implementá un shell que:
1. Muestre un prompt `$ ` y lea un comando
2. Si el comando es `exit`, termine
3. Si el comando es `cd`, cambie de directorio (sin fork, porque cd debe afectar al shell mismo)
4. Para cualquier otro comando, haga fork+exec+wait
5. Imprima el código de salida si no es 0

<details>
<summary>Ver solución</summary>

Ver `clase_04_procesos_fork_exec_wait/contenido.md` sección "Procesos en práctica: el shell" — esa implementación es la solución base. Tu versión puede agregar:

- Manejo de pipes con `|` (verás en clase 5)
- Background processes con `&` (no esperar al hijo)
- Variables de entorno con `export VAR=value`
- Historial de comandos
</details>

---

## Ejercicio 6: Comunicación por código de salida

**Objetivo:** Practicar fork con código de salida como mensaje.

**Consigna:** escribí una función `archivo_existe(path)` que use fork: el hijo intenta abrir el archivo y sale con código 0 si pudo, 1 si no. El padre devuelve True o False según el código.

<details>
<summary>Ver solución</summary>

```python
import os

def archivo_existe(path):
    pid = os.fork()
    if pid == 0:
        try:
            with open(path):
                pass
            os._exit(0)
        except OSError:
            os._exit(1)
    else:
        _, status = os.waitpid(pid, 0)
        return os.WEXITSTATUS(status) == 0

print(archivo_existe("/etc/passwd"))     # True
print(archivo_existe("/no_existe"))      # False
```
</details>

---

## Ejercicios adicionales

### Watcher de archivos

Lanzá un proceso hijo que se quede mirando un archivo (con polling) y reporte cada vez que se modifica. El padre podría matar al hijo con una señal después de cierto tiempo.

### Pool manual de workers

Implementá un "mini pool" usando solo fork: el padre tiene una lista de tareas, lanza N hijos, cada hijo agarra una tarea y la procesa, terminado, y el padre lanza un nuevo hijo hasta agotar las tareas.

---

*Computación II - 2026 - Clase 4*
