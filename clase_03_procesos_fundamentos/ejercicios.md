# Clase 3: Procesos - Fundamentos — Ejercicios

> Estos ejercicios cubren la **anatomía del proceso** (jerarquía, PID/PPID, memoria virtual, file descriptors).
> Los ejercicios sobre `fork()`, `exec()` y `wait()` están en la **clase 4**.

---

## Ejercicio 1: Explorar tu propio proceso

**Objetivo:** Inspeccionar la información de un proceso usando Python y `/proc`.

**Consigna:** escribí un script que imprima:
- Su PID y PPID
- Su working directory
- Sus file descriptors abiertos (listando `/proc/<pid>/fd/`)
- Su mapa de memoria (las primeras líneas de `/proc/<pid>/maps`)

<details>
<summary>Ver solución</summary>

```python
import os

pid = os.getpid()
print(f"PID: {pid}")
print(f"PPID: {os.getppid()}")
print(f"CWD: {os.getcwd()}")

print("\nFile descriptors abiertos:")
for fd in os.listdir(f"/proc/{pid}/fd"):
    try:
        link = os.readlink(f"/proc/{pid}/fd/{fd}")
        print(f"  fd {fd} -> {link}")
    except OSError:
        pass

print("\nMapa de memoria (primeras 20 líneas):")
with open(f"/proc/{pid}/maps") as f:
    for i, line in enumerate(f):
        if i >= 20: break
        print(f"  {line.strip()}")
```
</details>

---

## Ejercicio 2: Árbol de procesos

**Objetivo:** Ver la jerarquía de procesos del sistema.

**Consigna:** desde la línea de comandos, ejecutá:

```bash
pstree -p $$           # tu shell y sus descendientes
ps -ef --forest        # todos los procesos del sistema en árbol
ps -o pid,ppid,comm -p $$ $(pgrep -P $$)
```

Identificá:
- El PID 1 — ¿qué proceso es?
- Tu shell — ¿quién es su padre?
- Subí la jerarquía hasta llegar a init/systemd

---

## Ejercicio 3: Memoria virtual — observar text/data/heap/stack

**Objetivo:** Identificar los segmentos de memoria en `/proc/<pid>/maps`.

**Consigna:** corré un programa simple en background, mirá su `/proc/<pid>/maps` y andá identificando:

- ¿Dónde está el text segment? (busca el ejecutable, permisos `r-xp`)
- ¿Dónde está el heap? (busca la línea con `[heap]`)
- ¿Dónde está el stack? (busca `[stack]`)
- ¿Qué hay en las regiones intermedias? (librerías `.so` cargadas)

```bash
python3 -c "import time; time.sleep(60)" &
cat /proc/$!/maps
```

---

## Ejercicio 4: PIDs y reciclado

**Objetivo:** Ver que los PIDs se reciclan.

**Consigna:** corré muchos procesos rápidos consecutivos. Vas a ver que los PIDs aumentan, pero al alcanzar el máximo (`/proc/sys/kernel/pid_max`) se reciclan.

```bash
for i in $(seq 1 20); do
    sh -c 'echo "PID=$$"'
done

# Ver el máximo
cat /proc/sys/kernel/pid_max
```

---

## Ejercicios adicionales

### Conteo de procesos por usuario

Hacé un programa que use `ps` o `/proc` y reporte cuántos procesos tiene cada usuario del sistema.

### Detector de huérfanos

Escribí un script que recorra `/proc` y encuentre procesos cuyo PPID sea 1 (huérfanos adoptados por init).

---

*Computación II - 2026 - Clase 3*
