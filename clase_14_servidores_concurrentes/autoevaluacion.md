# Clase 14: Servidores Concurrentes - Autoevaluación

> Completá esta autoevaluación **después** de leer el contenido y hacer los ejercicios.
> No mires las respuestas antes de intentarlo.

---

## Parte 1: Por qué concurrencia acá

**Pregunta 1.** ¿Por qué los threads sirven para un servidor de red aunque no sirvan para cálculo numérico (en el build con GIL)?

a) Porque el GIL se libera durante las operaciones de I/O
b) Porque los sockets son más rápidos que la CPU
c) No sirven: siempre hay que usar procesos
d) Porque los servidores usan menos memoria

**Pregunta 2.** Un servidor de red es principalmente:

a) Memory-bound
b) CPU-bound
c) I/O-bound
d) Ninguna: no aplica la clasificación

**Pregunta 3.** ¿Desde qué versión de Python el build free-threaded dejó de ser experimental?

a) Todavía es experimental
b) 3.12
c) 3.13
d) 3.14

**Pregunta 4.** El build free-threaded es, hoy:

a) Oficialmente soportado, pero opcional: hay que instalarlo aparte
b) Fue abandonado
c) Experimental y desaconsejado para producción
d) El binario por defecto que baja todo el mundo

**Pregunta 5.** Si tu servidor corre en un build free-threaded, ¿qué cambia para el trabajo I/O-bound?

a) Deja de funcionar
b) Se vuelve mucho más rápido
c) Hay que reescribirlo con procesos
d) Prácticamente nada: los threads ya funcionaban bien, porque el GIL se libera esperando

---

## Parte 2: Threads

**Pregunta 6.** ¿Cuál es el cambio esencial entre el servidor secuencial y el de threads?

a) Aumentar el backlog de `listen()`
b) Que el bucle principal delegue y vuelva inmediatamente a `accept()`
c) Usar sockets distintos
d) Usar `SO_REUSEADDR`

**Pregunta 7.** ¿Para qué sirve `daemon=True` al crear el thread?

a) Hace que el thread no impida que el programa termine
b) Le da más prioridad
c) Lo ejecuta como root
d) Lo reinicia si falla

**Pregunta 8.** Dos threads hacen `contador += 1` sin lock. ¿Cuál es el problema?

a) Solo falla en free-threaded
b) Ninguno: el GIL lo hace atómico
c) Python no permite variables globales en threads
d) La operación son varios pasos (leer, sumar, escribir) y pueden intercalarse

**Pregunta 9.** ¿Cuál es el costo principal de un thread por cliente?

a) Los threads no pueden usar sockets
b) Cada thread reserva memoria para su stack y compite por el planificador
c) Cada thread necesita su propio puerto
d) No tiene costo

---

## Parte 3: Procesos y fork

**Pregunta 10.** Tras un `fork()`, ¿en cuántos procesos existe el descriptor de la conexión?

a) En ninguno: hay que volver a abrirlo
b) En los dos
c) Solo en el hijo
d) Solo en el padre

**Pregunta 11.** ¿Qué debe cerrar cada proceso después del `fork()`?

a) Los dos cierran todo
b) Ninguno cierra nada
c) El padre cierra el socket que escucha; el hijo cierra `conn`
d) El padre cierra `conn`; el hijo cierra el socket que escucha

**Pregunta 12.** Corrés un servidor fork en Python **sin** `conn.close()` en el padre y contás descriptores. ¿Qué observás?

a) No crecen: al reasignarse `conn` en la próxima vuelta, CPython libera el objeto y cierra el descriptor
b) El servidor falla al segundo cliente
c) Crecen sin parar hasta agotar el límite
d) Crecen solo con más de 1000 clientes

**Pregunta 13.** Siguiendo la anterior, ¿por qué sigue siendo correcto escribir el `close()` explícito?

a) Porque lo exige POSIX
b) Por costumbre, no hace falta
c) Porque en C hace falta, porque si el padre retiene la referencia sí se filtra, y porque no toda implementación de Python usa conteo de referencias
d) Porque acelera el servidor

