# Trabajo Práctico Nº 1: Monitor de Procesos y Threads (versión macOS)

**Computación II — Universidad de Mendoza — 2026**

> Esta es la **versión para alumnos que trabajen en macOS** sin Docker Linux.
> Es funcionalmente equivalente a la versión Linux: mismos objetivos, misma arquitectura,
> misma evaluación. La diferencia está en **cómo se extrae la información del SO**, porque
> macOS no tiene `/proc` y usa APIs nativas (libproc + Mach).

---

## Información general

| | |
|-|-|
| **Entrega** | Clase 11 (02/06/2026) al final de la clase de Sincronización II |
| **Modalidad** | Individual |
| **Plataforma** | macOS (Intel o Apple Silicon) |
| **Lenguaje** | Python 3.11+ |
| **Entrega** | Repositorio público en GitHub |

> **Importante**: si trabajás en Linux (nativo o con Docker), usá la versión `consigna.md`.
> Esta versión es solo para quienes prefieren trabajar directo en macOS.

---

## Objetivos pedagógicos

Al terminar este TP deberías poder:

1. **Inspeccionar un proceso de macOS desde fuera**, leyendo información del kernel mediante `libproc`, syscalls Mach y herramientas nativas (`sysctl`, `ps`, `lsof`, `vm_stat`).
2. **Diseñar un sistema multiproceso** que distribuye trabajo entre componentes que se ejecutan en paralelo.
3. **Comunicar procesos** usando `Queue`, `Pipe` y memoria compartida (`Manager`, `Value`, `Array`).
4. **Manejar señales** para implementar shutdown limpio, reload y dump on-demand.
5. **Identificar y resolver race conditions** con primitivas de sincronización.
6. **Conectar la teoría de la materia** con un sistema vivo y entender las **diferencias entre familias UNIX**: por qué macOS (Darwin/XNU) tiene un modelo distinto a Linux para exponer info del kernel.

---

## Diferencias clave con la versión Linux

| Aspecto | Linux | macOS |
|---------|-------|-------|
| **Modelo de inspección** | Filesystem virtual `/proc` (todo es archivo) | Llamadas a APIs (libproc + Mach) |
| **Info de procesos** | Leer `/proc/<pid>/...` | `proc_pidinfo()`, `proc_listpids()` |
| **Info de threads** | `/proc/<pid>/task/<tid>/` | `task_threads()`, `thread_info()` (Mach) |
| **Info del sistema** | `/proc/stat`, `/proc/meminfo` | `sysctl`, `host_statistics()`, `vm_stat` |
| **File descriptors** | `/proc/<pid>/fd/` | `proc_pidfdinfo()` con tipo de FD |
| **Memoria virtual** | `/proc/<pid>/maps` | `mach_vm_region()` o `vmmap` CLI |
| **Señales (info)** | Líneas SigBlk/SigIgn/SigCgt en `status` | Bits de máscaras vía `proc_pidinfo` + estructuras Mach |
| **Scheduling** | `nice`, `priority` en `stat` | `getpriority()`, `task_policy_get()` |

> **Nota cultural**: macOS usa el kernel **XNU**, que combina Mach (microkernel) y BSD. Por eso muchas APIs son híbridas: algunas son tipo BSD (`getpriority`, `sysctl`), otras son Mach (`task_info`, `host_statistics`). El TP te lleva a tocar ambas.

---

## Descripción del sistema a construir

Vas a desarrollar un **monitor del sistema en tiempo real**, parecido a `htop` o al `Activity Monitor` de macOS pero con énfasis en mostrar la **anatomía interna** de cada proceso y sus threads. La información se extrae llamando directamente a APIs del SO (no se permite `psutil` ni equivalentes).

El monitor es un **sistema multiproceso**: un recolector central consulta el SO, distribuye el trabajo entre analizadores especializados que corren en paralelo, un agregador mantiene el snapshot global en memoria compartida, y una interfaz de texto (TUI) muestra los datos al usuario con múltiples vistas alternables.

