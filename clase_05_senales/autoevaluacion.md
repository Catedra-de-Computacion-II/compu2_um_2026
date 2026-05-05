# Clase 5: Señales - Autoevaluación

Responde estas preguntas para verificar tu comprensión. Las respuestas están al final.

---

## Parte 1: Conceptos básicos (6 preguntas)

### Pregunta 1
¿Qué es una señal en Unix?

a) Un tipo de archivo especial
b) Una notificación asíncrona enviada a un proceso
c) Un pipe de comunicación
d) Una variable compartida

### Pregunta 2
¿Qué señal envía Ctrl+C?

a) SIGTERM
b) SIGKILL
c) SIGINT
d) SIGQUIT

### Pregunta 3
¿Qué comando envía SIGTERM por defecto?

a) `kill -9 <pid>`
b) `kill <pid>`
c) `killall <pid>`
d) `pkill -9 <pid>`

### Pregunta 4
¿Cuáles son las dos señales que NO se pueden capturar ni ignorar?

a) SIGTERM y SIGINT
b) SIGKILL y SIGSTOP
c) SIGHUP y SIGQUIT
d) SIGUSR1 y SIGUSR2

### Pregunta 5
¿Qué sucede por defecto cuando un proceso recibe SIGTERM?

a) Se ignora
b) El proceso se pausa
c) El proceso termina
d) El proceso se reinicia

### Pregunta 6
¿Qué diferencia hay entre SIGTERM y SIGKILL?

a) SIGTERM es más rápido
b) SIGKILL puede ser capturado, SIGTERM no
c) SIGTERM puede ser capturado, SIGKILL no
d) No hay diferencia

---

## Parte 2: Enviar señales (4 preguntas)

### Pregunta 7
¿Qué función de Python envía una señal a un proceso?

a) `signal.send(pid, sig)`
b) `os.kill(pid, sig)`
c) `os.signal(pid, sig)`
d) `signal.kill(pid, sig)`

### Pregunta 8
¿Cómo enviás SIGUSR1 al proceso con PID 1234 desde bash?

a) `signal USR1 1234`
b) `kill -USR1 1234`
c) `send SIGUSR1 1234`
d) `kill USR1 1234`

### Pregunta 9
¿Qué hace `kill -0 <pid>`?

a) Envía la señal 0
b) Termina el proceso
c) Verifica si el proceso existe (sin enviar señal)
d) Reinicia el proceso

### Pregunta 10
¿Qué señal recibe un proceso cuando escribe a un pipe sin lectores?

a) SIGINT
b) SIGTERM
c) SIGPIPE
d) SIGIO

---

## Parte 3: Manejar señales (6 preguntas)

### Pregunta 11
¿Qué función registra un manejador de señal en Python?

a) `signal.handler(signum, func)`
b) `signal.signal(signum, func)`
c) `signal.register(signum, func)`
d) `os.signal(signum, func)`

### Pregunta 12
¿Qué parámetros recibe una función manejador de señal?

a) Solo el número de señal
b) El número de señal y el frame del stack
c) El PID del emisor y la señal
d) Ningún parámetro

### Pregunta 13
¿Qué hace `signal.SIG_IGN`?

a) Restaura el manejador por defecto
b) Ignora la señal
c) Bloquea la señal
d) Termina el proceso

### Pregunta 14
¿Qué hace `signal.SIG_DFL`?

a) Restaura el manejador por defecto
b) Ignora la señal
c) Define un nuevo manejador
d) Bloquea la señal

### Pregunta 15
¿Qué función hace que un proceso espere hasta recibir una señal?

a) `signal.wait()`
b) `signal.pause()`
c) `signal.block()`
d) `os.wait()`

### Pregunta 16
¿Qué problema tienen las funciones como `print()` en un manejador de señal?

a) Son muy lentas
b) No son async-signal-safe (pueden causar corrupción)
c) No funcionan en manejadores
d) Consumen mucha memoria

