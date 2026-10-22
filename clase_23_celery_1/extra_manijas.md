# Clase 23: Celery I - Extra Manijas

Material opcional para profundizar.

---

## La promesa que no es tan fuerte: acks_late

En la clase dijimos que la tarea "sobrevive al proceso". Es verdad, pero hay un caso donde se pierde, y conviene conocerlo porque el default de Celery no es el que uno esperaría.

El experimento: un worker con `--concurrency=1`, una tarea de 30 segundos, y a los 4 segundos lo matamos con `kill -9`.

```bash
celery -A tareas worker --concurrency=1    # terminal 1
python3 -c "from tareas import lenta; print(lenta.delay(30).id)"
# esperar 4 segundos y:
kill -9 <pid del worker>
```

Resultado medido:

```
cola:   LLEN celery -> 0
estado: PENDING
result: None
```

La tarea **desapareció**. No quedó en la cola, no se reejecutó, y su estado es `PENDING` para siempre. Nadie la va a hacer nunca y nadie va a enterarse.

La razón está en una opción que por default viene así:

```python
>>> app.conf.task_acks_late
False
```

El protocolo del broker tiene una confirmación: el worker avisa "este mensaje ya es mío, borralo de la cola". La pregunta es *cuándo* avisa. Con `acks_late=False` —el default— avisa **al recibir** el mensaje. Con `acks_late=True`, avisa **al terminar** la tarea.

```python
app.conf.task_acks_late = True
```

Con eso, si el worker muere a mitad de camino, el mensaje nunca se confirmó, sigue en el broker, y otro worker lo toma. La tarea no se pierde.

¿Por qué no es el default, entonces? Porque mueve el problema en lugar de eliminarlo. Con `acks_late=True`, una tarea que hace morir al worker —por memoria, por un bug— se va a reejecutar, va a volver a matarlo, y así para siempre. Es el *poison message*: un mensaje que tumba a todo worker que lo toque.

La disyuntiva no tiene salida gratis y cada sistema la resuelve distinto:

| | `acks_late=False` (default) | `acks_late=True` |
|---|---|---|
| Worker muere a mitad | la tarea se pierde | se reejecuta |
| Garantía | *at most once* | *at least once* |
| Riesgo | perder trabajo | duplicar trabajo, poison messages |

Esos dos nombres —*at most once* y *at least once*— son el vocabulario estándar de los sistemas de mensajería. Y falta el tercero que todo el mundo quiere: *exactly once*. La respuesta corta es que no existe en un sistema distribuido con fallas; la larga es el teorema de los Two Generals. Lo que se hace en la práctica es elegir *at least once* y hacer las tareas **idempotentes**, de modo que ejecutar dos veces dé el mismo resultado que ejecutar una. Eso lo vemos la clase que viene.

Una nota de honestidad sobre el `kill -9`: con `Ctrl+C` (SIGTERM) el worker hace *warm shutdown*, termina lo que está haciendo y recién entonces sale. La pérdida pasa cuando el proceso no tiene oportunidad de limpiar — lo que, en una máquina real, es exactamente lo que hace el OOM killer. Es la clase 6 otra vez: hay una señal que se puede manejar y una que no.

---

## prefetch: por qué un worker ocupado acapara tareas

Otro default que sorprende:

```python
>>> app.conf.worker_prefetch_multiplier
4
```

Un worker no pide una tarea a la vez: pide `concurrency * 4`. Con `--concurrency=2`, se reserva 8 mensajes aunque solo pueda ejecutar 2.

La idea es buena: si cada tarea dura milisegundos, ir al broker por cada una sería ridículo —es el mismo problema del `chunksize` de la clase 22, con la red en lugar del pipe.

El problema aparece con tareas largas y desparejas. Imaginá dos workers y diez tareas, ocho cortas y dos de diez minutos. El primer worker llega primero, se reserva ocho mensajes, y entre ellos caen las dos largas. El segundo worker se queda con dos tareas cortas, las termina en un segundo, y después **mira el techo** mientras el primero sigue con las largas y con seis cortas reservadas que no puede empezar.

Los mensajes reservados no se le pueden pasar a nadie: ya son de ese worker.

Para tareas largas, entonces:

```bash
celery -A tareas worker --prefetch-multiplier=1
```

Y la regla general: **tareas cortas y parejas, prefetch alto; tareas largas o desparejas, prefetch 1**. Es el mismo criterio que el `chunksize` de la clase pasada, y por la misma razón: amortizar el transporte contra el riesgo de repartir mal.

---

## El id lo elige quien encola (y eso sirve)

Celery genera un UUID para cada tarea, pero se puede imponer:

```python
sumar.apply_async(args=(2, 3), task_id='reporte-usuario-42-2026-10')
```