---

## Arquitectura mínima obligatoria

```
       ┌──────────────────────────────────────┐
       │           SNAPSHOT GLOBAL            │
       │      (Manager dict compartido)       │
       │  ┌─────────────────────────────────┐ │
       │  │ "resumen"   : {...}  ts: ...    │ │
       │  │ "memoria"   : {...}  ts: ...    │ │
       │  │ "fds"       : {...}  ts: ...    │ │
       │  │ "threads"   : {...}  ts: ...    │ │
       │  │ "senales"   : {...}  ts: ...    │ │
       │  │ "scheduling": {...}  ts: ...    │ │
       │  │ "sistema"   : {...}  ts: ...    │ │
       │  └─────────────────────────────────┘ │
       └────────▲─────────────────────▲───────┘
                │ escriben            │ lee
   ┌────────────┼─────────┬──────────┴────────┐
   │            │         │                    │
┌──▼──────┐ ┌───▼─────┐ ┌─▼──────┐  ...  ┌────▼─────┐
│Resumen  │ │Memoria  │ │FDs     │       │ Display  │
│cada 2s  │ │cada 3s  │ │cada 5s │       │ TUI      │
└─────────┘ └─────────┘ └────────┘       │ (vista   │
                                          │ activa)  │
   7 analizadores en paralelo,            └──────────┘
   cada uno con su propio ritmo
```

### Componentes mínimos

| Componente | Responsabilidad |
|------------|----------------|
| **Recolector** | Lista procesos (vía `libproc` o `ps`), distribuye trabajo a los analizadores |
| **7 analizadores** | Cada uno extrae una dimensión específica (resumen, memoria, FDs, threads, señales, scheduling, sistema) |
| **Agregador** | Mantiene el snapshot global en memoria compartida |
| **Display (TUI)** | Renderiza la vista activa según los datos del snapshot |
| **Manejador de señales** | Captura las señales que recibe el monitor y dispara acciones |

Cada analizador es un **proceso independiente** (no thread), con su propio intervalo de refresco. La comunicación entre componentes debe usar primitivas de `multiprocessing` (`Queue`, `Pipe`, `Manager`, `Value`, `Array`).

> **Nota sobre threads**: podés usar threads internamente dentro del proceso de display para la entrada de teclado. Pero la arquitectura principal debe ser **multiproceso**, no multithread.

---

## Datos a mostrar por proceso

A continuación se detallan los datos a extraer y **las APIs específicas de macOS** que los proveen.

### Cómo acceder a las APIs nativas desde Python

Hay tres caminos válidos (podés mezclarlos):

1. **`ctypes` directamente sobre `libproc.dylib`** (la opción más educativa, más cercana al SO)
2. **`subprocess` invocando herramientas CLI nativas** (`ps`, `lsof`, `vm_stat`, `sysctl`, `vmmap`)
3. **Una combinación**: ctypes donde se pueda, subprocess donde sea más práctico

Lo que **NO** se permite:
- `psutil` ni equivalentes que abstraigan todo
- Librerías que envuelvan libproc por vos (ej: `macos-pid`, `pylibproc`)

### Datos básicos (vista Resumen)

| Dato | Cómo obtenerlo en macOS |
|------|------------------------|
| PID | `proc_listpids(PROC_ALL_PIDS, 0, ...)` |
| PPID | `proc_pidinfo(pid, PROC_PIDBSDINFO, ...)` campo `pbi_ppid` |
| UID/GID + usuario | `pbi_uid`, `pbi_gid` y `pwd.getpwuid()` |
| Estado (R/S/D/T/Z, equivalentes Darwin: SIDL/SRUN/SSLEEP/SSTOP/SZOMB) | `pbi_status` |
| Comando | `proc_pidpath(pid, ...)` (path completo del ejecutable) |
| Args completos | `sysctl(KERN_PROCARGS2, pid)` |
| CPU% | `proc_pid_rusage(pid, RUSAGE_INFO_V4)` campo `ri_user_time` + `ri_system_time` (delta entre lecturas) |
| Cantidad de threads | `task_threads()` o `task_info(TASK_BASIC_INFO)` |

