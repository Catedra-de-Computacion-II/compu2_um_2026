# Clase 3: Procesos - Fundamentos

## Introducción: ¿Qué es un proceso?

Cuando ejecutás un programa, el sistema operativo crea algo llamado **proceso**. Pero un proceso no es simplemente "un programa corriendo" - es mucho más que eso. Un proceso es una instancia de un programa en ejecución junto con todo su contexto: la memoria que usa, los archivos que tiene abiertos, su estado de ejecución, y su relación con otros procesos.

Pensalo así: si el programa es la receta, el proceso es la acción de cocinar. Podés tener la misma receta (programa) pero cocinarla múltiples veces simultáneamente (múltiples procesos). Cada vez que cocinás, tenés tus propios ingredientes (memoria), tus propias ollas (file descriptors), y tu propio progreso (program counter).

Esta distinción es fundamental para entender sistemas operativos. Un programa es pasivo - bytes almacenados en disco. Un proceso es activo - una entidad viva que el kernel gestiona, le asigna CPU, y eventualmente termina.

---

## El modelo de procesos en UNIX

### Una jerarquía familiar

UNIX organiza los procesos en una estructura de árbol. Cada proceso (excepto el primero) tiene un padre que lo creó. Este modelo jerárquico no es un accidente de diseño - refleja cómo los programas naturalmente delegan trabajo a subprocesos.

Cuando arranca tu sistema Linux, el kernel crea el proceso con PID 1, tradicionalmente llamado `init` (hoy es `systemd` en la mayoría de distribuciones). Este proceso es el ancestro de todos los demás. Cada vez que abrís una terminal, `systemd` (o algún descendiente suyo) crea un proceso shell. Cuando en ese shell escribís un comando, el shell crea un proceso hijo para ejecutarlo.

```bash
# Ver el árbol de procesos
pstree -p

# Salida típica (simplificada):
# systemd(1)─┬─sshd(1234)───sshd(5678)───bash(5680)───python(6789)
#            ├─dockerd(2345)───containerd(2346)
#            └─nginx(3456)─┬─nginx(3457)
#                          └─nginx(3458)
```

Esta jerarquía tiene consecuencias importantes. Cuando un proceso padre termina, sus hijos quedan "huérfanos" y son adoptados por init/systemd. Cuando un hijo termina pero su padre no recoge su estado de salida, el hijo queda como "zombie" - un proceso muerto que aún ocupa una entrada en la tabla de procesos. Vamos a profundizar estos casos en la próxima clase.

### Anatomía de un proceso

Cada proceso en Linux tiene varios componentes esenciales:

**PID (Process ID):** Un número único que identifica al proceso. Los PIDs se asignan secuencialmente y eventualmente se reciclan cuando se agotan.

**PPID (Parent Process ID):** El PID del proceso padre. Esto forma la cadena jerárquica.

**Estado:** Running (ejecutándose o listo para ejecutar), Sleeping (esperando algo), Stopped (detenido por una señal), Zombie (terminado pero no recogido por el padre).

**Memoria virtual:** Cada proceso tiene su propio espacio de direcciones virtuales, completamente aislado de otros procesos. El kernel y la MMU (Memory Management Unit) del procesador se encargan de traducir las direcciones virtuales que usa el programa a direcciones físicas reales en la RAM. Esto significa que dos procesos pueden usar la "misma" dirección de memoria virtual sin conflicto — cada uno apunta a una ubicación física distinta.

El espacio de memoria de un proceso se organiza en segmentos con propósitos específicos:

```
Direcciones altas
┌──────────────────────┐
│       Stack          │  Crece hacia abajo
│                      │
├──────────────────────┤
│         ↕            │  Espacio libre
├──────────────────────┤
│       Heap           │  Crece hacia arriba
├──────────────────────┤
│       BSS            │
├──────────────────────┤
│       Data           │
├──────────────────────┤
│       Text           │
└──────────────────────┘
Direcciones bajas
```

- **Text segment (código):** Contiene las instrucciones del programa compilado. Es de **solo lectura** — si un proceso intenta escribir acá, el kernel lo mata con una señal SIGSEGV (segmentation fault). Es compartible: si corrés 10 veces el mismo programa, las 10 instancias pueden compartir la misma copia del text segment en memoria física.

- **Data segment (datos inicializados):** Almacena las variables globales y estáticas que tienen un valor inicial asignado en el código. Por ejemplo, si en C escribís `int contador = 42;`, esa variable vive acá. El valor inicial se copia del ejecutable al cargar el programa.

- **BSS (Block Started by Symbol):** Almacena las variables globales y estáticas que **no** fueron inicializadas explícitamente (o se inicializaron a cero). El nombre viene del ensamblador de los años '50 y quedó por tradición. La diferencia con Data es que BSS no ocupa espacio en el archivo ejecutable — el kernel simplemente reserva la memoria y la llena de ceros al cargar el proceso. Si declarás `int tabla[1000000];` sin inicializar, no vas a tener un ejecutable de 4MB; el SO sabe que necesita reservar ese espacio y ponerlo en cero.

- **Heap (montículo):** Memoria dinámica que el programa solicita en tiempo de ejecución. En C se obtiene con `malloc()`/`free()`, en Python el intérprete la gestiona internamente para crear objetos. Crece hacia direcciones altas. Si se queda sin espacio, el proceso puede pedir más al kernel (vía `brk()` o `mmap()`).

- **Stack (pila):** Almacena las variables locales de funciones, los argumentos pasados a funciones, y las direcciones de retorno (para saber adónde volver cuando una función termina). Crece hacia direcciones bajas — es decir, en dirección opuesta al heap. Cada vez que llamás a una función se apila un **stack frame**; cuando la función retorna, ese frame se desapila. Si se crece demasiado (por ejemplo, recursión infinita), el proceso recibe un stack overflow.

El hecho de que heap y stack crezcan en direcciones opuestas es un diseño deliberado: aprovechan el mismo espacio libre desde extremos opuestos.

Podés ver el mapa de memoria de cualquier proceso en Linux:

```bash
# Ver el layout de memoria de un proceso
cat /proc/<pid>/maps

# Ejemplo práctico en Docker:
python3 -c "
import os
print(f'Mi PID es {os.getpid()}')
input('Presioná Enter para salir...')
" &
cat /proc/$!/maps
```

**File descriptors:** Una tabla de archivos abiertos. Por defecto, cada proceso hereda tres: stdin (0), stdout (1), stderr (2).

**Credenciales:** UID y GID que determinan los permisos del proceso.

---

## Conceptos clave para recordar

1. **Proceso vs Programa:** El programa es código en disco, el proceso es ejecución activa con su contexto.

2. **Jerarquía de procesos:** Todo proceso tiene un padre. init/systemd es el ancestro de todos.

3. **Memoria virtual aislada:** Cada proceso tiene su propio espacio de direcciones, organizado en text/data/BSS/heap/stack.

4. **File descriptors y credenciales:** Otros componentes esenciales del contexto de un proceso.

---

## Preparación para la próxima clase

En la **clase 4 (Procesos: fork, exec, wait)** vamos a ver cómo crear procesos en Linux con las llamadas al sistema `fork()`, `exec()` y `wait()`. Veremos:

- Cómo `fork()` duplica un proceso (y por qué eso es elegante y eficiente con Copy-on-Write)
- Cómo `exec()` reemplaza el programa de un proceso
- Cómo `wait()` recoge el estado de salida de los hijos y evita zombies
- El patrón fork-exec que está en la base de cómo funciona un shell

---

*Computación II - 2026 - Clase 3*
