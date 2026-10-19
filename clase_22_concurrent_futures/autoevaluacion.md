# Clase 22: concurrent.futures - Autoevaluación

Respondé sin mirar el apunte. Si una pregunta te deja dudando, ahí está el tema a repasar.

---

## Bloque 1: el Future

1. ¿Qué devuelve `submit()` y cuánto tarda en devolverlo?

2. Enumerá los cuatro estados por los que puede pasar un `Future` y decí cuáles son finales.

3. ¿Cuál de estos métodos bloquea y cuál no: `done()`, `result()`, `cancel()`, `exception()`?

4. ¿En qué estado tiene que estar una tarea para que `cancel()` devuelva `True`?

5. `f.result(timeout=2)` levanta `TimeoutError`. ¿Qué pasó con la tarea?

6. ¿Por qué `done()` devuelve `True` tanto si la tarea salió bien como si falló?

---

## Bloque 2: los patrones de recolección

7. Con `map`, ¿las tareas se ejecutan en orden?

8. Con `map`, ¿los resultados se entregan en orden?

9. Si la primera tarea tarda 10 s y las otras cuatro 0.1 s, ¿cuándo veo el resultado de la quinta con `map`? ¿Y con `as_completed`?

10. ¿Cuál de los dos termina antes el trabajo total?

11. `as_completed` me da futures sueltos. ¿Cómo sé a qué entrada corresponde cada uno?

12. ¿Qué devuelve `wait(futuros, return_when=FIRST_COMPLETED)`?

13. Tengo que escribir los resultados en un CSV donde la fila 3 debe corresponder a la entrada 3. ¿Qué uso?

---

## Bloque 3: las excepciones

14. Una tarea levanta `ValueError` y nadie llama a `result()`. ¿Qué se ve en la consola?

15. ¿Dónde quedó guardada esa excepción?

16. ¿Qué diferencia hay entre `f.exception()` y `f.result()` cuando la tarea falló?

17. Nombrá las tres defensas contra la pérdida silenciosa de errores y decí cuándo conviene cada una.

18. Un `map` sobre 100 entradas donde la número 3 falla: ¿cuántos resultados puedo leer?

19. ¿Por qué las otras 97 tareas se calcularon igual?

20. El callback de `add_done_callback`, ¿en qué thread corre?

---

## Bloque 4: threads o procesos

21. ¿Qué línea hay que cambiar para pasar de threads a procesos?

22. Para cada caso, decí qué executor va y por qué:
   - Descargar 200 páginas web
   - Hashear 200 archivos grandes
   - Leer 200 archivos de disco
   - Consultar 200 veces una base de datos
   - Redimensionar 200 imágenes

23. ¿Por qué una `lambda` funciona con `ThreadPoolExecutor` y no con `ProcessPoolExecutor`?

24. ¿Por qué pasarle una lista de dos millones de enteros a un proceso es caro y a un thread no?

25. Tengo 4 núcleos y 200 descargas. ¿`max_workers=4`? Justificá.

26. ¿Por qué el default de `ThreadPoolExecutor` es mucho más grande que el de `ProcessPoolExecutor`?

---

## Bloque 5: el lugar en el curso

27. `concurrent.futures` no agrega capacidad nueva sobre `threading` y `multiprocessing`. Entonces, ¿qué agrega?

28. ¿Qué relación tiene `run_in_executor` (clase 21) con lo de hoy?

29. ¿Por qué `concurrent.futures` no sirve para hacer un servidor que atienda 10.000 conexiones?

30. En el TP2 vas a usar un executor dentro de una API async. ¿Qué problema resuelve ahí?

---

## Pregunta integradora

Tenés que procesar 5000 imágenes: bajar cada una de una URL, redimensionarla y guardarla en disco. Son tres etapas con perfiles distintos.

Diseñá la solución: qué executor para cada etapa, qué patrón de recolección, cómo manejás las que fallan, y dónde pondrías el límite de concurrencia. Justificá cada decisión con lo de hoy y de las clases 10, 20 y 21.

---

## Si dudaste

| Dudaste en | Repasá |
|---|---|
| 1 a 6 | `futuros.py` y la sección del Future como comprobante |
| 7 a 13 | `patrones.py` y la sección de map contra as_completed |
| 14 a 20 | `errores.py` y la sección de excepciones |
| 21 a 26 | La tabla de threads contra procesos, y la clase 10 (GIL) |
| 27 a 30 | La sección sobre dónde encaja esto en el curso |

---

*Computación II - 2026 - Clase 22*