### Memoria

| Dato | Cómo obtenerlo en macOS |
|------|------------------------|
| RSS (resident size) | `task_info(TASK_BASIC_INFO_64)` campo `resident_size` |
| Virtual size | `task_info()` campo `virtual_size` |
| Memoria física compartida vs privada | `task_info(TASK_VM_INFO)` campos `phys_footprint`, `internal`, `compressed` |
| Page faults | `proc_pid_rusage()` campos `ri_pageins` |
| Regiones de memoria (equivalente a `/proc/<pid>/maps`) | `mach_vm_region()` o invocar `vmmap <pid>` y parsear |

### File Descriptors

| Dato | Cómo obtenerlo en macOS |
|------|------------------------|
| Lista de FDs abiertos | `proc_pidinfo(pid, PROC_PIDLISTFDS, ...)` |
| Info de cada FD | `proc_pidfdinfo(pid, fd, PROC_PIDFDVNODEPATHINFO, ...)` |
| Tipo de FD (vnode/socket/pipe/kqueue) | El campo `proc_fdtype` en el listado |
| Path del archivo (si es file) | `vip_path` en `proc_fdinfo_vnodepathinfo` |
| Info de socket | `proc_pidfdinfo(pid, fd, PROC_PIDFDSOCKETINFO, ...)` |

Alternativa práctica: invocar `lsof -p <pid> -F` y parsear.

### Threads (Mach threads)

| Dato | Cómo obtenerlo en macOS |
|------|------------------------|
| Lista de threads | `task_threads(task_for_pid(pid), ...)` |
| ID del thread | El propio `thread_act_t` devuelto |
| CPU usado por thread | `thread_info(thread, THREAD_BASIC_INFO)` campos `user_time`, `system_time` |
| Estado del thread | `thread_info()` campo `run_state` (TH_STATE_RUNNING, etc.) |
| Política de scheduling del thread | `thread_info(thread, THREAD_SCHED_POLICY_INFO)` |
| Nombre del thread (si lo tiene) | `pthread_getname_np()` (no expuesto a otros procesos fácilmente) |

> **Nota técnica**: en macOS, `task_for_pid()` requiere **permisos especiales**. Para procesos del mismo usuario suele funcionar, para otros procesos puede fallar con `KERN_FAILURE` por **SIP (System Integrity Protection)** y el **hardened runtime**. Si tu Python no tiene el entitlement `com.apple.security.cs.debugger`, podés acceder a tus propios procesos pero no a procesos de root. Documentá esa limitación en tu README.

### Señales

| Dato | Cómo obtenerlo en macOS |
|------|------------------------|
| Señales bloqueadas | `proc_pidinfo(pid, PROC_PIDTASKALLINFO, ...)` y dentro de `pti_pending_signals` |
| Señales pendientes (al proceso) | Misma estructura |
| Handlers registrados | macOS no expone esto al userland desde otro proceso (es info privada del proceso) — documentá la limitación |
| Pendientes al grupo | Similar al anterior |

> Esta es una de las **limitaciones reales** de macOS respecto a Linux. La vas a documentar en tu README como aprendizaje.

### Scheduling

| Dato | Cómo obtenerlo en macOS |
|------|------------------------|
| Nice (prioridad BSD) | `getpriority(PRIO_PROCESS, pid)` |
| Política de scheduling (POLICY_TIMESHARE, POLICY_RR, POLICY_FIFO) | `thread_info(thread, THREAD_SCHED_POLICY_INFO)` por thread |
| QoS class (Quality of Service, exclusivo de macOS) | `proc_pid_rusage()` campos `ri_interrupt_wkups`, `ri_billed_*_time` y categoría QoS |
| CPU Affinity | macOS **no** expone affinity a procesos no privilegiados. Documentar como limitación. |
| Voluntary / Involuntary context switches | `proc_pid_rusage()` campos `ri_syscalls_unix`, `ri_syscalls_mach`, `ri_csw` |
| utime / stime | `proc_pid_rusage()` |
| Sesión y grupo de procesos | `pbi_sessid`, `pbi_pgid` en `proc_bsdinfo` |

