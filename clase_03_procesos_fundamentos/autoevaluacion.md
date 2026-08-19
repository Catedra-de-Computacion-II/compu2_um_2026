# Clase 3: Procesos - Fundamentos — Autoevaluación

> Cubre el material de fundamentos: anatomía del proceso, jerarquía, memoria virtual, file descriptors.
> Las preguntas sobre `fork()`, `exec()` y `wait()` están en la autoevaluación de **clase 4**.

---

## Preguntas

**1.** ¿Cuál es la diferencia fundamental entre un programa y un proceso?

a) No hay diferencia, son lo mismo
b) El programa siempre tiene PID y el proceso no
c) El programa está en disco, el proceso es la instancia en ejecución
d) Un proceso es más grande

**2.** ¿Qué proceso es el ancestro de todos los demás en Linux?

a) `root`
b) `kernel`
c) `bash`
d) `init` o `systemd` (PID 1)

**3.** ¿Qué es el PPID?

a) Process Parent ID — el PID del proceso padre
b) Permanent PID
c) Primary PID
d) Public Process ID

**4.** ¿Qué pasa con un proceso si su padre termina antes que él?

a) Se transforma en kernel
b) Queda zombie
c) Queda huérfano y es adoptado por init/systemd
d) Muere automáticamente

**5.** ¿En cuál segmento de memoria vive el código compilado del programa?

a) Stack
b) Heap
c) BSS
d) Text segment (solo lectura)

**6.** ¿Para qué sirve el segmento BSS?

a) Para variables globales no inicializadas (o inicializadas a cero)
b) Para variables locales
c) Para variables globales inicializadas
d) Para el código

**7.** ¿De dónde viene el nombre "BSS"?

a) Boot Storage Segment
b) Background System Storage
c) Binary System Segment
d) Block Started by Symbol (de un ensamblador viejo)

**8.** ¿En qué dirección crece el stack?

a) Hacia direcciones bajas (en oposición al heap)
b) Aleatoriamente
c) No crece, es fijo
d) Hacia direcciones altas

**9.** ¿Qué son los file descriptors estándar 0, 1 y 2?

a) stdin, stdout, stderr
b) Memoria, CPU, disco
c) Read, write, execute
d) Padre, hijo, abuelo

**10.** ¿Qué archivo en `/proc` muestra el mapa de memoria de un proceso?

a) `/proc/<pid>/memory`
b) `/proc/<pid>/maps`
c) `/proc/<pid>/cmdline`
d) `/proc/<pid>/status`

**11.** Si dos procesos usan la misma dirección de memoria virtual, ¿qué pasa?

a) Cada uno apunta a una ubicación física distinta (memoria virtual aísla)
b) Comparten la misma memoria física
c) Es imposible
d) Hay conflicto y uno mata al otro

**12.** ¿Qué componente traduce direcciones virtuales a físicas?

a) El intérprete de Python
b) La CPU
c) El compilador
d) La MMU (Memory Management Unit)

---

## Respuestas

<details>
<summary>Click para ver respuestas</summary>

| # | Resp | Explicación |
|---|------|-------------|
| 1 | c | Programa en disco, proceso es ejecución activa |
| 2 | d | init / systemd (PID 1) |
| 3 | a | PID del proceso padre |
| 4 | c | Huérfano, adoptado por init |
| 5 | d | Text segment (solo lectura) |
| 6 | a | Variables globales no inicializadas |
| 7 | d | Block Started by Symbol |
| 8 | a | Hacia direcciones bajas (opuesto al heap) |
| 9 | a | stdin, stdout, stderr |
| 10 | b | `/proc/<pid>/maps` |
| 11 | a | Cada uno apunta a memoria física distinta (aislamiento) |
| 12 | d | MMU (Memory Management Unit) |

</details>

---

*Computación II - 2026 - Clase 3*
