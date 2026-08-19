# Clase 6: Señales - Autoevaluación

Responde estas preguntas para verificar tu comprensión. Las respuestas están al final.

---

## Parte 1: Conceptos básicos (6 preguntas)

### Pregunta 1
¿Qué es una señal en Unix?

a) Una variable compartida
b) Un pipe de comunicación
c) Un tipo de archivo especial
d) Una notificación asíncrona enviada a un proceso

### Pregunta 2
¿Qué señal envía Ctrl+C?

a) SIGTERM
b) SIGINT
c) SIGKILL
d) SIGQUIT

### Pregunta 3
¿Qué comando envía SIGTERM por defecto?

a) `killall <pid>`
b) `kill -9 <pid>`
c) `kill <pid>`
d) `pkill -9 <pid>`

### Pregunta 4
¿Cuáles son las dos señales que NO se pueden capturar ni ignorar?

a) SIGHUP y SIGQUIT
b) SIGUSR1 y SIGUSR2
c) SIGTERM y SIGINT
d) SIGKILL y SIGSTOP

### Pregunta 5
¿Qué sucede por defecto cuando un proceso recibe SIGTERM?

a) El proceso termina
b) Se ignora
c) El proceso se pausa
d) El proceso se reinicia

### Pregunta 6
¿Qué diferencia hay entre SIGTERM y SIGKILL?

a) SIGTERM puede ser capturado, SIGKILL no
b) SIGKILL puede ser capturado, SIGTERM no
c) SIGTERM es más rápido
d) No hay diferencia

---

## Parte 2: Enviar señales (4 preguntas)

### Pregunta 7
¿Qué función de Python envía una señal a un proceso?

a) `signal.send(pid, sig)`
b) `os.signal(pid, sig)`
c) `os.kill(pid, sig)`
d) `signal.kill(pid, sig)`

### Pregunta 8
¿Cómo enviás SIGUSR1 al proceso con PID 1234 desde bash?

a) `kill -USR1 1234`
b) `signal USR1 1234`
c) `kill USR1 1234`
d) `send SIGUSR1 1234`

### Pregunta 9
¿Qué hace `kill -0 <pid>`?

a) Envía la señal 0
b) Verifica si el proceso existe (sin enviar señal)
c) Termina el proceso
d) Reinicia el proceso

### Pregunta 10
¿Qué señal recibe un proceso cuando escribe a un pipe sin lectores?

a) SIGPIPE
b) SIGINT
c) SIGIO
d) SIGTERM

---

## Parte 3: Manejar señales (6 preguntas)

### Pregunta 11
¿Qué función registra un manejador de señal en Python?

a) `signal.signal(signum, func)`
b) `signal.register(signum, func)`
c) `os.signal(signum, func)`
d) `signal.handler(signum, func)`

### Pregunta 12
¿Qué parámetros recibe una función manejador de señal?

a) Ningún parámetro
b) Solo el número de señal
c) El PID del emisor y la señal
d) El número de señal y el frame del stack

### Pregunta 13
¿Qué hace `signal.SIG_IGN`?

a) Ignora la señal
b) Restaura el manejador por defecto
c) Termina el proceso
d) Bloquea la señal

### Pregunta 14
¿Qué hace `signal.SIG_DFL`?

a) Define un nuevo manejador
b) Bloquea la señal
c) Ignora la señal
d) Restaura el manejador por defecto

### Pregunta 15
¿Qué función hace que un proceso espere hasta recibir una señal?

a) `signal.wait()`
b) `signal.pause()`
c) `signal.block()`
d) `os.wait()`

### Pregunta 16
¿Qué problema tienen las funciones como `print()` en un manejador de señal?

a) No son async-signal-safe (pueden causar corrupción)
b) Consumen mucha memoria
c) Son muy lentas
d) No funcionan en manejadores

---

## Parte 4: SIGCHLD y procesos (4 preguntas)

### Pregunta 17
¿Cuándo envía el kernel SIGCHLD a un proceso?

a) Cuando el padre termina
b) Cuando un hijo termina o cambia de estado
c) Cuando el proceso hace fork
d) Cada segundo automáticamente

### Pregunta 18
¿Por qué es útil manejar SIGCHLD?

a) Para enviar datos a los hijos
b) Para que los hijos corran más rápido
c) Para terminar hijos remotamente
d) Para recoger hijos terminados sin bloquear con wait()

### Pregunta 19
¿Qué sucede si no hacés wait() en un hijo terminado?

a) El padre termina
b) El hijo queda como zombie
c) No pasa nada
d) El hijo se reinicia

### Pregunta 20
¿Qué flag de waitpid() evita que bloquee si no hay hijos terminados?

a) `os.WCONTINUED`
b) `os.WNOWAIT`
c) `os.WNOHANG`
d) `os.WNOBLOCK`

---

## Parte 5: Alarmas y timers (5 preguntas)

### Pregunta 21
¿Qué señal envía el kernel cuando expira un timer configurado con alarm()?

a) SIGALRM
b) SIGCLOCK
c) SIGINT
d) SIGTIMER

### Pregunta 22
¿Qué hace `signal.alarm(5)`?

a) Espera 5 señales
b) Programa SIGALRM para que llegue en 5 segundos
c) Envía 5 señales SIGALRM
d) Pausa el proceso por 5 segundos

### Pregunta 23
¿Cómo cancelás una alarma pendiente?

a) No se puede cancelar
b) `signal.alarm(0)`
c) `signal.alarm(-1)`
d) `signal.cancel_alarm()`

### Pregunta 24
¿Para qué se puede usar SIGALRM?

a) Para implementar timeouts
b) Para terminar procesos
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
1. **d** - Una notificación asíncrona enviada a un proceso
2. **b** - SIGINT
3. **c** - `kill <pid>` (sin argumentos envía SIGTERM)
4. **d** - SIGKILL y SIGSTOP
5. **a** - El proceso termina
6. **a** - SIGTERM puede ser capturado, SIGKILL no

### Parte 2: Enviar señales
7. **c** - `os.kill(pid, sig)`
8. **a** - `kill -USR1 1234`
9. **b** - Verifica si el proceso existe (sin enviar señal)
10. **a** - SIGPIPE

### Parte 3: Manejar señales
11. **a** - `signal.signal(signum, func)`
12. **d** - El número de señal y el frame del stack
13. **a** - Ignora la señal
14. **d** - Restaura el manejador por defecto
15. **b** - `signal.pause()`
16. **a** - No son async-signal-safe (pueden causar corrupción)

### Parte 4: SIGCHLD y procesos
17. **b** - Cuando un hijo termina o cambia de estado
18. **d** - Para recoger hijos terminados sin bloquear con wait()
19. **b** - El hijo queda como zombie
20. **c** - `os.WNOHANG`

### Parte 5: Alarmas y timers
21. **a** - SIGALRM
22. **b** - Programa SIGALRM para que llegue en 5 segundos
23. **b** - `signal.alarm(0)`
24. **a** - Para implementar timeouts
25. **b** - `signal.setitimer()`

### Puntuación
- 23-25: Excelente dominio de señales
- 18-22: Buen nivel
- 13-17: Necesitas repasar algunos conceptos
- <13: Revisa el material nuevamente

</details>

---

*Computación II - 2026 - Clase 6*
