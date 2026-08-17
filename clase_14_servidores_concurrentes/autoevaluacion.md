# Clase 14: Servidores Concurrentes - Autoevaluación

> Completá esta autoevaluación **después** de leer el contenido y hacer los ejercicios.
> No mires las respuestas antes de intentarlo.

---

## Parte 1: Por qué concurrencia acá

**Pregunta 1.** ¿Por qué los threads sirven para un servidor de red aunque no sirvan para cálculo numérico (en el build con GIL)?

a) Porque los sockets son más rápidos que la CPU
b) Porque el GIL se libera durante las operaciones de I/O
c) Porque los servidores usan menos memoria
d) No sirven: siempre hay que usar procesos

**Pregunta 2.** Un servidor de red es principalmente:

a) CPU-bound
b) I/O-bound
c) Memory-bound
d) Ninguna: no aplica la clasificación

**Pregunta 3.** ¿Desde qué versión de Python el build free-threaded dejó de ser experimental?

a) 3.12
b) 3.13
c) 3.14
d) Todavía es experimental

**Pregunta 4.** El build free-threaded es, hoy:

a) El binario por defecto que baja todo el mundo
b) Oficialmente soportado, pero opcional: hay que instalarlo aparte
c) Experimental y desaconsejado para producción
d) Fue abandonado

**Pregunta 5.** Si tu servidor corre en un build free-threaded, ¿qué cambia para el trabajo I/O-bound?

a) Se vuelve mucho más rápido
b) Prácticamente nada: los threads ya funcionaban bien, porque el GIL se libera esperando
c) Deja de funcionar
d) Hay que reescribirlo con procesos

---

## Parte 2: Threads

**Pregunta 6.** ¿Cuál es el cambio esencial entre el servidor secuencial y el de threads?

a) Usar sockets distintos
b) Que el bucle principal delegue y vuelva inmediatamente a `accept()`
c) Aumentar el backlog de `listen()`
d) Usar `SO_REUSEADDR`

**Pregunta 7.** ¿Para qué sirve `daemon=True` al crear el thread?

a) Le da más prioridad
b) Hace que el thread no impida que el programa termine
c) Lo ejecuta como root
d) Lo reinicia si falla

**Pregunta 8.** Dos threads hacen `contador += 1` sin lock. ¿Cuál es el problema?

a) Ninguno: el GIL lo hace atómico
b) La operación son varios pasos (leer, sumar, escribir) y pueden intercalarse
c) Python no permite variables globales en threads
d) Solo falla en free-threaded

**Pregunta 9.** ¿Cuál es el costo principal de un thread por cliente?

a) Cada thread reserva memoria para su stack y compite por el planificador
b) Los threads no pueden usar sockets
c) Cada thread necesita su propio puerto
d) No tiene costo

---

## Parte 3: Procesos y fork

**Pregunta 10.** Tras un `fork()`, ¿en cuántos procesos existe el descriptor de la conexión?

a) Solo en el padre
b) Solo en el hijo
c) En los dos
d) En ninguno: hay que volver a abrirlo

**Pregunta 11.** ¿Qué debe cerrar cada proceso después del `fork()`?

a) El padre cierra `conn`; el hijo cierra el socket que escucha
b) El padre cierra el socket que escucha; el hijo cierra `conn`
c) Ninguno cierra nada
d) Los dos cierran todo

**Pregunta 12.** Corrés un servidor fork en Python **sin** `conn.close()` en el padre y contás descriptores. ¿Qué observás?

a) Crecen sin parar hasta agotar el límite
b) No crecen: al reasignarse `conn` en la próxima vuelta, CPython libera el objeto y cierra el descriptor
c) El servidor falla al segundo cliente
d) Crecen solo con más de 1000 clientes

**Pregunta 13.** Siguiendo la anterior, ¿por qué sigue siendo correcto escribir el `close()` explícito?

a) Por costumbre, no hace falta
b) Porque en C hace falta, porque si el padre retiene la referencia sí se filtra, y porque no toda implementación de Python usa conteo de referencias
c) Porque acelera el servidor
d) Porque lo exige POSIX

**Pregunta 14.** ¿Qué es un proceso zombie?

a) Un proceso que consume 100% de CPU
b) Un proceso terminado cuyo padre todavía no llamó a `wait()`
c) Un proceso sin terminal asociada
d) Un proceso que quedó sin memoria

**Pregunta 15.** Un servidor fork sin manejo de `SIGCHLD` atiende 40 clientes. ¿Cuántos zombies quedan?

a) Ninguno: el kernel los limpia solo
b) Los 40
c) Solo el último
d) Depende de la carga

**Pregunta 16.** ¿Por qué el handler de `SIGCHLD` necesita un bucle `while`?

a) Por elegancia
b) Porque las señales no se encolan: si varios hijos mueren casi a la vez, llega un solo aviso
c) Porque `waitpid()` siempre falla la primera vez
d) No lo necesita

**Pregunta 17.** ¿Qué hace `WNOHANG` en `os.waitpid(-1, os.WNOHANG)`?

a) Espera indefinidamente
b) Hace que la llamada no bloquee si no hay hijos terminados
c) Mata al hijo
d) Ignora los errores

**Pregunta 18.** ¿Cuál es la ventaja de los procesos que **no** desaparece con el free-threading?

a) Que son más rápidos de crear
b) El aislamiento: si un cliente provoca un crash, no se lleva puesto al servidor
c) Que usan menos memoria
d) Que no necesitan sockets

---

## Parte 4: Pools

