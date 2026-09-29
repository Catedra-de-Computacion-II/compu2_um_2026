# Clase 20: Asyncio en red - Autoevaluación

> Completá esta autoevaluación **después** de leer el contenido y hacer los ejercicios.
> No mires las respuestas antes de intentarlo.

---

## Parte 1: La API de streams

**Pregunta 1.** ¿Qué devuelve `await asyncio.open_connection(host, puerto)`?

a) Un socket
b) Un par `(StreamReader, StreamWriter)`
c) Una corrutina
d) Un file descriptor

**Pregunta 2.** ¿A qué se parecen `reader`/`writer` de clases anteriores?

a) A `select` y `poll`
b) A `rfile`/`wfile` de `StreamRequestHandler` (clase 16)
c) A los pipes de la clase 5
d) A nada visto antes

**Pregunta 3.** ¿Por qué `writer.write()` NO lleva `await`?

a) Es un descuido de la API
b) Porque no bloquea: copia a un buffer interno y vuelve
c) Porque es sincrónico de verdad
d) Porque no manda nada

**Pregunta 4.** ¿Para qué sirve `await writer.drain()`?

a) Para vaciar el buffer de lectura
b) Para control de flujo: se suspende si venís escribiendo más rápido de lo que la red manda
c) Para cerrar la conexión
d) Para forzar el envío inmediato

**Pregunta 5.** ¿Qué pasa si omitís `drain()` y el otro extremo es lento?

a) Falla con excepción
b) El buffer crece sin control y consume memoria
c) Los datos se pierden
d) Nada

**Pregunta 6.** ¿Qué hace `await reader.readexactly(n)` si el otro lado cierra antes de mandar n bytes?

a) Devuelve lo que haya
b) Lanza `IncompleteReadError`
c) Devuelve `b''`
d) Espera para siempre

**Pregunta 7.** ¿A qué corresponden `readline()` y `readexactly()`?

a) A nada en particular
b) A los dos framings de la clase 13: delimitador y prefijo de longitud
c) A dos formas de cerrar
d) A lectura bloqueante y no bloqueante

**Pregunta 8.** ¿Qué devuelve `await reader.read(n)` si el cliente cerró?

a) `None`
b) `b''`
c) Lanza excepción
d) Se cuelga

---

## Parte 2: El servidor

**Pregunta 9.** ¿Qué crea `asyncio.start_server` por cada conexión?

a) Un thread
b) Una Task
c) Un proceso
d) Un socket nuevo solamente

**Pregunta 10.** ¿Cuántos threads usa un servidor asyncio con 500 clientes conectados?

a) 500
b) 1
c) Uno por core
d) Depende del backlog

**Pregunta 11.** ¿Qué estructura es una conexión en asyncio, comparado con la clase 14?

a) Un thread del sistema operativo, igual que antes
b) Un objeto Task de unos cientos de bytes
c) Un proceso
d) Un archivo

**Pregunta 12.** En la medición de la clase, 1000 clientes concurrentes tardaron:

a) ~60 s
b) Menos de un segundo
c) Falló antes de los 1000
d) ~10 s

**Pregunta 13.** ¿De qué problema es esto la respuesta?

a) Del GIL
b) Del problema C10K planteado en la clase 14
c) Del deadlock
d) De la fragmentación IP

---

## Parte 3: Sincronización

**Pregunta 14.** ¿Por qué un `contador += 1` no necesita `Lock` entre corrutinas?

a) Porque Python lo hace atómico
b) Porque el cambio de contexto solo ocurre en un `await`, y ahí no hay ninguno
c) Porque hay un solo core
d) Sí lo necesita

**Pregunta 15.** ¿Y en este caso?

```python
saldo = cuentas[origen]
await registrar(monto)
cuentas[origen] = saldo - monto
```

a) Tampoco hace falta
b) Sí hace falta: hay un `await` en el medio de la sección crítica
c) Hace falta un `threading.Lock`
d) Hay que usar procesos

**Pregunta 16.** ¿Cuál es la regla?

a) Siempre usar lock
b) Hace falta lock solo si la sección crítica contiene un `await`
c) Nunca hace falta en asyncio
d) Depende de la cantidad de tareas

**Pregunta 17.** ¿Cómo se usa un `asyncio.Lock`?

a) `with lock:`
b) `async with lock:`
c) `lock.acquire()` sin más
d) Igual que `threading.Lock`

**Pregunta 18.** ¿Qué ventaja tiene esto sobre los threads de la clase 11?

a) Es más rápido
b) Los puntos donde puede haber race condition son visibles: están marcados con `await`
c) No hay race conditions nunca
d) Ninguna

---

## Parte 4: Clientes concurrentes

**Pregunta 19.** Diez descargas con `gather`, la más lenta de 2 s y la suma de 8 s. ¿Cuánto tarda?

a) ~8 s
b) ~2 s
c) ~0.8 s
d) Depende de los cores

**Pregunta 20.** ¿Por qué `requests` no sirve dentro de una corrutina?

a) Porque no soporta HTTPS
b) Porque es sincrónico: bloquea el event loop
c) Porque es lento
d) Sí sirve

**Pregunta 21.** ¿Por qué el `AsyncClient` de httpx se crea una sola vez?

a) Por ahorrar memoria
b) Para reutilizar conexiones: el keep-alive de la clase 19
c) Porque solo se puede crear uno
d) Es indistinto

**Pregunta 22.** ¿Para qué sirve un `asyncio.Semaphore` en descargas concurrentes?

a) Para ordenarlas
b) Para acotar cuántas corren a la vez
c) Para acelerarlas
d) Para cancelarlas