> **Diferencia conceptual**: macOS tiene **QoS classes** (USER_INTERACTIVE, USER_INITIATED, UTILITY, BACKGROUND) que reemplazan parcialmente la noción de "nice". Es un sistema más moderno donde el SO decide la prioridad real basándose en clases semánticas. Es interesante mostrarlo en tu monitor.

### Stats globales del sistema

| Dato | Cómo obtenerlo en macOS |
|------|------------------------|
| CPU global (user/system/idle) | `host_statistics(HOST_CPU_LOAD_INFO)` o `sysctl kern.cp_time` |
| Load average | `sysctl vm.loadavg` o `getloadavg(3)` |
| Cores | `sysctl hw.ncpu` y `hw.activecpu` |
| Memoria total | `sysctl hw.memsize` |
| Memoria libre/wired/active/inactive/compressed | `host_statistics(HOST_VM_INFO64)` o `vm_stat` |
| Swap usage | `sysctl vm.swapusage` |
| Procesos totales por estado | recorrer `proc_listpids()` |
| Boot time | `sysctl kern.boottime` |
| Uptime | calculado a partir del anterior |
| Top 3 por CPU / memoria | derivar del snapshot |

---

## Interfaz de usuario: 7 vistas alternables

La TUI siempre muestra una **lista de procesos** en la parte superior con datos resumidos, y un **panel de detalle** abajo que cambia según la vista activa.

### Vistas obligatorias

| # | Tecla | Vista | Intervalo default | Intervalo mínimo |
|---|-------|-------|-------------------|------------------|
| 1 | `1` / `r` | Resumen (estado, CPU, RSS, threads, comando) | 2s | 0.5s |
| 2 | `2` / `m` | Memoria (regiones, footprint, compressed, faults) | 3s | 1s |
| 3 | `3` / `f` | File descriptors (lista de FDs y sus destinos) | 5s | 2s |
| 4 | `4` / `t` | Threads (Mach threads con CPU%, política, run_state) | 2s | 0.5s |
| 5 | `5` / `s` | Señales (pending, mask, con notas de limitaciones de macOS) | 10s | 5s |
| 6 | `6` / `p` | Scheduling (nice, QoS class, política, ctx switches) | 10s | 5s |
| 7 | `7` / `g` | Sistema global (CPU, memoria, load, totales, vm_stat) | 2s | 1s |

### Keybindings obligatorios

Idénticos a la versión Linux:

| Tecla | Acción |
|-------|--------|
| `1`–`7` o `r/m/f/t/s/p/g` | Cambiar de vista |
| `↑` `↓` | Navegar por la lista de procesos |
| `Enter` | Pin del proceso seleccionado (no cambia aunque cambie el orden) |
| `/` | Filtrar por nombre de comando |
| `u` | Filtrar por usuario |
| `c` | Toggle ordenamiento (CPU% / RSS / PID) |
| `+` / `-` | Ajustar intervalo de la vista activa |
| `q` | Salir limpiamente |
| `h` / `?` | Ayuda |

### Refresh diferenciado por vista

Cada analizador (proceso independiente) tiene su propio intervalo, ajustable en tiempo real con `+` / `-` cuando esa vista está activa. La comunicación display → analizador para cambiar el intervalo debe usar **memoria compartida** (`multiprocessing.Value`).

---

## Señales del monitor

El monitor debe responder a las siguientes señales que recibe **él mismo**. Es el mismo conjunto que en Linux (las señales POSIX son comunes):