**Pregunta 14.** ¿Qué es un proceso zombie?

a) Un proceso sin terminal asociada
b) Un proceso terminado cuyo padre todavía no llamó a `wait()`
c) Un proceso que consume 100% de CPU
d) Un proceso que quedó sin memoria

**Pregunta 15.** Un servidor fork sin manejo de `SIGCHLD` atiende 40 clientes. ¿Cuántos zombies quedan?

a) Ninguno: el kernel los limpia solo
b) Depende de la carga
c) Solo el último
d) Los 40

**Pregunta 16.** ¿Por qué el handler de `SIGCHLD` necesita un bucle `while`?

a) Por elegancia
b) Porque las señales no se encolan: si varios hijos mueren casi a la vez, llega un solo aviso
c) No lo necesita
d) Porque `waitpid()` siempre falla la primera vez

**Pregunta 17.** ¿Qué hace `WNOHANG` en `os.waitpid(-1, os.WNOHANG)`?

a) Espera indefinidamente
b) Ignora los errores
c) Hace que la llamada no bloquee si no hay hijos terminados
d) Mata al hijo

**Pregunta 18.** ¿Cuál es la ventaja de los procesos que **no** desaparece con el free-threading?

a) Que no necesitan sockets
b) El aislamiento: si un cliente provoca un crash, no se lleva puesto al servidor
c) Que usan menos memoria
d) Que son más rápidos de crear

---

## Parte 4: Pools

**Pregunta 19.** Un pool con 5 workers recibe 20 clientes que tardan 1 segundo cada uno. ¿Cuánto tarda el total?

a) 5 segundos
b) 1 segundo
c) 4 segundos
d) 20 segundos

**Pregunta 20.** En ese escenario, los clientes 6 a 20:

a) Se atienden en paralelo igual
b) Son rechazados con un error
c) Esperan en la cola del pool hasta que se libere un worker
d) Provocan un crash

**Pregunta 21.** ¿Cuál es el problema del pool con conexiones persistentes?

a) No soporta TCP
b) No se puede acotar
c) Cada cliente ocupa un worker durante toda su sesión, no solo mientras trabaja
d) Consume más memoria que un thread por cliente

**Pregunta 22.** ¿Para qué tipo de carga es el pool la herramienta correcta?

a) Tareas cortas y acotadas: una petición, una respuesta, se libera el worker
b) Solo para trabajo CPU-bound
c) Conexiones de larga duración, tipo WebSocket
d) Cualquier carga

**Pregunta 22b.** ¿Qué devuelve `pool.submit(funcion, arg)`?

a) El valor que devuelve `funcion`, esperando a que termine
b) Un `Future`: un recibo del resultado que todavía no está. Vuelve enseguida
c) `None`
d) El thread que va a ejecutar la tarea

**Pregunta 23.** ¿Qué pasa si `atender()` lanza una excepción dentro de `pool.submit()`?

a) El pool se detiene
b) Se reintenta automáticamente
c) Se propaga al bucle principal
d) La excepción queda silenciada dentro del `Future` y no te enterás

---

## Parte 5: Medición y límites

**Pregunta 24.** Medís un servidor secuencial con 20 clientes que tardan 1 segundo. Latencia mínima 1s, máxima 20s. ¿Qué significa?

a) Que el servidor tiene un bug
b) Que la red está congestionada
c) Que los clientes fueron atendidos en serie: el primero esperó 1s y el último 20s
d) Que hubo errores de conexión

**Pregunta 25.** Corrés el benchmark **sin** simular trabajo (sin `--lento`) y las cuatro estrategias dan casi lo mismo. ¿Qué concluís?

a) Que la arquitectura da igual
b) Que el benchmark está mal
c) Que el servidor secuencial es concurrente
d) Que sin trabajo por cliente casi cualquier arquitectura anda: el parámetro que discrimina es el tiempo de atención

**Pregunta 26.** ¿Qué límite del sistema operativo afecta a todas las estrategias?

