# Clase 3: Procesos - Fundamentos — Autoevaluación

> Cubre el material de fundamentos: anatomía del proceso, jerarquía, memoria virtual, file descriptors.
> Las preguntas sobre `fork()`, `exec()` y `wait()` están en la autoevaluación de **clase 4**.

---

## Preguntas

**1.** ¿Cuál es la diferencia fundamental entre un programa y un proceso?

a) No hay diferencia, son lo mismo
b) El programa está en disco, el proceso es la instancia en ejecución
c) Un proceso es más grande
d) El programa siempre tiene PID y el proceso no

**2.** ¿Qué proceso es el ancestro de todos los demás en Linux?

a) `bash`
b) `kernel`
c) `init` o `systemd` (PID 1)
d) `root`

**3.** ¿Qué es el PPID?

a) Process Parent ID — el PID del proceso padre
b) Public Process ID
c) Primary PID
d) Permanent PID

**4.** ¿Qué pasa con un proceso si su padre termina antes que él?

a) Muere automáticamente
b) Queda zombie
c) Queda huérfano y es adoptado por init/systemd
d) Se transforma en kernel

**5.** ¿En cuál segmento de memoria vive el código compilado del programa?

a) Heap
b) Stack
c) Text segment (solo lectura)
d) BSS

**6.** ¿Para qué sirve el segmento BSS?

a) Para variables globales no inicializadas (o inicializadas a cero)
b) Para variables locales
c) Para el código
d) Para variables globales inicializadas

**7.** ¿De dónde viene el nombre "BSS"?

a) Boot Storage Segment
b) Block Started by Symbol (de un ensamblador viejo)
c) Binary System Segment
d) Background System Storage

**8.** ¿En qué dirección crece el stack?

a) Hacia direcciones altas
b) Hacia direcciones bajas (en oposición al heap)
c) No crece, es fijo
d) Aleatoriamente

**9.** ¿Qué son los file descriptors estándar 0, 1 y 2?

a) Memoria, CPU, disco
b) stdin, stdout, stderr
c) Padre, hijo, abuelo
d) Read, write, execute

**10.** ¿Qué archivo en `/proc` muestra el mapa de memoria de un proceso?

a) `/proc/<pid>/status`
b) `/proc/<pid>/maps`
c) `/proc/<pid>/memory`
d) `/proc/<pid>/cmdline`

**11.** Si dos procesos usan la misma dirección de memoria virtual, ¿qué pasa?

a) Hay conflicto y uno mata al otro
b) Comparten la misma memoria física
c) Cada uno apunta a una ubicación física distinta (memoria virtual aísla)
d) Es imposible

**12.** ¿Qué componente traduce direcciones virtuales a físicas?

a) La CPU
b) La MMU (Memory Management Unit)
c) El intérprete de Python
d) El compilador

---

## Respuestas

<details>
<summary>Click para ver respuestas</summary>

| # | Resp | Explicación |
|---|------|-------------|
| 1 | b | Programa en disco, proceso es ejecución activa |
| 2 | c | init / systemd (PID 1) |
| 3 | a | PID del proceso padre |
| 4 | c | Huérfano, adoptado por init |
| 5 | c | Text segment (solo lectura) |
| 6 | a | Variables globales no inicializadas |
| 7 | b | Block Started by Symbol |
| 8 | b | Hacia direcciones bajas (opuesto al heap) |
| 9 | b | stdin, stdout, stderr |
| 10 | b | `/proc/<pid>/maps` |
| 11 | c | Cada uno apunta a memoria física distinta (aislamiento) |
| 12 | b | MMU (Memory Management Unit) |

</details>

---

*Computación II - 2026 - Clase 3*
