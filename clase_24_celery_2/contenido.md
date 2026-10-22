# Clase 24: Celery II - Orquestación y producción

## Introducción: el sistema completo

La clase pasada Celery funcionó, pero con una coreografía incómoda: tres terminales, un worker lanzado a mano, un `localhost:6399` escrito en el código. Sirve para entender el mecanismo y no sirve para nada más.

Hoy cerramos las dos puntas del año.

La primera es **Docker Compose**: el sistema entero —API, broker, workers, dashboard— levantado con un comando, escalado con un flag. Eso es un arco que abrimos en la clase 1 con contenedores sueltos y que recién hoy se puede cerrar, porque hasta ahora no teníamos un sistema de varias piezas que valiera la pena orquestar.

La segunda es lo que separa una demostración de algo que se puede dejar corriendo: **componer tareas**, **sobrevivir a las fallas** y **poder ver qué está pasando**.

> **Nota:** el directorio `proyecto/` tiene el sistema completo. Es el código que vamos a correr toda la clase.

---

## Parte 1: Orquestar

### El sistema como un solo objeto

Esto es todo el sistema:

```yaml
services:
  redis:
    image: redis:7
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 3s
      retries: 10

  api:
    build: .
    command: uvicorn api:api --host 0.0.0.0 --port 8000
    ports:
      - "8000:8000"
    environment:
      BROKER_URL: redis://redis:6379/0
    depends_on:
      redis:
        condition: service_healthy

  worker:
    build: .
    command: celery -A tareas worker --loglevel=info --concurrency=2
    environment:
      BROKER_URL: redis://redis:6379/0
    depends_on:
      redis:
        condition: service_healthy

  flower:
    build: .
    command: celery -A tareas flower --port=5555
    ports:
      - "5555:5555"
    environment:
      BROKER_URL: redis://redis:6379/0
```

```bash
docker compose up -d --build
```

```
proyecto-redis-1    running
proyecto-api-1      running
proyecto-worker-1   running
proyecto-flower-1   running
```

Cuatro servicios, un comando. Vale detenerse en cuatro decisiones de ese archivo, porque cada una responde a algo que ya vimos.

### Una imagen, tres roles

La API, el worker y Flower comparten el `build: .` y se diferencian solo por el `command`. Es **la misma imagen** corriendo tres veces con tres comandos distintos.

Eso no es un ahorro casual: es lo que garantiza que el worker tenga exactamente el mismo `tareas.py` que la API. La clase pasada vimos que el código de la tarea no viaja por la cola, y que si el worker no lo tiene, el mensaje queda sin atender. Compartir la imagen es la forma de que ese problema no exista.

### Se encuentran por nombre

Fijate en la URL del broker:

```python
BROKER_URL: redis://redis:6379/0
```

Dos cosas cambiaron respecto de la clase 23. El host dejó de ser `localhost` y pasó a ser **`redis`**, que es el nombre del servicio. Compose crea una red interna y registra cada servicio en su DNS, así que `redis` resuelve al contenedor correcto sin que nadie sepa su IP.

Y el puerto volvió a ser el **6379**, no el 6399. El 6399 era un mapeo al host, para que pudiéramos espiar desde afuera; adentro de la red, los contenedores hablan directo por el puerto real. El mapeo `host:contenedor` no participa en la comunicación interna — y de hecho, en este compose, Redis **no publica ningún puerto**: nadie de afuera necesita entrarle.

La consecuencia: el worker podría estar en otra máquina y lo único que cambiaría es esa URL. El código no.

### depends_on no alcanza, healthcheck sí

Acá hay una trampa clásica. Esto no funciona bien:

```yaml
depends_on:
  - redis
```

`depends_on` solo espera a que el contenedor **arranque**, no a que el servicio de adentro esté listo. Redis tarda una fracción de segundo en aceptar conexiones, y en ese hueco la API ya intentó conectarse y falló.

La forma correcta combina las dos cosas:

```yaml
redis:
  healthcheck:
    test: ["CMD", "redis-cli", "ping"]
    interval: 3s
    retries: 10

api:
  depends_on:
    redis:
      condition: service_healthy
```

Ahora `depends_on` espera a que el healthcheck pase. En el log se ve el orden:

