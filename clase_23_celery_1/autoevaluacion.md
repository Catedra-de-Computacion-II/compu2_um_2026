# Clase 23: Celery I - Autoevaluación

Respondé sin mirar el apunte. Si una pregunta te deja dudando, ahí está el tema a repasar.

---

## Bloque 1: por qué Celery

1. ¿Cuál es la frontera que ninguna herramienta de concurrencia del año cruzaba?

2. Nombrá las tres cosas que no se pueden hacer con un `Future` y sí con Celery.

3. Un proceso encola una tarea y muere inmediatamente. ¿Qué pasa con la tarea?

4. ¿Por qué un `Future` no puede recuperarse después de que su proceso murió? (La respuesta no es "no está implementado".)

5. Dame un caso donde Celery sea la herramienta equivocada y `ProcessPoolExecutor` la correcta.

---

## Bloque 2: las tres piezas

6. ¿Qué es el broker y qué guarda?

7. ¿Qué es el result backend y por qué es opcional?

8. ¿En qué casos conviene **no** configurar backend?

9. ¿Cómo se lanza un worker? ¿Es un proceso aparte o un thread de tu programa?

10. En el banner del worker, ¿qué significa `concurrency: 4 (prefork)`? ¿Qué clase del año vimos ese patrón?

11. ¿Para qué sirve la lista `[tasks]` que imprime el worker al arrancar?

12. Redis contra RabbitMQ: ¿por qué usamos Redis en la materia y cuándo elegirías el otro?

---

## Bloque 3: lo que viaja

13. ¿Qué contiene exactamente el mensaje que queda en la cola?

14. ¿Viaja el código de la función? Entonces, ¿cómo sabe el worker qué ejecutar?

15. ¿Qué pasa si encolás una tarea que el worker no tiene registrada?

16. Un worker corre en otra máquina. ¿Qué necesita esa máquina además de Celery?

17. ¿Por qué los argumentos tienen que ser serializables a JSON?

18. Enunciá la regla "pasá IDs, no objetos" y dame **dos** razones distintas: una de tamaño y una de frescura del dato.

---

## Bloque 4: AsyncResult

19. ¿Qué devuelve `delay()`?

20. Completá la correspondencia con la clase 22:

| `Future` | `AsyncResult` |
|---|---|
| `submit()` | ? |
| `result()` | ? |
| `done()` | ? |

21. ¿Dónde vive el estado de un `AsyncResult`?

22. Tengo solo un id en un archivo de texto. ¿Puedo saber el resultado? ¿Cómo?

23. ¿Qué significa el estado `PENDING`? (Cuidado: no es lo que parece.)

24. Consulto un id que nunca existió. ¿Qué me contesta Celery? ¿Por qué?

25. ¿Cómo harías para distinguir "encolada" de "este id no existe"?

---

## Bloque 5: fallas

26. Una tarea levanta `ZeroDivisionError` en el worker. ¿Qué estado queda y qué hay en `result`?

27. ¿Qué hace `get()` sobre una tarea que falló?

28. El traceback se generó en otro proceso, quizá en otra máquina. ¿Cómo llega hasta el programa que consulta?

29. En la clase 22, una excepción en un `Future` abandonado se perdía en silencio. ¿Por qué acá no pasa lo mismo?

30. ¿Queda algún caso en que el error exista pero nadie se entere?

---

## Bloque 6: escalar

31. Nombrá las tres formas de duplicar la capacidad de procesamiento.

32. ¿Cuál de las tres no era posible antes de hoy?

33. Levanto dos workers contra el mismo broker. ¿Qué tengo que configurar para que se repartan las tareas?

34. 4 tareas de 2 s con `--concurrency=2`: ¿cuánto tarda? ¿Y con `--concurrency=4`?

35. Con `--concurrency=8` y solo 4 tareas, ¿mejora respecto de 4? ¿Por qué no?

36. ¿Cuánto más caro es `delay()` que `submit()`? ¿Qué se compra con esa diferencia?

---

## Pregunta integradora

Tenés una API que recibe pedidos de generación de reportes PDF. Cada reporte tarda entre 30 segundos y 5 minutos. Los usuarios suben el pedido desde el navegador y quieren poder cerrar la pestaña y volver más tarde a buscarlo.

Diseñá la solución completa: qué responde la API al recibir el pedido, qué se guarda y dónde, cómo averigua el usuario si ya está listo, qué pasa si el servidor de la API se reinicia a mitad de camino, y qué pasa si un worker se muere mientras genera un reporte.

Justificá cada decisión con lo de hoy y con las clases 19, 21 y 22.

---

## Si dudaste

| Dudaste en | Repasá |
|---|---|
| 1 a 5 | La introducción y la demostración de los tres pasos |
| 6 a 12 | La sección "Las tres piezas" y el banner del worker |
| 13 a 18 | "Lo que viaja por la cola" |
| 19 a 25 | "AsyncResult: el Future que vive afuera" |
| 26 a 30 | "Cuando la tarea falla", y la clase 22 (el bug silencioso) |
| 31 a 36 | "Escalar: el punto de todo esto" |

---

*Computación II - 2026 - Clase 23*
