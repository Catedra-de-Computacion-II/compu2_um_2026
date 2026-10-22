# Clase 24: Celery II - Extra Manijas

Material opcional para profundizar. Es el último del año.

---

## PID 1, o por qué matar un proceso en un contenedor es raro

Vale la pena contar un experimento que **salió mal**, porque lo que enseña es más interesante que lo que iba a demostrar.

La idea era comprobar que con `acks_late=True` una tarea interrumpida se reejecuta. El plan: encolar una tarea de 40 segundos y matar el worker a mitad.

```bash
docker compose exec worker sh -c 'kill -9 1'
```

El resultado:

```
received:  1
succeeded: 1
recibida 12:07:54 -> completada 12:08:34   (40s exactos)
RestartCount: 0
```

La tarea **terminó normalmente** y el contenedor nunca se reinició. El `kill -9 1` no mató nada relevante.

La razón es la estructura de procesos adentro del contenedor. El PID 1 es el proceso que lanzó el `command`, pero Celery con el pool prefork levanta un padre y N hijos (la clase 9, otra vez). Matar al padre no mata a los hijos, y el hijo que estaba ejecutando la tarea siguió hasta terminarla.

De paso, eso explica una rareza que conviene conocer: **el PID 1 de un contenedor es especial**. En Linux, el PID 1 tiene un tratamiento distinto: las señales que no tiene manejador explícito **no lo matan**. Es una protección del kernel, pensada para `init`, que se hereda en los contenedores porque un contenedor es un namespace de PIDs con su propio PID 1.

De ahí salen dos consecuencias prácticas:

- `docker stop` manda SIGTERM al PID 1 y espera 10 segundos antes del SIGKILL. Si tu proceso no maneja SIGTERM, se come los 10 segundos enteros y después muere a lo bruto.
- Un PID 1 que no entierra a sus hijos deja zombies, porque es él quien hereda los huérfanos. Es exactamente el problema de la clase 5, y la solución en Docker es el flag `--init`, que mete un `init` mínimo como PID 1 que sí hace `wait()`.

Celery maneja SIGTERM correctamente (es el *warm shutdown* que medimos en la clase 23), así que `docker compose stop worker` hace lo correcto: deja que termine lo que está haciendo.

Para matar de verdad el worker completo y ver la recuperación:

```bash
docker compose kill -s SIGKILL worker
```

Eso mata el contenedor entero, hijos incluidos. La documentación de Celery dice que con `acks_late=True` el mensaje, al no haber sido confirmado, vuelve a estar disponible y otro worker lo toma. Vale probarlo y verificarlo ustedes: es un buen ejercicio, y es el tipo de afirmación que conviene no creer hasta verla.

---

## Por qué Beat no se puede escalar

Celery Beat es el programador de tareas periódicas: "esta tarea, cada 5 minutos".

```bash
celery -A tareas beat
```

Y es el único servicio del sistema que **no se puede escalar**. Si levantás dos Beat con el mismo cronograma, cada tarea se encola **dos veces**. Tres Beat, tres veces.

La razón es que Beat no coordina con nadie: cada instancia lleva su propio reloj y su propio archivo de estado (`celerybeat-schedule`), y a la hora señalada encola. No hay elección de líder, no hay lock distribuido.

Es el problema de la clase 11 en su forma más incómoda: varios procesos que quieren hacer una acción **exactamente una vez**, sin un mecanismo de exclusión mutua entre ellos. Y la solución estándar es la misma: un lock. Lo que pasa es que acá el lock tiene que ser distribuido, y eso es un problema en sí mismo.

Las salidas, en orden de simplicidad:

- **Una sola instancia de Beat.** Lo que se hace casi siempre. El costo es que si se cae, no se encola nada hasta que vuelva.
- **`celery beat` con un backend de lock**, como `celery-redbeat`, que guarda el cronograma en Redis y usa un lock para que solo uno encole.
- **Delegarlo afuera**: un cron del sistema o un CronJob de Kubernetes que llame a un endpoint. Mueve el problema a una herramienta que ya lo resolvió.

Lo que vale retener: **la periodicidad es un recurso único**, igual que un puerto. Y los recursos únicos no escalan horizontalmente sin coordinación.

---

## Lo que falta para escalar la API

En la clase dijimos que la API no se puede escalar porque choca el puerto. Eso es cierto pero incompleto: el puerto es el síntoma, no el problema.

Para tener tres APIs hace falta algo adelante que reparta las conexiones: un **balanceador de carga**. En Compose sería un servicio más, típicamente nginx o Traefik, que publica el 80 y manda cada pedido a una de las tres APIs.

```yaml
nginx:
  image: nginx
  ports:
    - "80:80"
  # con una config que haga proxy_pass a api:8000
```

Y acá pasa algo que vale notar: nginx puede escribir `proxy_pass http://api:8000` sin saber cuántas APIs hay, porque **el DNS interno de Compose resuelve el nombre de un servicio escalado a varias IPs**. El balanceo más simple lo hace el propio resolver.

Lo interesante es que nuestra arquitectura ya es escalable en la parte que importa. La API no guarda nada: recibe, encola, responde. Todo el estado está en el broker. Eso se llama ser **stateless**, y es la condición para poder poner N copias atrás de un balanceador sin que al usuario le importe cuál le tocó.