| Señal | Acción |
|-------|--------|
| **SIGINT** (Ctrl+C) | Shutdown limpio: termina hijos, vacía buffers, persiste log si corresponde |
| **SIGTERM** | Igual que SIGINT |
| **SIGHUP** | Recarga configuración (intervalos por vista, filtros default) desde `config.json` |
| **SIGUSR1** | Dump del snapshot actual a `dump_<timestamp>.json` |
| **SIGUSR2** | Toggle modo verbose |
| **SIGWINCH** | Repintar la pantalla — opcional |

Todos los handlers deben ser **async-signal-safe**. Usar el patrón **self-pipe** o `signal.set_wakeup_fd` si necesitás coordinar señales con loops principales.

---

## Requisitos técnicos

### Tecnologías y librerías

- **Python**: 3.11 o superior (idealmente instalado vía Homebrew o python.org, no el preinstalado del sistema)
- **Permitido**:
  - Stdlib completa (`os`, `multiprocessing`, `signal`, `threading`, `queue`, `time`, `json`, `re`, `ctypes`, `subprocess`, etc.)
  - `rich` o `curses` para la TUI
  - `prompt_toolkit` para entrada de teclado si lo necesitás
- **Prohibido**:
  - `psutil` y librerías equivalentes
  - Librerías de terceros que envuelvan `libproc`, `Mach` o `sysctl` por vos
  - Cualquier cosa que abstraiga la lectura del kernel — la idea es que vos llames a las APIs

### Ejecución

A diferencia de la versión Linux que se entrega en Docker, esta versión **corre directo en macOS**. Por eso:

- El repo debe incluir un `Makefile` o script `run.sh` con un comando único de arranque
- Documentar requisitos (versión de Python, librerías a instalar)
- `pip install -r requirements.txt` debe alcanzar para tener todo
- Probar en **macOS 13 (Ventura) o superior**. Documentar si funciona en versiones más viejas.

### Permisos y SIP

Documentá claramente en el README:

- Qué procesos puede inspeccionar tu monitor (los del mismo usuario sí, los de root probablemente no)
- Cómo correr el monitor con `sudo` si querés ver todos los procesos
- Si tuviste que firmar tu binario de Python con algún entitlement
- Las limitaciones de macOS comparadas con Linux (señales privadas, no hay affinity, etc.)

### Estructura sugerida del repo

```
.
├── README.md                 ← informe (ver más abajo)
├── dudas.md                  ← opcional, bienvenido
├── Makefile                  ← targets: run, install, clean
├── requirements.txt
├── config.json               ← config inicial (intervalos, defaults)
├── src/
│   ├── main.py
│   ├── recolector.py
│   ├── analizadores/
│   │   ├── resumen.py
│   │   ├── memoria.py
│   │   ├── fds.py
│   │   ├── threads.py
│   │   ├── senales.py
│   │   ├── scheduling.py
│   │   └── sistema.py
│   ├── display.py
│   ├── macos_api.py          ← wrappers de ctypes sobre libproc/Mach
│   └── senales.py            ← handlers
└── tests/                    ← opcional pero bienvenido
```

---

## Entregables

Idénticos a la versión Linux:

### 1. Repositorio público en GitHub

### 2. README.md con el informe

Mismas secciones que en la versión Linux, **más** una sección extra obligatoria:

#### Sección obligatoria adicional para macOS

**"Comparación con la versión Linux"**: explicá en uno o dos párrafos:
- Qué cosas son distintas en macOS respecto a `/proc`
- Qué información NO pudiste extraer en macOS y por qué
- Si alguna API te resultó particularmente interesante o difícil

Es la forma de **demostrar que entendiste la diferencia** entre familias UNIX, no solo que "copiaste código y anduvo".

### 3. dudas.md (opcional pero bienvenido)

---

## Criterios de evaluación

