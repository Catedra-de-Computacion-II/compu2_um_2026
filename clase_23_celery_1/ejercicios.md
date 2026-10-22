# Clase 23: Celery I - Ejercicios Prácticos

Los archivos `tareas.py`, `encolar.py`, `consultar.py` y `docker-compose.yml` acompañan la clase.

## Antes de empezar

```bash
pip install celery redis
docker compose up -d
docker compose exec redis redis-cli ping      # PONG
```

Y en una terminal aparte, cuando haga falta:

```bash
celery -A tareas worker --loglevel=info --concurrency=2
```

---

## Ejercicio 1: El salto de escala (obligatorio)

### Objetivo

Comprobar que una tarea sobrevive al proceso que la encoló. Es la propiedad que ningún `Future` tiene.

### Parte A: los tres pasos

Hacelo **sin ningún worker corriendo**.

```bash
python3 encolar.py
docker compose exec redis redis-cli LLEN celery
python3 consultar.py
```

1. ¿Qué estado tiene la tarea? ¿Cuánto vale `LLEN celery`?
2. Si `LLEN` te dio 0, ¿qué pasó? Arreglalo y repetí.
3. Ahora arrancá el worker en otra terminal. ¿Cuánto tarda en tomar la tarea?
4. Volvé a correr `python3 consultar.py`. Copiá el estado y el resultado.
5. Escribí en dos renglones por qué esto es imposible con `ThreadPoolExecutor`.

### Parte B: el mensaje

6. Encolá una tarea sin worker y mirá el mensaje crudo:

```bash
docker compose exec redis redis-cli LINDEX celery 0
```

7. Decodificá el `body` (está en base64). ¿Qué hay adentro?
8. ¿Aparece el **código** de la función en algún lado del mensaje?
9. Entonces, ¿cómo sabe el worker qué ejecutar?
10. ¿Qué pasa si el worker no tiene el `tareas.py`? Probalo: arrancá un worker desde otro directorio.

### Parte C: el id como recibo

11. Guardá un id, bajá el worker, bajá el broker (`docker compose down`), volvé a levantar todo y consultá ese id. ¿Sigue estando el resultado?
12. ¿Por qué? ¿Dónde vivía?
13. Probá `python3 consultar.py --inventado`. ¿Qué estado devuelve un id que nunca existió?
14. ¿Cómo distinguirías "está en la cola" de "este id no existe"?

---

## Ejercicio 2: Estados y fallas

### 2.1 El recorrido

1. Encolá una tarea de 10 segundos y consultá su estado cada 2 segundos. Anotá la secuencia de estados que ves.
2. ¿Viste `STARTED`? Por default Celery no lo reporta. Buscá en la documentación `task_track_started` y activalo. Repetí.
3. ¿Qué devuelve `ready()` cuando la tarea falló?

### 2.2 Las excepciones

```bash
python3 encolar.py --falla
python3 consultar.py
```

4. ¿Qué estado tiene? ¿Qué hay en `result`?
5. ¿De dónde salió el traceback que imprime, si el error ocurrió en otro proceso?
6. Compará con el bug silencioso de la clase 22: ahí la excepción se perdía. ¿Por qué acá no?
7. Probá `python3 consultar.py --esperar` con la tarea que falla. ¿Qué hace `get()`?
8. Buscá `get(propagate=False)`. ¿Para qué sirve?

### 2.3 Sin backend

9. Comentá el `backend=` en `tareas.py`, reiniciá el worker y encolá algo. ¿Qué pasa al consultar?
10. ¿En qué casos conviene **no** tener backend?

---

## Ejercicio 3: Concurrencia y escalado

### 3.1 Medir

```bash
python3 encolar.py --varias
time python3 consultar.py --esperar
```

1. Con `--concurrency=2`, ¿cuánto tardan 4 tareas de 2 s? ¿Cuánto sería secuencial?
2. Subí a `--concurrency=4` y repetí. ¿Ahora cuánto?
3. Con `--concurrency=8` y 4 tareas, ¿mejora? ¿Por qué no?

### 3.2 Dos workers

