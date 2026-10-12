# Clase 21: Asyncio avanzado - Autoevaluación

> Completá esta autoevaluación **después** de leer el contenido y hacer los ejercicios.
> No mires las respuestas antes de intentarlo.

---

## Parte 1: Colas

**Pregunta 1.** ¿Qué resuelve una `asyncio.Queue`?

a) Acelerar las corrutinas
b) Desacoplar quién produce trabajo de quién lo consume
c) Reemplazar al event loop
d) Evitar el GIL

**Pregunta 2.** ¿Qué pasa con `await cola.put(x)` si la cola está llena?

a) Lanza excepción
b) Se suspende hasta que haya lugar
c) Descarta el elemento
d) Agranda la cola

**Pregunta 3.** ¿Cómo se llama ese mecanismo?

a) Throttling
b) Backpressure
c) Rate limiting
d) Buffering

**Pregunta 4.** ¿Qué pasa con `maxsize=0`?

a) La cola no acepta nada
b) La cola es infinita: un productor rápido puede agotar la memoria
c) Solo acepta un elemento
d) Es un error

**Pregunta 5.** ¿Qué espera `await cola.join()`?

a) A que la cola quede vacía
b) A que todas las tareas estén procesadas, o sea que se hayan llamado todos los `task_done()`
c) A que los workers terminen
d) A que se llene

**Pregunta 6.** ¿Qué pasa si un worker se olvida de llamar a `task_done()`?

a) Nada
b) `join()` espera para siempre
c) La cola se corrompe
d) Lanza excepción

**Pregunta 7.** ¿Por qué `task_done()` va en un `finally`?

a) Por estilo
b) Para que el contador baje aunque el procesamiento falle
c) Porque es obligatorio sintácticamente
d) Para que sea más rápido

**Pregunta 8.** ¿Cuál es la ventaja del centinela sobre cancelar los workers?

a) Es más rápido
b) Cada worker termina la tarea que está procesando antes de salir
c) Usa menos memoria
d) Ninguna

**Pregunta 9.** Si tenés 4 workers, ¿cuántos centinelas hay que poner?

a) Uno
b) Cuatro: uno por worker
c) Depende de las tareas pendientes
d) Ninguno

**Pregunta 10.** ¿Qué problema puede traer una `PriorityQueue`?

a) Es más lenta
b) Inanición: si siempre entran tareas urgentes, las de baja prioridad nunca se procesan
c) No funciona con corrutinas
d) Pierde elementos

---

## Parte 2: TaskGroup

**Pregunta 11.** Con `gather`, si una corrutina falla, ¿qué pasa con las otras?

a) Se cancelan automáticamente
b) Siguen corriendo huérfanas, sin nadie que las espere
c) Se pausan
d) Se reinician

**Pregunta 12.** ¿Y con `TaskGroup`?

a) Lo mismo
b) Las hermanas se cancelan automáticamente
c) Se ignora el error
d) El grupo se reinicia

**Pregunta 13.** ¿Cómo se llama ese enfoque?

a) Concurrencia cooperativa
b) Concurrencia estructurada
c) Paralelismo
d) Multiplexing

**Pregunta 14.** ¿Qué tipo de excepción propaga un `TaskGroup`?

a) La excepción original
b) Un `ExceptionGroup`
c) `CancelledError`
d) `RuntimeError`

**Pregunta 15.** ¿Con qué sintaxis se captura?

a) `except` común
b) `except*`
c) `catch`
d) `with`

**Pregunta 16.** Si fallan un `ValueError` y un `TypeError`, ¿cuántas ramas `except*` se ejecutan?

a) Solo la primera
b) Las dos
c) Ninguna
d) Depende del orden

**Pregunta 17.** ¿Cómo se obtienen los resultados de un `TaskGroup`?

a) Los devuelve el `async with`
b) Guardando las tasks y leyendo su `.result()` después del bloque
c) Con `gather`
d) No se puede

---

## Parte 3: Sincronización

**Pregunta 18.** ¿Cuándo hace falta un `asyncio.Lock`?

a) Siempre que haya estado compartido
b) Solo si la sección crítica contiene un `await`
c) Nunca
d) Solo con varios threads

**Pregunta 19.** ¿Cómo se usan las primitivas de asyncio?

a) `with lock:`
b) `async with lock:`
c) `lock.acquire()` sin más
d) Como las de `threading`

**Pregunta 20.** ¿Cuál es la diferencia entre un `Semaphore` y una `Queue`?

a) Ninguna
b) El semáforo limita la concurrencia; la cola además desacopla productor de consumidor
c) El semáforo es más rápido
d) La cola no sirve para limitar

**Pregunta 21.** ¿Para qué sirve un `asyncio.Event`?

a) Para contar elementos
b) Como bandera que varias corrutinas pueden esperar
c) Para medir tiempo
d) Para cancelar tareas

**Pregunta 22.** Entre una cola y un lock para resolver el mismo problema, ¿qué conviene?

a) El lock, siempre
b) La cola: no hay estado compartido que proteger, hay mensajes que viajan
c) Es indistinto
d) Depende del sistema operativo