**Pregunta 19.** Un pool con 5 workers recibe 20 clientes que tardan 1 segundo cada uno. ¿Cuánto tarda el total?

a) 1 segundo
b) 4 segundos
c) 20 segundos
d) 5 segundos

**Pregunta 20.** En ese escenario, los clientes 6 a 20:

a) Son rechazados con un error
b) Esperan en la cola del pool hasta que se libere un worker
c) Se atienden en paralelo igual
d) Provocan un crash

**Pregunta 21.** ¿Cuál es el problema del pool con conexiones persistentes?

a) No soporta TCP
b) Cada cliente ocupa un worker durante toda su sesión, no solo mientras trabaja
c) Consume más memoria que un thread por cliente
d) No se puede acotar

**Pregunta 22.** ¿Para qué tipo de carga es el pool la herramienta correcta?

a) Conexiones de larga duración, tipo WebSocket
b) Tareas cortas y acotadas: una petición, una respuesta, se libera el worker
c) Cualquier carga
d) Solo para trabajo CPU-bound

**Pregunta 22b.** ¿Qué devuelve `pool.submit(funcion, arg)`?

a) El valor que devuelve `funcion`, esperando a que termine
b) Un `Future`: un recibo del resultado que todavía no está. Vuelve enseguida
c) `None`
d) El thread que va a ejecutar la tarea

**Pregunta 23.** ¿Qué pasa si `atender()` lanza una excepción dentro de `pool.submit()`?

a) El pool se detiene
b) La excepción queda silenciada dentro del `Future` y no te enterás
c) Se propaga al bucle principal
d) Se reintenta automáticamente

---

## Parte 5: Medición y límites

**Pregunta 24.** Medís un servidor secuencial con 20 clientes que tardan 1 segundo. Latencia mínima 1s, máxima 20s. ¿Qué significa?

a) Que la red está congestionada
b) Que los clientes fueron atendidos en serie: el primero esperó 1s y el último 20s
c) Que hubo errores de conexión
d) Que el servidor tiene un bug

**Pregunta 25.** Corrés el benchmark **sin** simular trabajo (sin `--lento`) y las cuatro estrategias dan casi lo mismo. ¿Qué concluís?

a) Que la arquitectura da igual
b) Que sin trabajo por cliente casi cualquier arquitectura anda: el parámetro que discrimina es el tiempo de atención
c) Que el benchmark está mal
d) Que el servidor secuencial es concurrente

**Pregunta 26.** ¿Qué límite del sistema operativo afecta a todas las estrategias?

a) La cantidad de RAM
b) La cantidad de descriptores de archivo por proceso (`ulimit -n`)
c) La velocidad del disco
d) La cantidad de puertos

**Pregunta 27.** ¿Qué es el problema C10K?

a) Un virus de los años 90
b) Cómo atender diez mil conexiones simultáneas en una máquina
c) Un límite de tamaño de paquete
d) Una vulnerabilidad de TCP

**Pregunta 28.** ¿Cómo se resolvió el C10K?

a) Haciendo los threads más baratos
b) Cambiando de modelo: un hilo que atiende muchas conexiones preguntándole al SO cuáles tienen datos listos
c) Comprando más servidores
d) No se resolvió

**Pregunta 29.** `socketserver.ThreadingTCPServer` resuelve en diez líneas lo que la clase construyó a mano. ¿Por qué escribirlo igual?

a) Para practicar tipeo
b) Porque cuando falla bajo carga, el diagnóstico requiere saber qué hace por dentro
c) Porque `socketserver` no funciona
d) Porque es más rápido a mano

**Pregunta 30.** ¿Qué estrategia elegirías para un servidor que hace trabajo CPU-bound pesado por cliente, en un Python con GIL?

a) Threads
b) Procesos
c) Pool de threads
d) Servidor secuencial

---

## Respuestas

<details>
<summary>Ver respuestas (intentá primero)</summary>

| # | Respuesta | Comentario |
|---|-----------|------------|
| 1 | b | El GIL se libera esperando I/O |
| 2 | b | Pasa la mayor parte del tiempo esperando |
| 3 | c | Python 3.14, vía PEP 779 |
| 4 | b | Fase II: soportado pero opcional |
| 5 | b | Los threads ya funcionaban para I/O |
| 6 | b | Delegar y volver a `accept()` |
| 7 | b | No impide que el programa termine |
| 8 | b | Read-modify-write no es atómico |
| 9 | a | Stack y presión sobre el planificador |
| 10 | c | En los dos: el fd se hereda |
| 11 | a | Padre cierra `conn`, hijo cierra `servidor` |
| 12 | b | El refcount de CPython cierra el fd |
| 13 | b | C, referencias retenidas, y PyPy |
| 14 | b | Terminado sin que el padre lo recoja |
| 15 | b | Los 40 (medido) |
| 16 | b | Las señales no se encolan |
| 17 | b | No bloquea si no hay hijos listos |
| 18 | b | El aislamiento ante crashes |
| 19 | b | 4 segundos: 20/5 = 4 tandas |
| 20 | b | Esperan, no son rechazados |
| 21 | b | Ocupan el worker toda la sesión |
| 22 | b | Tareas cortas y acotadas |
| 22b | b | Un `Future`; `submit()` no bloquea |
| 23 | b | Silenciada en el `Future` |
| 24 | b | La escalera del servidor secuencial |
| 25 | b | El tiempo de atención es lo que discrimina |
| 26 | b | `ulimit -n` |
| 27 | b | Diez mil conexiones simultáneas |
| 28 | b | I/O multiplexing (clase 17) |
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