4. Levantá **dos** workers con `--concurrency=1` cada uno, en dos terminales.
5. Encolá 6 tareas. Mirá los dos logs: ¿cómo se repartieron?
6. ¿Tuviste que configurar algo para que se repartan? ¿Por qué no?
7. Matá un worker en medio del procesamiento (Ctrl+C). ¿Qué pasa con la tarea que estaba ejecutando?
8. Probá con `kill -9` en lugar de Ctrl+C. ¿Cambia algo? Relacionalo con las señales de la clase 6.

### 3.3 El tipo de pool

9. El banner dice `concurrency: 2 (prefork)`. ¿Qué significa prefork? ¿Qué clase vimos eso?
10. Arrancá con `--pool=threads`. ¿Cuándo convendría cada uno? (Pensá en la clase 10 y el GIL.)
11. ¿Qué pool usarías para tareas de descarga? ¿Y para hashear archivos?

---

## Ejercicio 4: Lo que se puede y no se puede mandar

1. Intentá encolar una tarea pasándole un objeto `datetime`. ¿Funciona? Mirá el mensaje con `LINDEX`: ¿en qué se convirtió?
2. Probá con un `set`. ¿Y una lista de listas? Una de las dos falla: ¿por qué esa y no la otra?
3. Definí una clase propia y pasá una instancia. ¿Qué error da?
4. ¿Por qué la restricción es más estricta que la del pickle en la clase 22?
5. Escribí una tarea que reciba un `id` y una que reciba el objeto entero (simulalo con un diccionario grande). Medí la diferencia de tamaño del mensaje con `LINDEX`.
6. Explicá la regla "pasá IDs, no objetos" con dos argumentos distintos: uno de tamaño y uno de **frescura del dato**.

---

## Ejercicio 5: Una API que no hace esperar

Juntá la clase 19 con la de hoy.

1. Tomá tu `api.py` de la clase 19.
2. Agregá `POST /trabajos`, que encole una tarea de Celery y responda **`202 Accepted`** con el id.
3. Agregá `GET /trabajos/{id}`, que devuelva el estado consultando el `AsyncResult`.
4. Probá: encolá un trabajo de 10 segundos y pedí el estado tres veces mientras corre.
5. Matá el servidor de la API mientras la tarea está corriendo. Levantalo de nuevo y consultá el id. ¿Sigue ahí el resultado?
6. Esa última prueba es el punto de la clase. Explicá por qué con el executor de la clase 22 no funcionaría.

---

## Verificación del ejercicio obligatorio

### Ejercicio 1: El salto de escala

- [ ] Los tres pasos corriendo, con el `LLEN celery` en 1 sin workers
- [ ] El estado y el resultado de la tarea huérfana, consultados desde un tercer proceso
- [ ] Explicaste por qué es imposible con `ThreadPoolExecutor`
- [ ] Decodificaste el mensaje y dijiste qué viaja y qué no
- [ ] Probaste qué pasa cuando el worker no tiene el código de la tarea
- [ ] Probaste que el resultado sobrevive a bajar y levantar todo
- [ ] Probaste la trampa de `PENDING` con un id inventado

---

## Ejercicios adicionales

### Espiar la cola

Escribí un script que muestre cada segundo cuántas tareas hay en la cola (`LLEN celery`) mientras encolás 20 tareas lentas. Es el monitoreo más básico posible, y la semana que viene lo vamos a reemplazar por Flower.

### Dos colas

Buscá cómo enviar tareas a colas distintas (`queue=`) y levantá un worker que consuma solo de una. Es la base del ejercicio de prioridades.

### El worker que no conoce la tarea

Armá deliberadamente el error: encolá `tareas.sumar` y levantá un worker que solo tenga registrada `lenta`. ¿Qué dice el log del worker? ¿Qué pasa con el mensaje?

### Cuánto cuesta el broker

Medí cuánto tarda `sumar.delay(2, 3)` en volver (solo el encolado, no el resultado). Compará con un `submit()` de `ThreadPoolExecutor` de la clase 22. Esa diferencia es lo que se paga por tener la cola afuera.

---

*Computación II - 2026 - Clase 23*