| Ítem | Peso |
|------|------|
| **Funcionalidad**: el monitor funciona, las 7 vistas se ven correctamente, la navegación responde | 30% |
| **Arquitectura**: multiproceso bien diseñado, IPC adecuado, sin race conditions visibles | 25% |
| **Señales**: las 5 señales (SIGINT/TERM/HUP/USR1/USR2) funcionan como se especifica | 10% |
| **Acceso al kernel**: todos los datos pedidos están y son correctos, llamadas a libproc/Mach/sysctl bien hechas | 15% |
| **README**: justifica decisiones, conecta con la teoría, **explica las diferencias con Linux** | 15% |
| **Código limpio**: estructura clara, manejo de errores razonable, PEP 8 razonable | 5% |
| **Bonus**: extensiones opcionales | +10% |

### Lo que vamos a preguntar al corregir

Vamos a hacerte preguntas conceptuales sobre tu propio código. Algunas posibles:

- "Mostrame dónde podría ocurrir una race condition en tu código. ¿Cómo la prevenís?"
- "¿Por qué tu agregador usa `Manager.dict` y no un `dict` regular?"
- "¿Cómo enumerás los threads de un proceso en macOS? ¿Por qué necesitás `task_for_pid()`?"
- "¿Qué es una QoS class? ¿Cómo se relaciona con el `nice` clásico?"
- "Diferencia entre el modelo de threads de Linux (LWPs) y el de macOS (Mach threads)."
- "Si tu monitor no puede ver las señales de otro proceso, ¿por qué? ¿Es una limitación del SO o de tu código?"
- "Si mato a uno de tus analizadores con `kill`, ¿qué pasa con el monitor?"

**Si no podés explicar tu propio código, no aprueba** — aunque el código funcione perfecto.

---

## Restricciones

- **No usar `psutil`** ni librerías equivalentes
- **No usar redes** (eso es 2do cuatrimestre)
- **No usar bases de datos** ni ORMs
- **No usar `asyncio`** (eso es 2C)

> A diferencia de la versión Linux, **sí se permite** llamar a herramientas nativas con `subprocess` (`ps`, `lsof`, `vm_stat`, `sysctl`, `vmmap`) porque en macOS hay info que es muy engorrosa de obtener vía ctypes y la idea no es que sufras con los detalles de C, sino que entiendas qué información expone el SO.

---

## Extensiones opcionales (bonus)

Si terminás lo obligatorio y querés sumar:

1. **Histórico**: guardar series temporales de CPU/MEM por proceso y mostrar mini-gráficos ASCII
2. **Detección de anomalías**: alertar cuando un proceso pega un pico, aparece un zombie, o consume demasiado
3. **Modo daemon**: poder correr el monitor sin TUI, solo loggeando a archivo
4. **Exportación**: guardar snapshots periódicos a JSON o CSV
5. **Vista de jerarquía**: mostrar el árbol de procesos tipo `pstree`
6. **Tests**: tests unitarios del parseo, idealmente con archivos de muestra
7. **Vista QoS específica de macOS**: explorar las QoS classes, mostrar cuánto tiempo cada proceso pasó en cada clase
8. **Detección de procesos firmados**: usar `csops` o similar para mostrar quién firmó cada ejecutable

Cada extensión bien hecha vale hasta +2%, máximo +10% total.

---

## Cómo trabajar con IA

Te recomendamos fuertemente usar una IA como tutor durante el desarrollo. Tenemos un prompt diseñado especialmente para que la IA te enseñe en vez de hacerte el trabajo:

→ ver `prompt_tutor_ia.md` en esta misma carpeta

El prompt vale para las dos versiones (Linux y macOS).

---

## Material de referencia

### Del curso

- Clase 3: Procesos - Fundamentos (anatomía)
- Clase 4: fork, exec, wait (zombies, COW)
- Clase 5: Pipes (file descriptors, IPC básico)
- Clase 6: Señales (handlers, máscaras, async-signal-safe, self-pipe)
- Clase 7: mmap y memoria compartida
- Clase 8: Multiprocessing fundamentos (`Process`, `Queue`, `Pipe`, daemons)
- Clase 9: Multiprocessing avanzado (`Pool`, `Manager`, `Value`, `Array`)
- Clase 10: Threading (GIL)

### Externa