**Pregunta 23.** ¿Qué problema evita acotar la concurrencia?

a) Ninguno, solo hace más lento
b) Agotar descriptores, saturar la red, o que el servidor remoto te bloquee
c) Race conditions
d) Deadlocks

**Pregunta 24.** Con `gather` normal, si una corrutina lanza excepción:

a) Las demás siguen y se ignora el error
b) Se propaga la excepción; las demás quedan corriendo huérfanas
c) Se cancelan todas automáticamente
d) El programa termina

---

## Parte 5: Timeouts y cancelación

**Pregunta 25.** ¿Qué hace `async with asyncio.timeout(5)` cuando vence?

a) Devuelve `None`
b) Cancela la tarea y lanza `TimeoutError`
c) Deja la tarea corriendo en segundo plano
d) Reintenta

**Pregunta 26.** ¿Qué hace `tarea.cancel()`?

a) Mata la tarea inmediatamente
b) Inyecta un `CancelledError` en el próximo punto de suspensión
c) La saca de la cola sin más
d) Espera a que termine

**Pregunta 27.** ¿Se puede cancelar una tarea que está calculando sin ningún `await`?

a) Sí, inmediatamente
b) No: el `cancel()` queda pendiente hasta que llegue a un `await`
c) Sí, pero corrompe el estado
d) Lanza excepción

**Pregunta 28.** Si capturás `CancelledError`, ¿qué hay que hacer?

a) Nada, devolver un valor
b) Relanzarla con `raise`
c) Convertirla en otra excepción
d) Ignorarla

**Pregunta 29.** ¿Qué pasa si no la relanzás?

a) Nada
b) Quien pidió la cancelación nunca se entera: el `await tarea` no termina
c) Se cancela igual
d) Error de sintaxis

**Pregunta 30.** ¿Por qué `CancelledError` hereda de `BaseException`?

a) Por razones históricas
b) Para que un `except Exception:` distraído no se la coma sin querer
c) Porque no es un error
d) Para que sea más rápida

**Pregunta 31.** ¿Dónde va la limpieza de recursos en una corrutina cancelable?

a) En el `except`
b) En un `finally`
c) En el `else`
d) Al final del cuerpo

---

## Parte 6: Señales y cierre

**Pregunta 32.** ¿Qué ventaja tiene `loop.add_signal_handler()` sobre `signal.signal()`?

a) Es más rápido
b) El loop ejecuta el callback entre tareas, en un momento seguro
c) Soporta más señales
d) Ninguna

**Pregunta 33.** ¿Qué patrón de la clase 6 usa por debajo?

a) El de máscaras de señales
b) El self-pipe
c) `sigaction`
d) Polling

**Pregunta 34.** ¿Cuándo NO conviene asyncio?

a) Con muchas conexiones
b) Con trabajo CPU-bound, o cuando las bibliotecas que necesitás son sincrónicas
c) Con timeouts
d) Siempre conviene

---

## Respuestas

<details>
<summary>Ver respuestas (intentá primero)</summary>

| # | Respuesta | Comentario |
|---|-----------|------------|
| 1 | b | `StreamReader` y `StreamWriter` |
| 2 | b | Los primos async de `rfile`/`wfile` |
| 3 | b | Copia a un buffer y vuelve |
| 4 | b | Control de flujo de aplicación |
| 5 | b | Crece sin control; no falla en pruebas |
| 6 | b | `IncompleteReadError` |
| 7 | b | Los dos framings, ya implementados |
| 8 | b | `b''`, como en la clase 13 |
| 9 | b | Una Task |
| 10 | b | Uno solo, verificado |
| 11 | b | Una estructura de datos, no un hilo del SO |
| 12 | b | 0.59 s en la medición de la clase |
| 13 | b | C10K |
| 14 | b | No hay `await` en el medio |
| 15 | b | El `await` abre la ventana |
| 16 | b | Solo si hay `await` en la sección crítica |
| 17 | b | `async with` |
| 18 | b | Los puntos de riesgo son visibles |
| 19 | b | Lo que tarda la más lenta |
| 20 | b | Bloquea el event loop (clase 19) |
| 21 | b | Keep-alive y pool de conexiones |
| 22 | b | Acotar la concurrencia |
| 23 | b | Descriptores, red, bloqueo remoto |
| 24 | b | Por eso existe `return_exceptions` y `TaskGroup` |
| 25 | b | El timeout es una cancelación |
| 26 | b | En el próximo `await` |
| 27 | b | Verificado: termina igual |
| 28 | b | Relanzarla siempre |
| 29 | b | La tarea queda viva y nadie se entera |
| 30 | b | Para que no la capture un `except Exception` |
| 31 | b | En `finally` |
| 32 | b | Entre tareas, sin async-signal-safety |
| 33 | b | El self-pipe |
| 34 | b | CPU-bound o bibliotecas sincrónicas |

</details>

---

## Resultado de la autoevaluación

| Puntaje | Diagnóstico |
|---------|-------------|
| 30-34 correctas | Excelente. Avanzá a la clase 21 (Asyncio avanzado) |
| 24-29 | Buen nivel. Repasá los temas donde fallaste |
| 17-23 | Nivel intermedio. Rehacé el ejercicio 3 (concurrencia) y el 4 (locks) |
| < 17 | Repasá el contenido completo. Consultá con el docente antes de la próxima clase |

> Las preguntas 14 a 18 y 26 a 31 son las que más importan para el TP2: cuándo hace falta sincronizar y cómo cancelar limpiamente. El enunciado pide las dos cosas explícitamente.

---

*Computación II - 2026 - Clase 20*
