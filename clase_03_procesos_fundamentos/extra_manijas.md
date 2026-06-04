# Clase 3: Procesos - Fundamentos — Extra Manijas

> Material opcional de profundización.

---

## 1. La estructura `task_struct` del kernel

Cada proceso en Linux está representado internamente por una estructura llamada `task_struct`. Es una estructura masiva (más de 1000 campos) que contiene todo lo que el kernel necesita saber sobre un proceso:

```c
struct task_struct {
    pid_t                pid;          // PID
    pid_t                tgid;         // Thread group ID
    struct task_struct  *parent;       // Padre
    struct list_head     children;     // Hijos
    struct mm_struct    *mm;           // Memoria
    struct files_struct *files;        // File descriptors
    long                 state;        // Estado (running, sleeping, etc.)
    struct cred         *cred;         // UID, GID
    char                 comm[16];     // Nombre del programa
    // ... muchísimos más campos
};
```

El kernel mantiene una lista enlazada de todas las `task_struct` activas. Cuando hacés `ps`, está leyendo (vía `/proc`) esa información.

Podés ver muchos campos en `/proc/<pid>/status`:

```bash
cat /proc/$$/status | head -20
```

---

## 2. Estados de un proceso en detalle

Los estados que ves en `ps -o stat` son letras:

| Letra | Significado |
|-------|-------------|
| R | Running o runnable |
| S | Sleeping (interrumpible) |
| D | Sleeping (uninterrumpible, esperando I/O) |
| T | Stopped (por señal o ptrace) |
| Z | Zombie (terminado, no recogido) |
| X | Dead (no debería verse) |
| I | Idle (kernel thread idle) |

Estados modificadores que pueden seguir a la letra principal:

| Modificador | Significado |
|-------------|-------------|
| `<` | Alta prioridad |
| `N` | Baja prioridad (nice) |
| `L` | Páginas bloqueadas en memoria |
| `s` | Session leader |
| `l` | Multi-threaded |
| `+` | En foreground group |

---

## 3. Memoria virtual y paginación

El concepto de memoria virtual que vimos en clase es solo la punta del iceberg. El kernel divide la memoria en **páginas** (típicamente 4KB) y mantiene una **tabla de páginas** por proceso que mapea páginas virtuales a páginas físicas.

```
Proceso A                        RAM física
0x1000  ──>  tabla páginas A  ──> Frame 7
                                  Frame 19
                                  Frame 42 (compartido)

Proceso B                        
0x1000  ──>  tabla páginas B  ──> Frame 42 (compartido con A)
                                  Frame 88
```

Cuando un proceso accede a una dirección virtual:
1. La MMU consulta la tabla de páginas
2. Si está mapeada → traduce a física, lee/escribe directo
3. Si NO está mapeada → page fault → el kernel decide (cargar de disco, asignar nueva, matar al proceso si es ilegal)

Para ver estadísticas de page faults:
```bash
ps -o pid,min_flt,maj_flt,comm -p $$
# min_flt: faults menores (sin disco)
# maj_flt: faults mayores (con I/O de disco)
```

---

## 4. cgroups y namespaces (lo que hace Docker)

Linux moderno tiene dos mecanismos clave que permiten contenedores:

### Namespaces

Aislamiento del "qué ve" un proceso:
- **PID namespace**: el proceso cree que es PID 1 y solo ve los procesos de su namespace
- **Network namespace**: red propia, interfaces propias
- **Mount namespace**: sistema de archivos propio
- **UTS namespace**: hostname propio
- **IPC namespace**: shared memory, queues separadas
- **User namespace**: UIDs propios

Verlos:
```bash
ls -l /proc/$$/ns/
```

### cgroups (Control Groups)

Limitación de **cuánto** puede consumir un proceso:
- CPU (cuotas, prioridades)
- Memoria (límite máximo)
- I/O de disco
- Red (con ayuda de tc)

Ver cgroups del proceso actual:
```bash
cat /proc/$$/cgroup
```

Docker, Kubernetes, systemd, todos usan cgroups + namespaces.

---

## 5. ASLR (Address Space Layout Randomization)

Si corrés dos veces el mismo programa y mirás `/proc/<pid>/maps`, vas a ver que **las direcciones cambian** cada vez:

```bash
python3 -c "import time; print(open('/proc/self/maps').read()[:200])"
# corré dos veces y compará
```

Es **ASLR** — el kernel aleatoriza las direcciones donde carga el stack, heap y librerías. Es una defensa contra exploits de seguridad: si no sabés dónde está una función, no podés saltar a ella con un return-oriented programming.

Podés ver si está activo:
```bash
cat /proc/sys/kernel/randomize_va_space
# 0 = off, 1 = parcial, 2 = full (default en Linux moderno)
```

---

## 6. Lecturas recomendadas

- **Advanced Programming in the UNIX Environment** (Stevens & Rago) — capítulo 8
- **The Linux Programming Interface** (Kerrisk) — capítulos 6-7
- **Operating Systems: Three Easy Pieces** (Arpaci-Dusseau) — capítulos 4-6 (gratis online)
- **man proc(5)** — la doc completa del sistema de archivos `/proc`

---

*Computación II - 2026 - Clase 3 — Material opcional*