```
Container proyecto-redis-1  Starting
Container proyecto-redis-1  Started
Container proyecto-redis-1  Waiting
Container proyecto-redis-1  Healthy      <- recién acá
Container proyecto-api-1    Starting
```

Es la diferencia entre "el proceso existe" y "el servicio responde", que es exactamente la distinción que hicimos en la clase 12 entre un puerto abierto y un servicio funcionando.

### El que se puede escalar y el que no

Comparemos el servicio `api` con el servicio `worker`:

| | `api` | `worker` |
|---|---|---|
| `ports` | `8000:8000` | — |
| `container_name` | — | — |
| ¿Se puede escalar? | no (choca el puerto) | **sí** |

Un puerto del host lo puede tomar un solo contenedor. Si el worker publicara un puerto, `--scale worker=3` fallaría con *port is already allocated*. Y lo mismo con `container_name`: dos contenedores no pueden llamarse igual.

**Un servicio escalable es un servicio sin recursos únicos del host.** Esa es la regla, y es la razón por la que los workers no tienen ni puerto ni nombre fijo: no les hace falta, porque nadie los llama — ellos van a buscar trabajo al broker.

### Escalar

```bash
docker compose up -d --scale worker=3
```

```
proyecto-worker-1   running
proyecto-worker-2   running
proyecto-worker-3   running
```

Y la API los descubre sin configurar nada:

```bash
curl localhost:8000/salud
```

```json
{"api":"ok","workers":["celery@02d26e79b59f","celery@5d565e155ea7","celery@c4263a10f1af"]}
```

Medido con 6 tareas de 4 segundos:

| Configuración | Slots | Tiempo |
|---|---|---|
| 1 worker, `--concurrency=2` | 2 | **12.22 s** |
| 3 workers, `--concurrency=2` | 6 | **4.22 s** |
| secuencial | 1 | 24 s |

**Mismo código, mismo broker, mismas tareas.** Lo único que cambió fue un número en la línea de comandos. Eso es escalado horizontal, y es lo que veníamos persiguiendo desde la clase 14.

---

## Parte 2: La API que no hace esperar

Con la infraestructura arriba, el patrón de la clase 19 por fin se puede completar.

```python
@api.post("/trabajos", status_code=202)
def crear(trabajo: Trabajo):
    resultado = hashear.delay(trabajo.dato)
    return {
        "id": resultado.id,
        "estado": resultado.state,
        "consultar_en": f"/trabajos/{resultado.id}",
    }
```

El `202 Accepted` es el código correcto y vale justificar por qué. Un `200 OK` sería mentira: el trabajo no está hecho. Un `201 Created` también: no se creó ningún recurso todavía. `202` significa exactamente *"recibí tu pedido, lo voy a hacer, todavía no está"*.

El cliente recibe el id y consulta cuando quiera:

```bash
curl -X POST localhost:8000/trabajos -d '{"tipo":"esperar","dato":"6"}'
```

```
HTTP/1.1 202 Accepted
{"id":"078f04df...","estado":"PENDING","consultar_en":"/trabajos/078f04df..."}
```

```bash
curl localhost:8000/trabajos/078f04df...     # inmediato
{"estado":"STARTED","listo":false}

curl localhost:8000/trabajos/078f04df...     # a los 9 segundos
{"estado":"SUCCESS","listo":true,"resultado":"espere 6s"}
```

Tres propiedades que no teníamos:

- **La API nunca se bloquea.** Responde en milisegundos aunque la tarea tarde minutos.
- **El cliente puede desaparecer.** Cierra la pestaña, vuelve mañana con el id.
- **La API puede reiniciarse.** El estado está en el broker, no en su memoria.

Esa última es la que conviene probar en vivo: encolar algo largo, `docker compose restart api`, y consultar el id. Sigue ahí.

> Un detalle del código: el objeto FastAPI se llama `api`, no `app`, porque `app` ya es el de Celery. De ahí el `uvicorn api:api` del compose — primero el módulo, después el objeto.

### El STARTED que no aparece solo

Arriba se ve `STARTED`, pero por default Celery no lo reporta: la tarea salta de `PENDING` a `SUCCESS` sin avisar que empezó. Hay que pedirlo:

```python
app.conf.task_track_started = True
```

El default es `False` porque reportarlo cuesta una escritura más en el backend por cada tarea. Para un usuario que mira una pantalla esperando, la diferencia entre "en cola" y "ya está trabajando" vale esa escritura.

---

## Parte 3: Componer tareas

Hasta ahora cada tarea fue una isla. Celery tiene un vocabulario —lo llama **Canvas**— para armar flujos de trabajo, y son tres primitivas.

### chain: una después de la otra

```python
from celery import chain

resultado = chain(sumar.s(2, 3), duplicar.s(), duplicar.s()).apply_async()
resultado.get()    # 20
```

El resultado de cada una entra como primer argumento de la siguiente: `(2+3) → 10 → 20`.

Ese `.s()` es una **firma**: la tarea con sus argumentos, pero sin ejecutar. Es lo que permite armar el flujo como un objeto y mandarlo entero. `duplicar.s()` sin argumentos es la pieza que espera recibirlos de la anterior.

Lo importante: el encadenamiento lo maneja el **worker**, no tu programa. Vos mandás el flujo y te vas; si cada paso tarda una hora, no hay nadie esperando.

### group: todas a la vez

```python
from celery import group

resultado = group(sumar.s(i, i) for i in range(4)).apply_async()
resultado.get()    # [0, 2, 4, 6]
```

En paralelo, y los resultados vuelven **en orden de entrada**, no de finalización. Es el `map` de la clase 22, repartido entre máquinas.

### chord: todas a la vez, y después una

```python
from celery import chord

resultado = chord(
    (sumar.s(i, i) for i in range(5)),   # 0, 2, 4, 6, 8
    total.s()                             # recibe [0,2,4,6,8]
).apply_async()
resultado.get()    # 20
```

Un `group` más un callback que recibe **la lista de todos los resultados**. Es el patrón map-reduce, y es lo que permite "procesar 100 archivos en paralelo y después generar un informe con todo".

La tarea final recibe una lista:

```python
@app.task
def total(numeros):
    return sum(numeros)
```

### Dónde ya vimos esto

| Canvas | Lo que ya conocés | Clase |
|---|---|---|
| `chain` | encadenar con el resultado anterior | — |
| `group` | `executor.map` / `asyncio.gather` | 21, 22 |
| `chord` | `gather` y después procesar todo | 21 |
| `.s()` | `functools.partial` | — |

La diferencia con `gather` y `map` es la de siempre: acá el flujo se ejecuta **afuera** y sobrevive a quien lo lanzó.

---

## Parte 4: Cuando las cosas fallan

Esta parte es la que convierte una demo en algo que se puede dejar andando.

### Reintentos

Hay errores transitorios —la red se cayó un segundo, el servicio del otro lado está saturado— donde reintentar es exactamente lo correcto.

La forma explícita:

```python
@app.task(bind=True, max_retries=3)
def inestable(self, exito_cada):
    if random.randint(1, exito_cada) != 1:
        raise self.retry(countdown=2 ** self.request.retries)
    return "salió"
```

`bind=True` hace que el primer parámetro sea `self`, la instancia de la tarea. De ahí salen `self.request.retries` (cuántas veces se reintentó) y `self.retry()` (volver a encolarla).

El `countdown=2 ** retries` es **backoff exponencial**: espera 1 s, después 2 s, después 4 s. Si el servicio del otro lado está caído, martillarlo cada 100 ms empeora las cosas; darle aire creciente le da chance de recuperarse.

La forma declarativa, más corta y la que conviene por default:

```python
@app.task(
    bind=True,
    autoretry_for=(ConnectionError,),
    retry_backoff=True,
    retry_kwargs={'max_retries': 3},
)
def descargar(self, url):
    if 'roto' in url:
        raise ConnectionError(f"no pude conectar a {url}")
    return f"bajé {url}"
```

`autoretry_for` es la clave: reintenta **solo** esos tipos de excepción. Un `ConnectionError` merece reintento; un `ValueError` por datos mal formados, no — reintentarlo 3 veces va a fallar 3 veces y nada más.

Medido con una URL que falla siempre:

```
4 recepciones de la tarea      (el intento original + 3 reintentos)
1 "raised unexpected"          (al agotarse los reintentos)
timestamps: 12:03:33, :34, :35  (los intervalos crecen)
estado final: FAILURE
```

Agotados los reintentos, la excepción queda guardada como cualquier otra falla. Y en la API, el estado intermedio es visible:

```python
elif r.state == 'RETRY':
    respuesta["nota"] = "falló y se está reintentando"
```

### Idempotencia: la que no es opcional

Acá está la idea más importante de la clase, y viene de un problema que ya vimos.

En la clase 23 descubrimos que con el default `acks_late=False`, si el worker muere a mitad de una tarea, esa tarea **se pierde**. La solución era:

```python
app.conf.task_acks_late = True
```

Con eso la tarea no se pierde: otro worker la toma. Pero el precio es que **se puede ejecutar dos veces** —la primera vez quizá llegó a hacer la mitad del trabajo antes de morir.

Y eso, según qué haga la tarea, puede ser un desastre:

```python
@app.task
def cobrar_mal(pedido_id, monto):
    total = db.get('total', 0)
    db['total'] = total + monto
    return db['total']
```

Ejecutada tres veces con el mismo pedido:

```
total acumulado: 100
total acumulado: 200
total acumulado: 300
```

Le cobramos tres veces al mismo cliente. La versión correcta:

```python
@app.task
def cobrar_bien(pedido_id, monto):
    if pedido_id in db:
        return f"pedido {pedido_id} ya estaba cobrado (no hice nada)"
    db[pedido_id] = monto
    return f"cobré {monto} del pedido {pedido_id}"
```

```
cobré 100 del pedido pedido-9
pedido pedido-9 ya estaba cobrado (no hice nada)
pedido pedido-9 ya estaba cobrado (no hice nada)
```

**Idempotente** significa eso: ejecutarla N veces da el mismo resultado que ejecutarla una. La marca por `pedido_id` es lo que lo logra.

La lógica completa es una cadena que vale seguir de punta a punta:

1. Quiero que una tarea no se pierda si el worker muere → `acks_late=True`.
2. Con `acks_late=True`, una tarea puede ejecutarse dos veces.
3. Entonces las tareas **tienen que** ser idempotentes.
4. Si no lo son, elegí: perder trabajo o duplicarlo. **No hay una tercera opción.**

Ese punto 4 no es una limitación de Celery, es un resultado sobre sistemas distribuidos. *Exactly once* —exactamente una vez, garantizado— no existe cuando hay red y fallas en el medio. Lo que se hace en la práctica es elegir *at least once* y volver las tareas idempotentes, que es la forma de que "al menos una" se comporte como "exactamente una".

Cómo lograrlo en la práctica, en orden de preferencia:

- **Chequear antes de actuar**, como arriba. Simple y suficiente casi siempre.
- **Operaciones naturalmente idempotentes**: `UPDATE saldo SET x = 100` se puede repetir; `UPDATE saldo SET x = x + 100` no.
- **Claves únicas en la base**: que el segundo intento falle por constraint.

---

## Parte 5: Ver lo que pasa

Hasta ahora miramos la cola con `redis-cli LLEN` y los estados uno por uno. Eso no escala a un sistema con tres workers y cientos de tareas.

**Flower** es un dashboard web que se conecta al mismo broker:

```yaml
flower:
  build: .
  command: celery -A tareas flower --port=5555
  ports:
    - "5555:5555"
```

```
http://localhost:5555
```

Lo que muestra, y para qué sirve cada cosa:

| Pestaña | Para qué |
|---|---|
| Workers | quiénes están vivos, cuántas tareas tiene cada uno |
| Tasks | el historial, con estados, tiempos y argumentos |
| Broker | cuánto hay encolado — si crece sin bajar, faltan workers |
| Monitor | gráficos de tasa de éxito y falla |

Conviene levantarlo, escalar a 3 workers, encolar 50 tareas y mirar la pantalla. Se ve el reparto en vivo, y se ve que ningún worker coordina con otro.

Y desde la línea de comandos, lo mismo sin navegador:

```bash
celery -A tareas inspect active      # qué se está ejecutando ahora
celery -A tareas inspect stats       # estadísticas por worker
celery -A tareas inspect registered  # qué tareas conoce cada uno
```

Ese último es el que resuelve el error más común: *"encolé la tarea y nadie la ejecuta"*. Si no aparece en `registered`, el worker no tiene el código.

---

## Cierre: el año

Vale mirar para atrás, porque la pregunta fue siempre la misma: **cómo hacer varias cosas a la vez**. Lo que cambió fue el alcance.

| | Unidad de concurrencia | Alcance | Clases |
|---|---|---|---|
| Procesos | el proceso | una máquina | 3-9 |
| Threads | el thread | un proceso | 10-11 |
| Corrutinas | la corrutina | un thread | 18-21 |
| Executors | la tarea | una máquina | 22 |
| Celery | la tarea | **varias máquinas** | 23-24 |

Y los problemas se repitieron en cada nivel, con otra ropa:

- **Coordinar el acceso a algo compartido**: locks (11), `asyncio.Lock` (20), idempotencia (hoy).
- **Repartir trabajo entre varios**: pool de procesos (14), `Queue` (10, 21), el broker (hoy).
- **Qué hacer cuando algo falla**: zombies y señales (5-6), excepciones en futures (22), reintentos (hoy).
- **Cómo pasar datos de un lado a otro**: pipes (5), sockets (13), pickle (22), mensajes JSON (23).

Si hoy Celery resultó razonable, no es porque sea simple: es porque cada pieza ya la habían visto en otro nivel. Eso era el punto del año.

---

## Conceptos clave

1. **Compose orquesta el sistema**: varios servicios, un comando.
2. **Una imagen, varios roles**: mismo `build`, distinto `command`.
3. **Los servicios se encuentran por nombre** en la red interna de Compose.
4. **`depends_on` no espera al servicio**, solo al contenedor: hace falta `healthcheck` con `condition: service_healthy`.
5. **Un servicio escalable no tiene recursos únicos del host**: ni puerto publicado ni `container_name`.
6. **`--scale`**: más workers sin tocar código. Medido: 12.22 s → 4.22 s.
7. **`202 Accepted`**: el código correcto para trabajo asincrónico.
8. **El id es el contrato** entre la API y el cliente.
9. **`task_track_started`**: para ver `STARTED`; por default no se reporta.
10. **`chain`**: en secuencia, cada resultado alimenta la siguiente.
11. **`group`**: en paralelo, resultados en orden de entrada.
12. **`chord`**: un group más un callback que recibe todos los resultados.
13. **`.s()`**: una firma, la tarea con argumentos pero sin ejecutar.
14. **`autoretry_for`**: reintentar solo los errores transitorios.
15. **Backoff exponencial**: esperar cada vez más entre reintentos.
16. **`acks_late=True`** evita perder tareas, pero habilita duplicarlas.
17. **Idempotencia**: ejecutar N veces = ejecutar una. Con `acks_late` no es opcional.
18. ***Exactly once* no existe**: se elige *at least once* más idempotencia.
19. **Flower**: ver workers, colas, historial y tasas de falla.
20. **`inspect registered`**: el diagnóstico de "nadie ejecuta mi tarea".

---

## Cierre del cuatrimestre

- **El TP2 se entrega hoy**, al inicio de la clase.
- Las semanas del **09 al 13/11** son de recuperaciones y firma de regularidades.
- Los requerimientos del final están en `FINAL_REQUERIMIENTOS.md`, en la raíz del repositorio.

---

## Referencias

- [Celery: Canvas](https://docs.celeryq.dev/en/stable/userguide/canvas.html) — chain, group, chord y las firmas, con todos los casos.
- [Celery: Retrying](https://docs.celeryq.dev/en/stable/userguide/tasks.html#retrying) — la referencia de reintentos.
- [Compose: depends_on](https://docs.docker.com/compose/how-tos/startup-order/) — por qué no alcanza y cómo se arregla.
- [Compose: Scale](https://docs.docker.com/reference/cli/docker/compose/up/) — el flag y sus límites.
- [Flower](https://flower.readthedocs.io/) — la documentación del dashboard.

---

*Computación II - 2026 - Clase 24*