- **[libproc.h header](https://github.com/apple-oss-distributions/xnu/blob/main/libsyscall/wrappers/libproc/libproc.h)** — todas las funciones disponibles
- **[Apple Developer: Activity Monitor](https://developer.apple.com/library/archive/documentation/Performance/Conceptual/PerformanceOverview/index.html)** — conceptos generales
- **[Mach IPC and Mach Threads (Apple Open Source)](https://opensource.apple.com/source/xnu/xnu-7195.81.3/osfmk/man/)** — APIs Mach
- **man pages**:
  - `man 3 proc_pidinfo`
  - `man 3 sysctl`
  - `man 3 host_statistics`
  - `man 8 ps`
  - `man 8 lsof`
  - `man 1 vm_stat`
  - `man 1 vmmap`
- **Tutoriales de ctypes**: [Python docs - ctypes](https://docs.python.org/3/library/ctypes.html)

### Comandos útiles para explorar

```bash
ps -eM                              # procesos con threads visibles
ps -o pid,ppid,state,nice,user,comm -A
lsof -p $$                          # FDs de tu shell
vmmap $$ | head -50                 # mapa de memoria de tu shell
sysctl hw.ncpu hw.memsize           # info del hardware
sysctl kern.cp_time                 # CPU tiempo total
vm_stat                             # estadísticas de memoria
htop                                # para comparar con tu monitor
top                                 # nativo de macOS
```

### Ejemplo de wrapper ctypes mínimo (para arrancar)

Esto NO es la solución, es solo un punto de partida para que veas la sintaxis. Pedile a tu tutor IA que te ayude a construir wrappers más completos.

```python
import ctypes
import ctypes.util

libc = ctypes.CDLL(ctypes.util.find_library("c"))

# proc_listpids
PROC_ALL_PIDS = 1

def listar_pids():
    # Primera llamada: averiguar tamaño
    libc.proc_listpids.restype = ctypes.c_int
    n = libc.proc_listpids(PROC_ALL_PIDS, 0, None, 0)
    if n <= 0:
        return []
    # Segunda llamada: pedir los PIDs
    pids = (ctypes.c_int * (n // 4))()
    libc.proc_listpids(PROC_ALL_PIDS, 0, pids, n)
    return [p for p in pids if p != 0]

print(listar_pids()[:10])  # primeros 10 PIDs del sistema
```

---

## Cronograma sugerido

| Semana | Tarea sugerida |
|--------|----------------|
| Semana 1 (después de clase 5: Pipes) | Recolector que liste procesos usando `proc_listpids` o `ps` |
| Semana 2 (después de clase 6: Señales) | Vistas Resumen, Memoria y Sistema. Manejo básico de señales |
| Semana 3 (después de clase 7: mmap) | Memoria compartida con `Manager` + agregador |
| Semana 4 (después de clase 8-9: Multiprocessing) | Los 7 analizadores corriendo en paralelo |
| Semana 5 (después de clase 10: Threading) | Vista Threads (con Mach threads), intervalos diferenciados |
| Semana 6 (después de clase 11: Sincronización) | Polishing, README con comparación Linux/macOS, dudas, entrega |

---

## Una nota sobre por qué hay dos versiones

Esta materia es de **sistemas operativos**, no de "Linux". Aunque la mayoría del material toma Linux como referencia (por ser más limpio pedagógicamente con `/proc`), entender que **macOS, FreeBSD, Solaris** y otros UNIX tienen modelos distintos es **parte de la formación**.

Si elegís esta versión, vas a:
- Tocar APIs más cercanas al kernel (no archivos, sino syscalls)
- Aprender ctypes y la convención de llamadas C
- Conocer las **QoS classes**, una contribución moderna de Apple a la teoría de scheduling
- Tener que documentar **limitaciones reales** del SO, lo cual es muy formativo

Es **un poco más difícil** que la versión Linux, pero la recompensa es entender más profundamente cómo varía la "filosofía UNIX" entre familias.

---

*Trabajo Práctico Nº 1 (versión macOS) — Computación II — 2026*
