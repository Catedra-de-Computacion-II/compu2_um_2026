# Trabajo Práctico Nº 1: Monitor de Procesos y Threads

**Computación II — Universidad de Mendoza — 2026**

---

## Información general

| | |
|-|-|
| **Entrega** | Clase 11 (02/06/2026) al final de la clase de Sincronización II |
| **Modalidad** | Individual |
| **Plataforma** | Linux (en Docker) |
| **Lenguaje** | Python 3.11+ |
| **Entrega** | Repositorio público en GitHub |

---

## Objetivos pedagógicos

Al terminar este TP deberías poder:

1. **Inspeccionar un proceso de Linux desde fuera**, leyendo `/proc` para extraer su estado, memoria, FDs, threads, señales y configuración de scheduling.
2. **Diseñar un sistema multiproceso** que distribuye trabajo entre componentes que se ejecutan en paralelo.
3. **Comunicar procesos** usando `Queue`, `Pipe` y memoria compartida (`Manager`, `Value`, `Array`).
4. **Manejar señales** para implementar shutdown limpio, reload y dump on-demand.
5. **Identificar y resolver race conditions** con primitivas de sincronización.
6. **Conectar la teoría de la materia** (procesos, threads, scheduler, GIL, IPC) con lo que ves en un sistema vivo.

---

## Descripción del sistema a construir

Vas a desarrollar un **monitor del sistema en tiempo real**, parecido a `htop` pero con énfasis en mostrar la **anatomía interna** de cada proceso y sus threads. La información se extrae leyendo `/proc` directamente (no se permite `psutil` ni equivalentes).

El monitor es un **sistema multiproceso**: un recolector central lee `/proc`, distribuye el trabajo entre analizadores especializados que corren en paralelo, un agregador mantiene el snapshot global en memoria compartida, y una interfaz de texto (TUI) muestra los datos al usuario con múltiples vistas alternables.

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
| **Recolector** | Lista procesos vía `/proc`, distribuye trabajo a los analizadores |
| **7 analizadores** | Cada uno extrae una dimensión específica (resumen, memoria, FDs, threads, señales, scheduling, sistema) |
| **Agregador** | Mantiene el snapshot global en memoria compartida |
| **Display (TUI)** | Renderiza la vista activa según los datos del snapshot |
| **Manejador de señales** | Captura las señales que recibe el monitor y dispara acciones |

Cada analizador es un **proceso independiente** (no thread), con su propio intervalo de refresco. La comunicación entre componentes debe usar primitivas de `multiprocessing` (`Queue`, `Pipe`, `Manager`, `Value`, `Array`).

> **Nota sobre threads**: podés usar threads internamente dentro del proceso de display para la entrada de teclado (no es obligatorio). Pero la arquitectura principal debe ser **multiproceso**, no multithread.

---

## Datos a mostrar por proceso

El TP requiere extraer y mostrar los siguientes datos. Todos salen de `/proc/<pid>/...`:

### Datos básicos (vista Resumen)

| Dato | Fuente |
|------|--------|
| PID | nombre de la carpeta `/proc/<pid>/` |
| PPID | `/proc/<pid>/status: PPid` |
| UID/GID + usuario | `/proc/<pid>/status: Uid, Gid` |
| Estado (R/S/D/T/Z) | `/proc/<pid>/stat` campo 3 |
| Comando completo | `/proc/<pid>/cmdline` |
| CPU% | calcular delta de jiffies entre lecturas (`/proc/<pid>/stat`, campos 14-15) |
| Cantidad de threads | `/proc/<pid>/status: Threads` |

### Memoria

| Dato | Fuente |
|------|--------|
| VmSize, VmRSS, VmData, VmStk, VmExe, VmLib | `/proc/<pid>/status` |
| VmHWM (high water mark de RSS) | `/proc/<pid>/status` |
| VmSwap | `/proc/<pid>/status` |
| Minor / Major page faults | `/proc/<pid>/stat` campos 10-13 |
| Segmentos agrupados (text/data/heap/stack/shared) | `/proc/<pid>/maps` agrupando por permisos y `[heap]`, `[stack]` |

### File Descriptors

| Dato | Fuente |
|------|--------|
| Lista de FDs abiertos | `os.listdir(f'/proc/<pid>/fd')` |
| Destino de cada FD | `os.readlink(f'/proc/<pid>/fd/<n>')` |
| Tipo (tty/socket/pipe/file/...) | Inferir del destino del symlink |

### Threads (LWPs)