a) La cantidad de descriptores de archivo por proceso (`ulimit -n`)
b) La cantidad de puertos
c) La cantidad de RAM
d) La velocidad del disco

**Pregunta 27.** ¿Qué es el problema C10K?

a) Una vulnerabilidad de TCP
b) Un virus de los años 90
c) Un límite de tamaño de paquete
d) Cómo atender diez mil conexiones simultáneas en una máquina

**Pregunta 28.** ¿Cómo se resolvió el C10K?

a) Cambiando de modelo: un hilo que atiende muchas conexiones preguntándole al SO cuáles tienen datos listos
b) No se resolvió
c) Haciendo los threads más baratos
d) Comprando más servidores

**Pregunta 29.** `socketserver.ThreadingTCPServer` resuelve en diez líneas lo que la clase construyó a mano. ¿Por qué escribirlo igual?

a) Para practicar tipeo
b) Porque cuando falla bajo carga, el diagnóstico requiere saber qué hace por dentro
c) Porque `socketserver` no funciona
d) Porque es más rápido a mano

**Pregunta 30.** ¿Qué estrategia elegirías para un servidor que hace trabajo CPU-bound pesado por cliente, en un Python con GIL?

a) Pool de threads
b) Procesos
c) Servidor secuencial
d) Threads

---

## Respuestas

<details>
<summary>Ver respuestas (intentá primero)</summary>

| # | Respuesta | Comentario |
|---|-----------|------------|
| 1 | a | El GIL se libera esperando I/O |
| 2 | c | Pasa la mayor parte del tiempo esperando |
| 3 | d | Python 3.14, vía PEP 779 |
| 4 | a | Fase II: soportado pero opcional |
| 5 | d | Los threads ya funcionaban para I/O |
| 6 | b | Delegar y volver a `accept()` |
| 7 | a | No impide que el programa termine |
| 8 | d | Read-modify-write no es atómico |
| 9 | b | Stack y presión sobre el planificador |
| 10 | b | En los dos: el fd se hereda |
| 11 | d | Padre cierra `conn`, hijo cierra `servidor` |
| 12 | a | El refcount de CPython cierra el fd |
| 13 | c | C, referencias retenidas, y PyPy |
| 14 | b | Terminado sin que el padre lo recoja |
| 15 | d | Los 40 (medido) |
| 16 | b | Las señales no se encolan |
| 17 | c | No bloquea si no hay hijos listos |
| 18 | b | El aislamiento ante crashes |
| 19 | c | 4 segundos: 20/5 = 4 tandas |
| 20 | c | Esperan, no son rechazados |
| 21 | c | Ocupan el worker toda la sesión |
| 22 | a | Tareas cortas y acotadas |
| 22b | b | Un `Future`; `submit()` no bloquea |
| 23 | d | Silenciada en el `Future` |
| 24 | c | La escalera del servidor secuencial |
| 25 | d | El tiempo de atención es lo que discrimina |
| 26 | a | `ulimit -n` |
| 27 | d | Diez mil conexiones simultáneas |
| 28 | a | I/O multiplexing (clase 17) |
| 29 | b | Diagnosticar requiere saber qué hay abajo |
| 30 | b | Procesos: esquivan el GIL |

</details>

---

## Resultado de la autoevaluación

| Puntaje | Diagnóstico |
|---------|-------------|
| 27-30 correctas | Excelente. Avanzá a la clase 15 (UDP) |
| 21-26 | Buen nivel. Repasá los temas donde fallaste |
| 15-20 | Nivel intermedio. Rehacé el ejercicio 3 (fork) y el 1 (mediciones) |
| < 15 | Repasá el contenido completo. Consultá con el docente antes de la próxima clase |

> Las preguntas 10 a 18 son las del ejercicio obligatorio. Si fallaste varias, volvé sobre el ejercicio 3 con el código en la mano: son errores que se cometen una sola vez si se entienden bien.

---

*Computación II - 2026 - Clase 14*
