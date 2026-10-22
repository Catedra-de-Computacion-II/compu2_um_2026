# Clase 24: Celery II - Autoevaluación

Respondé sin mirar el apunte. Es la última del cuatrimestre: el último bloque integra todo el año.

---

## Bloque 1: orquestación

1. ¿Cuántos servicios tiene el sistema de la clase y cuál es el rol de cada uno?

2. La API, el worker y Flower comparten el `build: .`. ¿Por qué conviene que sea la misma imagen?

3. ¿Qué los diferencia entonces?

4. En `redis://redis:6379/0`, ¿qué es cada parte? ¿De dónde sale el nombre `redis`?

5. ¿Por qué adentro de Compose el puerto es 6379 y no el que mapeamos al host?

6. ¿Por qué el servicio de Redis no publica ningún puerto?

7. `depends_on: [redis]` no alcanza. ¿Qué espera exactamente y qué le falta esperar?

8. ¿Cómo se arregla? Escribí el YAML.

9. ¿Qué distinción de la clase 12 es la misma que "contenedor arrancado" contra "servicio listo"?

---

## Bloque 2: escalar

10. ¿Cuál es el comando para levantar 3 workers?

11. ¿Qué dos cosas no puede tener un servicio para poder escalarse?

12. ¿Por qué el worker se puede escalar y la API no?

13. ¿Qué error exacto da `--scale api=2`?

14. ¿Qué habría que agregar al sistema para poder tener 3 APIs?

15. Con 1 worker de `concurrency=2`, 6 tareas de 4 s tardan 12.22 s. Con 3 workers, 4.22 s. ¿Cuántos slots hay en cada caso?

16. ¿Cuántas líneas de Python hay que cambiar para pasar de uno a otro?

17. Con 6 workers (12 slots) y solo 6 tareas, ¿mejora respecto de 3 workers? ¿Por qué?

18. ¿Tuviste que configurar algo para que los 3 workers se repartan el trabajo? ¿Por qué no?

---

## Bloque 3: la API asincrónica

19. ¿Por qué `202 Accepted` y no `200 OK` ni `201 Created`?

20. ¿Qué devuelve el POST y qué hace el cliente con eso?

21. Nombrá las tres propiedades que esta arquitectura tiene y una API sincrónica no.

22. Reinicio la API mientras una tarea corre. ¿Se pierde el resultado? ¿Por qué?

23. ¿Qué hay que configurar para ver el estado `STARTED`? ¿Por qué no viene por default?

24. El objeto FastAPI se llama `api`, no `app`. ¿Por qué, y qué consecuencia tiene en el comando de uvicorn?

---

## Bloque 4: Canvas

25. ¿Qué hace `chain(a.s(), b.s(), c.s())`? ¿De dónde saca `b` sus argumentos?

26. ¿Qué devuelve un `group` y en qué orden?

27. ¿Qué recibe la tarea final de un `chord`?

28. ¿Qué es una firma? ¿Qué diferencia hay entre `.s()` y `.delay()`?

29. Para cada caso, elegí la primitiva:
   - Convertir 100 imágenes y después armar un zip con todas
   - Validar un pedido, cobrarlo y mandar el mail de confirmación
   - Bajar 50 páginas web
   - Procesar 10 archivos en paralelo y después reportar cuántos fallaron

30. ¿Quién ejecuta el encadenamiento de un `chain`: tu programa o el worker? ¿Por qué importa?

---

## Bloque 5: fallas

31. ¿Qué hace `bind=True` en un decorador de tarea?

32. ¿Qué es el backoff exponencial y por qué conviene?

33. ¿Para qué sirve `autoretry_for`? ¿Qué pasa si no lo especificás?

34. ¿Por qué tiene sentido reintentar un `ConnectionError` y no un `ValueError`?

35. ¿Qué queda guardado cuando se agotan los `max_retries`?

36. ¿Qué significa que una tarea sea idempotente?

37. `acks_late=True` resuelve un problema y crea otro. ¿Cuáles son?

38. Reconstruí la cadena completa de razonamiento: de "no quiero perder tareas" a "mis tareas tienen que ser idempotentes".

39. ¿Por qué no existe *exactly once* en un sistema distribuido?

40. De estas, ¿cuál es idempotente y cuál no?
   - `UPDATE stock SET cantidad = 99 WHERE id = 5`
   - `UPDATE stock SET cantidad = cantidad - 1 WHERE id = 5`
   - `enviar_mail(destino, asunto)`
   - `generar_pdf(reporte_id)` que escribe en `/reportes/{reporte_id}.pdf`

---

## Bloque 6: observar

41. ¿Qué es Flower y a qué se conecta?

42. En el dashboard, ¿cómo se ve "me faltan workers"?

43. ¿Qué comando te dice qué se está ejecutando en este momento?

44. "Encolé una tarea y nadie la ejecuta." ¿Cuál es el comando que diagnostica eso y qué buscás en la salida?

---

## Bloque 7: el año entero

45. Completá la tabla con la unidad de concurrencia y el alcance de cada herramienta:

| Herramienta | Unidad | Alcance |
|---|---|---|
| `multiprocessing` | ? | ? |
| `threading` | ? | ? |
| `asyncio` | ? | ? |
| `ProcessPoolExecutor` | ? | ? |
| Celery | ? | ? |

46. El problema "coordinar el acceso a algo compartido" apareció en tres niveles distintos del año. Nombralos.

47. El problema "repartir trabajo entre varios" apareció en tres formas. ¿Cuáles?

48. Para cada caso, elegí la herramienta y justificá en un renglón:
   - Un servidor de chat con 20.000 conexiones
   - Redimensionar 500 imágenes en tu notebook
   - Un sistema de facturación que procesa cola de trabajos toda la noche, repartida en 4 servidores
   - Leer 100 archivos de disco y sumar sus tamaños
   - Una API que responde rápido pero dispara reportes que tardan 10 minutos

49. ¿Cuál es la pregunta que hay que hacerse para decidir entre un executor y Celery?

---

## Pregunta integradora final

Tenés que diseñar el backend de una plataforma que recibe videos, los transcodifica a tres resoluciones, genera miniaturas, y le avisa al usuario por mail cuando está listo. Hay picos: a veces llegan 500 videos en una hora y a veces ninguno en todo el día. Un transcodificado tarde entre 2 y 40 minutos.

Diseñá el sistema completo. Decí qué servicios hay, qué hace cada uno, cómo se comunican, qué estructura de Canvas usás para el flujo de cada video, qué pasa si un worker muere a mitad de un transcodificado, cómo te asegurás de no mandar el mail dos veces, cómo escalás en los picos, y cómo te enterás de que algo se rompió.

Justificá cada decisión con material del año, citando las clases.

---

## Si dudaste

| Dudaste en | Repasá |
|---|---|
| 1 a 9 | Parte 1, el compose comentado y el healthcheck |
| 10 a 18 | Parte 1, "El que se puede escalar y el que no" |
| 19 a 24 | Parte 2, y la clase 19 (códigos HTTP) |
| 25 a 30 | Parte 3, Canvas |
| 31 a 40 | Parte 4, y la clase 23 (extra: acks_late) |
| 41 a 44 | Parte 5 |
| 45 a 49 | El cierre, y la tabla de decisión de la clase 22 |

---

*Computación II - 2026 - Clase 24*