| Dato | Fuente |
|------|--------|
| Lista de threads del proceso | `os.listdir(f'/proc/<pid>/task')` |
| Estado de cada thread | `/proc/<pid>/task/<tid>/stat` |
| CPU usado por thread | `/proc/<pid>/task/<tid>/stat` (delta de jiffies) |
| Nombre del thread | `/proc/<pid>/task/<tid>/comm` |
| Context switches | `/proc/<pid>/task/<tid>/status` |

### Señales

| Dato | Fuente |
|------|--------|
| SigBlk (bloqueadas) | `/proc/<pid>/status: SigBlk` |
| SigIgn (ignoradas) | `/proc/<pid>/status: SigIgn` |
| SigCgt (con handler propio) | `/proc/<pid>/status: SigCgt` |
| SigPnd (pendientes proceso) | `/proc/<pid>/status: SigPnd` |
| ShdPnd (pendientes grupo) | `/proc/<pid>/status: ShdPnd` |

Estos son **máscaras hexadecimales de 64 bits** donde cada bit representa una señal. Hay que decodificarlas a nombres legibles (SIGTERM, SIGINT, etc.).

### Scheduling

| Dato | Fuente |
|------|--------|
| Nice | `/proc/<pid>/stat` campo 19 o `status: Nice` |
| Priority | `/proc/<pid>/stat` campo 18 |
| Scheduling Policy (OTHER/FIFO/RR/BATCH/IDLE) | `/proc/<pid>/stat` campo 41 o `/proc/<pid>/sched` |
| RT Priority | `/proc/<pid>/stat` campo 40 |
| CPU Affinity | `/proc/<pid>/status: Cpus_allowed_list` |
| Voluntary / Involuntary context switches | `/proc/<pid>/status: voluntary_ctxt_switches`, `nonvoluntary_ctxt_switches` |
| utime / stime | `/proc/<pid>/stat` campos 14-15 |
| Sesión (SID) y grupo de procesos (PGID) | `/proc/<pid>/stat` campos 6-7 |

### Stats globales del sistema

| Dato | Fuente |
|------|--------|
| CPU global (user/system/idle/iowait %) | `/proc/stat` línea `cpu` (delta) |
| Load average | `/proc/loadavg` |
| Memoria total/libre/buffers/cached/swap | `/proc/meminfo` |
| Procesos totales, por estado, threads totales, zombies | recorrer `/proc/<pid>/stat` |
| Boot time, uptime | `/proc/stat` línea `btime`, `/proc/uptime` |
| Top 3 por CPU y por memoria | derivar del snapshot |

---

## Interfaz de usuario: 7 vistas alternables

La TUI siempre muestra una **lista de procesos** en la parte superior con datos resumidos, y un **panel de detalle** abajo que cambia según la vista activa.

### Vistas obligatorias

| # | Tecla | Vista | Intervalo default | Intervalo mínimo |
|---|-------|-------|-------------------|------------------|
| 1 | `1` / `r` | Resumen (estado, CPU, RSS, threads, comando) | 2s | 0.5s |
| 2 | `2` / `m` | Memoria (segmentos, faults, swap) | 3s | 1s |
| 3 | `3` / `f` | File descriptors (lista de FDs y sus destinos) | 5s | 2s |
| 4 | `4` / `t` | Threads (lista de LWPs con CPU% y estado) | 2s | 0.5s |
| 5 | `5` / `s` | Señales (bloqueadas, ignoradas, con handler, pendientes) | 10s | 5s |
| 6 | `6` / `p` | Scheduling (nice, priority, policy, affinity, ctx switches) | 10s | 5s |
| 7 | `7` / `g` | Sistema global (CPU, memoria, load, totales) | 2s | 1s |

### Keybindings obligatorios

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

El monitor debe responder a las siguientes señales que recibe **él mismo**:

| Señal | Acción |
|-------|--------|
| **SIGINT** (Ctrl+C) | Shutdown limpio: termina hijos, vacía buffers, persiste log si corresponde |
| **SIGTERM** | Igual que SIGINT |
| **SIGHUP** | Recarga configuración (intervalos por vista, filtros default) desde un archivo `config.json` |
| **SIGUSR1** | Dump del snapshot actual a `dump_<timestamp>.json` |
| **SIGUSR2** | Toggle modo verbose (más detalle en cada proceso, ej: más FDs visibles) |
| **SIGWINCH** | Repintar la pantalla (terminal redimensionada) — opcional pero recomendado |

Todos los handlers deben ser **async-signal-safe**. Usar el patrón **self-pipe** o `signal.set_wakeup_fd` si necesitás coordinar señales con loops principales (lo vimos en clase 6).

---

## Requisitos técnicos

### Tecnologías y librerías