---

## Parte 4: SIGCHLD y procesos (4 preguntas)

### Pregunta 17
¿Cuándo envía el kernel SIGCHLD a un proceso?

a) Cuando el proceso hace fork
b) Cuando un hijo termina o cambia de estado
c) Cuando el padre termina
d) Cada segundo automáticamente

### Pregunta 18
¿Por qué es útil manejar SIGCHLD?

a) Para que los hijos corran más rápido
b) Para recoger hijos terminados sin bloquear con wait()
c) Para enviar datos a los hijos
d) Para terminar hijos remotamente

### Pregunta 19
¿Qué sucede si no hacés wait() en un hijo terminado?

a) El hijo se reinicia
b) El hijo queda como zombie
c) El padre termina
d) No pasa nada

### Pregunta 20
¿Qué flag de waitpid() evita que bloquee si no hay hijos terminados?

a) `os.WNOWAIT`
b) `os.WNOHANG`
c) `os.WNOBLOCK`
d) `os.WCONTINUED`

---

## Parte 5: Alarmas y timers (5 preguntas)

### Pregunta 21
¿Qué señal envía el kernel cuando expira un timer configurado con alarm()?

a) SIGINT
b) SIGTIMER
c) SIGALRM
d) SIGCLOCK

### Pregunta 22
¿Qué hace `signal.alarm(5)`?

a) Pausa el proceso por 5 segundos
b) Programa SIGALRM para que llegue en 5 segundos
c) Envía 5 señales SIGALRM
d) Espera 5 señales

### Pregunta 23
¿Cómo cancelás una alarma pendiente?

a) `signal.alarm(-1)`
b) `signal.alarm(0)`
c) `signal.cancel_alarm()`
d) No se puede cancelar

### Pregunta 24
¿Para qué se puede usar SIGALRM?

a) Para terminar procesos
b) Para implementar timeouts
c) Para enviar datos
d) Para crear procesos

### Pregunta 25
¿Qué función permite alarmas más precisas que alarm()?

a) `signal.precise_alarm()`
b) `signal.setitimer()`
c) `signal.nanotimer()`
d) `signal.alarm_ms()`

---

## Respuestas

<details>
<summary>Click para ver respuestas</summary>

### Parte 1: Conceptos básicos
1. **b** - Una notificación asíncrona enviada a un proceso
2. **c** - SIGINT
3. **b** - `kill <pid>` (sin argumentos envía SIGTERM)
4. **b** - SIGKILL y SIGSTOP
5. **c** - El proceso termina
6. **c** - SIGTERM puede ser capturado, SIGKILL no

### Parte 2: Enviar señales
7. **b** - `os.kill(pid, sig)`
8. **b** - `kill -USR1 1234`
9. **c** - Verifica si el proceso existe (sin enviar señal)
10. **c** - SIGPIPE

### Parte 3: Manejar señales
11. **b** - `signal.signal(signum, func)`
12. **b** - El número de señal y el frame del stack
13. **b** - Ignora la señal
14. **a** - Restaura el manejador por defecto
15. **b** - `signal.pause()`
16. **b** - No son async-signal-safe (pueden causar corrupción)

### Parte 4: SIGCHLD y procesos
17. **b** - Cuando un hijo termina o cambia de estado
18. **b** - Para recoger hijos terminados sin bloquear con wait()
19. **b** - El hijo queda como zombie
20. **b** - `os.WNOHANG`

### Parte 5: Alarmas y timers
21. **c** - SIGALRM
22. **b** - Programa SIGALRM para que llegue en 5 segundos
23. **b** - `signal.alarm(0)`
24. **b** - Para implementar timeouts
25. **b** - `signal.setitimer()`

### Puntuación
- 23-25: Excelente dominio de señales
- 18-22: Buen nivel
- 13-17: Necesitas repasar algunos conceptos
- <13: Revisa el material nuevamente

</details>

---

*Computación II - 2026 - Clase 5*