---

## Parte 4: Executors

**Pregunta 23.** Una corrutina hace un cálculo de 5 segundos sin `await`. ¿Qué le pasa al event loop?

a) Nada, sigue atendiendo
b) Queda bloqueado los 5 segundos: ninguna otra tarea avanza
c) Se reinicia
d) Lanza una excepción

**Pregunta 24.** En la medición de la clase, ¿cuánto se atrasó el loop sin executor?

a) ~10 ms
b) ~4300 ms
c) ~100 ms
d) No se atrasó

**Pregunta 25.** Con executor, el trabajo tarda lo mismo. ¿Qué mejoró entonces?

a) Nada
b) El loop sigue respondiendo: los demás pedidos se atienden mientras tanto
c) El cálculo es más rápido
d) Usa menos memoria

**Pregunta 26.** ¿Qué hace `asyncio.to_thread(funcion)`?

a) Crea una corrutina
b) Ejecuta la función en un thread del pool por defecto, fuera del loop
c) Crea un proceso
d) Es equivalente a `await`

**Pregunta 27.** Con 4 tareas CPU-bound, ¿qué pasa con `to_thread`?

a) Van en paralelo real
b) Se serializan por el GIL: tardan mucho más que con procesos
c) Fallan
d) Es más rápido que con procesos

**Pregunta 28.** En la medición, ¿cuál fue la diferencia entre threads y procesos con 4 tareas?

a) Ninguna
b) Los procesos fueron unas 3.5 veces más rápidos
c) Los threads fueron más rápidos
d) Dependió de la red

**Pregunta 29.** Con **una sola** tarea CPU-bound, ¿por qué empatan?

a) Porque el GIL no existe con una tarea
b) Porque no hay competencia por el GIL: no hay otro thread queriendo ejecutar bytecode
c) Porque el proceso es más lento
d) No empatan

**Pregunta 30.** ¿Qué función va a `ProcessPoolExecutor` y cuál a `to_thread`?

a) Cualquiera a cualquiera
b) CPU-bound a procesos, I/O bloqueante a threads
c) Al revés
d) Solo funciones sincrónicas

**Pregunta 31.** ¿Qué pasa si le pasás una `lambda` a `ProcessPoolExecutor`?

a) Funciona normalmente
b) Falla: no se puede picklear para mandarla a otro proceso
c) Se ejecuta en el proceso principal
d) Se convierte en función normal

**Pregunta 32.** ¿Por qué conviene crear el pool una sola vez?

a) Por estilo
b) Porque crear procesos es caro: hay que reutilizarlos
c) Porque solo se puede crear uno
d) No importa

---

## Respuestas

<details>
<summary>Ver respuestas (intentá primero)</summary>

| # | Respuesta | Comentario |
|---|-----------|------------|
| 1 | b | Productor-consumidor entre corrutinas |
| 2 | b | Se suspende: eso es el backpressure |
| 3 | b | Backpressure |
| 4 | b | Cola infinita, memoria sin control |
| 5 | b | Procesadas, no solo sacadas |
| 6 | b | El contador nunca llega a cero |
| 7 | b | Para que baje aunque falle |
| 8 | b | Termina su trabajo actual |
| 9 | b | Uno por worker |
| 10 | b | Inanición, como en la clase 11 |
| 11 | b | Quedan huérfanas |
| 12 | b | Se cancelan solas |
| 13 | b | Concurrencia estructurada |
| 14 | b | `ExceptionGroup` |
| 15 | b | `except*` |
| 16 | b | Las dos: no es excluyente |
| 17 | b | Guardar las tasks |
| 18 | b | Solo con `await` en el medio |
| 19 | b | `async with` |
| 20 | b | La cola además desacopla |
| 21 | b | Una bandera esperable |
| 22 | b | Mensajes en vez de estado compartido |
| 23 | b | Bloquea todo el loop |
| 24 | b | 4277 ms en la medición |
| 25 | b | El loop sigue respondiendo |
| 26 | b | Un thread, fuera del loop |
| 27 | b | El GIL los serializa |
| 28 | b | 3.5x |
| 29 | b | No hay competencia por el GIL |
| 30 | b | CPU a procesos, I/O a threads |
| 31 | b | No se puede picklear |
| 32 | b | Crear procesos es caro |

</details>

---

## Resultado de la autoevaluación

| Puntaje | Diagnóstico |
|---------|-------------|
| 28-32 correctas | Excelente. Ya tenés todo lo obligatorio del TP2 |
| 22-27 | Buen nivel. Repasá los temas donde fallaste |
| 16-21 | Nivel intermedio. Rehacé el ejercicio 3 (executors) y el 1 (colas) |
| < 16 | Repasá el contenido completo. Consultá con el docente antes de la próxima clase |

> Las preguntas 23 a 32 son el corazón de la medición 2 del TP2, y las 5 a 9 describen el apagado ordenado que también pide el enunciado. Si fallaste varias, volvé sobre `executor.py` y `cola.py`.

---

*Computación II - 2026 - Clase 21*