- **Python**: 3.11 o superior
- **Permitido**:
  - Stdlib completa (`os`, `multiprocessing`, `signal`, `threading`, `queue`, `time`, `json`, `re`, etc.)
  - `rich` o `curses` para la TUI (la que prefieras)
  - `prompt_toolkit` solo para entrada de teclado si lo necesitás
- **Prohibido**:
  - `psutil` y librerías equivalentes que hagan el trabajo de leer `/proc` por vos
  - Cualquier herramienta que abstraiga el acceso al kernel (toda la gracia es que vos lo leas a mano)

### Ejecución

El TP debe correr dentro de un contenedor Docker (`linux/amd64` o `linux/arm64`). El repo debe incluir:

- `Dockerfile` y `docker-compose.yml`
- Un comando único de levantar todo: `docker compose up --build`
- El contenedor debe ser interactivo (`tty: true`, `stdin_open: true`) para la TUI

### Estructura sugerida del repo

```
.
├── README.md                 ← informe (ver más abajo)
├── dudas.md                  ← opcional, bienvenido
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── config.json               ← config inicial (intervalos, defaults)
├── src/
│   ├── main.py               ← entry point
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
│   ├── procfs.py             ← helpers para parsear /proc
│   └── senales.py            ← handlers
└── tests/                    ← opcional pero bienvenido
```

---

## Entregables

### 1. Repositorio público en GitHub

Con todo el código y los archivos de configuración. Tiene que poder clonarse y correr con `docker compose up --build` sin más pasos.

### 2. README.md con el informe

El README es **central a la evaluación**. Debe incluir:

#### Secciones obligatorias

1. **Descripción general**: qué hace el monitor y cómo se usa
2. **Diagrama de arquitectura**: procesos y comunicación entre ellos (puede ser ASCII o imagen)
3. **Decisiones de diseño** argumentadas:
   - ¿Por qué elegiste tal mecanismo de IPC y no otro?
   - ¿Por qué `Manager` y no `Value`/`Array` para algunas cosas?
   - ¿Cómo manejaste las race conditions?
   - ¿Por qué los intervalos elegidos por defecto?
4. **Conceptos del curso aplicados**: relacionar partes específicas del código con clases. Ejemplo:
   > "Para detectar zombies en la vista Sistema, uso el campo `State` de `/proc/<pid>/stat`. Este concepto se vio en clase 4 (fork, exec, wait) cuando aprendimos que un zombie es un proceso terminado cuyo padre todavía no llamó a `wait()`."
5. **Limitaciones conocidas**: cosas que sabés que tu programa NO hace bien, o que tienen edge cases
6. **Cómo correr y testear**: instrucciones precisas

#### Secciones recomendadas

7. **Capturas de pantalla o GIF** del monitor funcionando
8. **Decisiones sobre la TUI** (por qué `rich` o `curses`, layout, etc.)
9. **Lo que aprendiste**: 2-3 párrafos personales sobre lo que descubriste haciendo el TP

### 3. dudas.md (opcional pero bienvenido)

Si llevaste un archivo con dudas que te quedaron sin resolver, **inclúilo en el repo**. No penaliza, al contrario: muestra honestidad intelectual.

---

## Criterios de evaluación

| Ítem | Peso |
|------|------|
| **Funcionalidad**: el monitor funciona, las 7 vistas se ven correctamente, la navegación responde | 30% |
| **Arquitectura**: multiproceso bien diseñado, IPC adecuado, sin race conditions visibles | 25% |
| **Señales**: las 5 señales (SIGINT/TERM/HUP/USR1/USR2) funcionan como se especifica | 10% |
| **Lectura de /proc**: todos los datos pedidos están y son correctos | 15% |
| **README**: justifica decisiones, conecta con la teoría, refleja entendimiento | 15% |
| **Código limpio**: estructura clara, manejo de errores razonable, PEP 8 razonable | 5% |
| **Bonus**: extensiones opcionales (ver abajo) | +10% |

### Lo que vamos a preguntar al corregir

Vamos a hacerte **preguntas conceptuales sobre tu propio código**. Algunas posibles:

- "Mostrame dónde podría ocurrir una race condition en tu código. ¿Cómo la prevenís?"
- "¿Por qué tu agregador usa `Manager.dict` y no un `dict` regular?"
- "Si yo lanzo tu monitor y abro 100 terminales abriendo procesos, ¿qué pasa? ¿Tu monitor escala?"
- "¿Cómo decodificás `SigBlk` para mostrar `SIGINT` legible?"
- "¿Qué es un context switch involuntario y por qué los procesos CPU-bound tienen muchos?"
- "Si mato a uno de tus analizadores con `kill`, ¿qué pasa con el monitor?"
- "Diferencia entre PID y TID en `/proc`. ¿Cómo se ve en tu output?"