Si la API guardara los trabajos en un diccionario en memoria —como hacía el ejemplo de la clase 19 antes de tener Celery— tres copias serían tres realidades distintas, y el usuario que consulta su id tendría dos de cada tres chances de que le digan "no existe".

De ahí sale el criterio general: **lo que se escala horizontalmente tiene que ser stateless, y el estado se empuja a un servicio compartido.** Es la misma idea que hizo escalables a los workers.

---

## Las colas son más que una

Todo el año usamos una sola cola, llamada `celery`. Se pueden tener varias, y es la herramienta para resolver un problema concreto.

El problema: una tarea de 40 minutos y una de 2 segundos en la misma cola. La corta puede quedar atrás de varias largas y tardar una hora en empezar, aunque se ejecute en dos segundos.

La solución es separarlas:

```python
app.conf.task_routes = {
    'tareas.hashear': {'queue': 'pesada'},
    'tareas.esperar': {'queue': 'rapida'},
}
```

Y dedicar workers a cada una:

```yaml
worker_rapido:
  command: celery -A tareas worker -Q rapida --concurrency=4

worker_pesado:
  command: celery -A tareas worker -Q pesada --concurrency=2
```

Ahora las tareas cortas tienen cuatro slots que ninguna tarea larga puede ocupar.

Esto es *prioridad por partición*, y es distinto de una cola de prioridad. Una `PriorityQueue` (clase 21) ordena **dentro** de una cola, y tiene el problema de la inanición: una tarea de baja prioridad puede esperar para siempre. Separar en colas con workers dedicados garantiza capacidad reservada para cada clase de trabajo, lo que en general es lo que uno quiere.

Y conectado con lo anterior: cada worker solo ejecuta las tareas de su cola, pero **todos tienen el código de todas**. La imagen es la misma; el `-Q` solo decide de dónde consume.

---

## Lo que dejamos afuera

Vale nombrar lo que existe y no vimos, para que sepan que está y qué buscar.

**Rate limiting.** `@app.task(rate_limit='10/m')` limita a 10 ejecuciones por minuto. Para no pasarse del límite de una API de terceros.

**Time limits.** `task_time_limit` mata una tarea que se pasó de tiempo; `task_soft_time_limit` le manda una excepción antes para que limpie. Sin eso, una tarea colgada ocupa un slot para siempre.

**`max_tasks_per_child`.** Recicla el proceso worker cada N tareas. Es la defensa contra las fugas de memoria: si una biblioteca pierde memoria de a poco, reiniciar el proceso cada 100 tareas lo resuelve sin arreglar la biblioteca.

**Revocar tareas.** `AsyncResult.revoke(terminate=True)` cancela una tarea. Con la misma limitación que vimos en la clase 22: si ya está ejecutando, hace falta `terminate=True`, que manda una señal al proceso — y eso trae todos los problemas de la clase 6.

**Resultados grandes.** Guardar un resultado de 50 MB en Redis es mala idea: Redis es memoria. El patrón es escribir el resultado donde corresponda (disco, S3, la base) y devolver la ruta.

**Monitoreo de verdad.** Flower sirve para mirar; para alertar hace falta exportar métricas a algo tipo Prometheus. La señal más importante es el **tamaño de la cola a lo largo del tiempo**: si sube y no baja, el sistema no da abasto y hay que agregar workers. Es el equivalente, en este nivel, del "atraso del event loop" que medimos en la clase 21.

---

## El año, en una idea

Si hay algo que llevarse del cuatrimestre, es que todos los problemas de concurrencia son el mismo puñado de problemas, y reaparecen en cada nivel de escala con nombres distintos.

Dos procesos que quieren escribir el mismo archivo, dos threads que incrementan el mismo contador, dos corrutinas que leen un saldo antes de modificarlo, y dos workers de Celery que cobran el mismo pedido: **son el mismo problema**. Lo resolvimos con `flock`, con `Lock`, con `asyncio.Lock` y con idempotencia, y las cuatro soluciones son la misma idea aplicada a un contexto distinto.

Lo mismo con repartir trabajo: un pool de procesos, una `Queue` con workers, un `TaskGroup`, un executor, un broker. Y con comunicar: pipes, memoria compartida, sockets, mensajes JSON.

Eso es lo que hace que un sistema distribuido sea aprendible. No es que sea simple: es que es **las mismas ideas, otra vez**, con la red en el medio y las fallas que la red trae.

---

## Lecturas

- [Celery: Periodic Tasks](https://docs.celeryq.dev/en/stable/userguide/periodic-tasks.html) — Beat, y la advertencia sobre una sola instancia.
- [Celery: Routing](https://docs.celeryq.dev/en/stable/userguide/routing.html) — varias colas, y el ruteo por tipo de tarea.
- [Celery: Workers](https://docs.celeryq.dev/en/stable/userguide/workers.html) — revocar, time limits, `max_tasks_per_child`.
- [The Twelve-Factor App](https://12factor.net/) — en particular los factores sobre procesos stateless y configuración por entorno. Es viejo y sigue siendo la mejor síntesis de por qué estas decisiones son las que son.
- [Docker: PID 1 y señales](https://docs.docker.com/reference/dockerfile/#entrypoint) — buscá la parte de `--init` y los zombies.

---

*Computación II - 2026 - Clase 24*