Parece un detalle y resuelve un problema concreto: **evitar encolar dos veces lo mismo**. Si el id es determinístico —derivado de qué se está pidiendo, no de cuándo— entonces un doble click del usuario genera el mismo id, y podés chequear si ya existe antes de encolar.

Es la versión más simple de un *lock distribuido*, y conecta con el problema de la clase 11: dos pedidos concurrentes que quieren hacer el mismo trabajo. Allá el recurso compartido era una variable y el lock un `threading.Lock`; acá el recurso es "el trabajo de generar el reporte 42" y el lock es la unicidad del id en el broker.

La advertencia: `AsyncResult` de un id reutilizado te va a dar el resultado de la ejecución *anterior*, porque el backend indexa por id. Si usás ids determinísticos, los resultados también se confunden entre ejecuciones.

---

## Por qué JSON y no pickle

Celery soporta pickle como serializador, y desde la versión 4 viene **deshabilitado**:

```python
>>> app.conf.accept_content
('json',)
```

La razón es de seguridad, y es grave. Deserializar un pickle **ejecuta código**: el formato incluye instrucciones para reconstruir objetos, y esas instrucciones pueden ser cualquier cosa.

Si tu broker acepta pickle, entonces cualquiera que pueda escribir un mensaje en la cola puede ejecutar código arbitrario en todos tus workers. Y los brokers suelen quedar expuestos: un Redis sin contraseña en una red interna es el caso clásico.

Con JSON, el peor escenario es que se deserialice un diccionario raro. Es una elección de diseño que vale la pena notar: se resignó poder expresivo —no se puede mandar cualquier objeto Python— para cerrar una clase entera de vulnerabilidades.

Lo que se gana en la práctica, además, es portabilidad: un mensaje JSON lo puede encolar un programa que no sea Python. Hay clientes de Celery para Node y Go que funcionan justamente porque el formato del mensaje es abierto y documentado — el que decodificamos a mano en clase.

Y el costo: por eso los argumentos no pueden ser un `set`.

```python
sumar.delay({1, 2}, 1)
# EncodeError: Object of type set is not JSON serializable
```

Un `datetime`, en cambio, sí pasa: Celery lo convierte a ISO 8601 y del otro lado llega como string. Conviene saberlo, porque la tarea recibe algo de un tipo distinto al que mandaste.

---

## Las colas son del broker, no de los workers

Una consecuencia del diseño que vale explicitar porque explica el escalado "mágico" de la clase.

Cuando levantás dos workers contra el mismo broker, no hay negociación entre ellos. Ninguno sabe cuántos hermanos tiene (el `mingle: all alone` del banner es solo para sincronizar relojes y revocaciones). Los dos hacen lo mismo: **le piden trabajo al broker**.

El reparto, entonces, no lo hace Celery: lo hace la semántica de la cola. Un `BRPOP` de Redis sobre la misma lista desde dos clientes entrega cada elemento **a uno solo**. El reparto es una propiedad de la estructura de datos, no un algoritmo de coordinación.

Por eso agregar un worker no requiere configurar nada, y por eso no hay un "coordinador" que pueda caerse. Es el mismo principio que la `queue.Queue` de la clase 10 repartiendo entre threads, llevado a la red: los consumidores no se conocen, solo comparten la cola.

Y de ahí sale también la respuesta a "¿quién decide qué worker hace qué?": nadie. El primero que pide, recibe.

---

## Flower, para la próxima

Hasta ahora miramos el broker con `redis-cli LLEN` y el estado con `AsyncResult`. Es suficiente para entender el mecanismo y completamente impracticable en producción.

Flower es un dashboard web que se conecta al mismo broker y muestra workers activos, tareas en vuelo, tiempos, tasas de falla e historial:

```bash
pip install flower
celery -A tareas flower       # http://localhost:5555
```

Vale la pena levantarlo antes de la clase que viene y encolar unas cuantas tareas mirando la pantalla. Es la diferencia entre entender el mecanismo y poder operarlo.

---

## Lecturas

- [Celery: Optimizing](https://docs.celeryq.dev/en/stable/userguide/optimizing.html) — prefetch, acks y los defaults, explicados por quienes los eligieron.
- [Celery: Task Options](https://docs.celeryq.dev/en/stable/userguide/tasks.html#task-options) — la lista completa de lo que se le puede pedir a una tarea.
- [Celery: Security](https://docs.celeryq.dev/en/stable/userguide/security.html) — por qué pickle está deshabilitado, y qué más hay que cerrar.
- "The Two Generals Problem" — el resultado teórico detrás de que *exactly once* no exista. Corto y vale la pena.
- [Celery: Routing](https://docs.celeryq.dev/en/stable/userguide/routing.html) — para quien quiera ver cómo se mandan tareas a colas distintas, que es el camino hacia las prioridades.

---

*Computación II - 2026 - Clase 23*