**Si no podés explicar tu propio código, no aprueba** — aunque el código funcione perfecto.

---

## Restricciones

- **No usar `psutil`** ni librerías que hagan el trabajo de parsear `/proc` por vos
- **No usar redes** (eso es 2do cuatrimestre)
- **No usar bases de datos** ni ORMs
- **No usar `subprocess` para correr `ps`, `top` u otras herramientas** y parsear su output — la idea es leer `/proc` directamente
- **No es necesario** que funcione en macOS o Windows (Linux only, lo cual el Docker resuelve)
- **No usar `asyncio`** (eso es 2C)

---

## Extensiones opcionales (bonus)

Si terminás lo obligatorio y querés sumar:

1. **Histórico**: guardar series temporales de CPU/MEM por proceso y mostrar mini-gráficos ASCII
2. **Detección de anomalías**: alertar cuando un proceso pega un pico, aparece un zombie, o consume demasiado
3. **Modo daemon**: poder correr el monitor sin TUI, sólo loggeando a archivo
4. **Exportación**: guardar snapshots periódicos a JSON o CSV
5. **Vista de jerarquía**: mostrar el árbol de procesos tipo `pstree`
6. **Tests**: tests unitarios del parseo de `/proc`, idealmente con archivos de muestra
7. **Mostrar señales que se reciben**: si tu monitor recibe SIGUSR2, mostrarlo en pantalla
8. **Comparativa cross-proceso**: seleccionar 2-3 procesos y compararlos lado a lado

Cada extensión bien hecha vale hasta +2%, máximo +10% total. Pero **siempre después de que lo obligatorio esté sólido**.

---

## Cómo trabajar con IA

Te recomendamos fuertemente usar una IA como tutor durante el desarrollo. Tenemos un prompt diseñado especialmente para que la IA te enseñe en vez de hacerte el trabajo:

→ ver `prompt_tutor_ia.md` en esta misma carpeta

No nos importa quién escriba el código. Nos importa que **vos entiendas qué hace y por qué**. Las preguntas al corregir van a evaluar exactamente eso.

---

## Material de referencia

### Del curso

- Clase 3: Procesos - Fundamentos (anatomía, `/proc`, memoria virtual)
- Clase 4: fork, exec, wait (zombies, COW)
- Clase 5: Pipes (file descriptors, IPC básico)
- Clase 6: Señales (handlers, máscaras, async-signal-safe, self-pipe)
- Clase 7: mmap y memoria compartida
- Clase 8: Multiprocessing fundamentos (`Process`, `Queue`, `Pipe`, daemons)
- Clase 9: Multiprocessing avanzado (`Pool`, `Manager`, `Value`, `Array`)
- Clase 10: Threading (GIL, threads como LWPs en `/proc/<pid>/task`)

### Externa

- [proc(5) — man page](https://man7.org/linux/man-pages/man5/proc.5.html) — la biblia del filesystem `/proc`
- [Python multiprocessing docs](https://docs.python.org/3/library/multiprocessing.html)
- [Python signal docs](https://docs.python.org/3/library/signal.html)
- [Rich documentation](https://rich.readthedocs.io/) si usás `rich` para la TUI
- [Curses HOWTO](https://docs.python.org/3/howto/curses.html) si preferís `curses`

### Comandos útiles para explorar

```bash
ps -eLf                          # lista todos los procesos y threads
ps -o pid,ppid,state,nice,pri,comm -e
cat /proc/$$/status              # tu shell
cat /proc/$$/stat
ls -l /proc/$$/fd/
cat /proc/$$/maps | head
cat /proc/loadavg
cat /proc/meminfo | head
chrt -p $$                       # política de scheduling de tu shell
htop                             # para comparar con tu monitor
```

---

## Cronograma sugerido

| Semana | Tarea sugerida |
|--------|----------------|
| Semana 1 (después de clase 5: Pipes) | Recolector que liste procesos y lea `/proc/<pid>/stat` |
| Semana 2 (después de clase 6: Señales) | Vistas Resumen, Memoria y Sistema. Manejo básico de señales |
| Semana 3 (después de clase 7: mmap) | Memoria compartida con `Manager` + agregador |
| Semana 4 (después de clase 8-9: Multiprocessing) | Los 7 analizadores corriendo en paralelo |
| Semana 5 (después de clase 10: Threading) | Vista Threads, intervalos diferenciados |
| Semana 6 (después de clase 11: Sincronización) | Polishing, README, dudas, entrega |

No es obligatorio seguir este cronograma, pero te puede servir de guía.

---

*Trabajo Práctico Nº 1 — Computación II — 2026*
