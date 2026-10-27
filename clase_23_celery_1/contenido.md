# Clase 23: Celery I - Tareas distribuidas

## Introducción: el límite que no habíamos cruzado

Todo lo que hicimos este año tuvo una frontera invisible: **el proceso**.

Los threads de la clase 10 viven dentro de un proceso. Los procesos hijos de la clase 9 son hijos de *ese* proceso. El event loop de la clase 20 corre en un proceso. El `ProcessPoolExecutor` de la clase 22 crea procesos, sí, pero los crea él, en la misma máquina, y cuando el programa termina se van con él.

Esa frontera tiene tres consecuencias que no se arreglan con más concurrencia:

- **Si el proceso muere, el trabajo pendiente se pierde.** La cola estaba en memoria.
- **No se puede escalar más allá de la máquina.** Agregar workers significa agregar núcleos, y los núcleos se terminan.
- **Quien encola tiene que seguir vivo.** Un `Future` solo existe mientras exista el proceso que lo creó.

Celery cruza esa frontera. La idea es la misma de siempre —encolar trabajo, recibir un recibo, consultar después el resultado— pero la cola deja de estar en memoria y pasa a estar **en un servidor aparte**. Y ahí cambia todo.

> **Nota:** los archivos `tareas.py`, `encolar.py`, `consultar.py` y `docker-compose.yml` acompañan la clase. Para dejar el entorno andando —Docker, el entorno virtual, las tres terminales y los errores habituales— está `anexo_puesta_en_marcha.md`.

---

## La demostración que resume la clase

Antes de la teoría, el experimento. Son tres pasos y conviene hacerlos en vivo.

**Paso 1.** Sin ningún worker corriendo, encolamos una tarea y el programa se muere inmediatamente:

```python
# encolar.py
from tareas import sumar

resultado = sumar.delay(2, 3)
print(f"encolado: {resultado.id}")
print(f"estado: {resultado.state}")
print("me muero sin esperar")
```

```
encolado: 61e15d75-b826-4770-96ba-59cfa6438a03
estado: PENDING
me muero sin esperar
```

El proceso terminó. No hay ningún `Future`, ningún thread, ningún pool: no queda nada vivo de ese programa.

**Paso 2.** Miramos la cola en el broker:

```bash
docker exec clase23_redis redis-cli LLEN celery
```

```
1
```

La tarea está ahí. Sobrevivió a la muerte de quien la encoló.

> Si te da `0`, tenés un worker corriendo de antes: lo tomó al instante. Bajalo y repetí desde el paso 1 — la gracia del experimento es que no haya nadie para ejecutarla.

**Paso 3.** Ahora —minutos después, si queremos— arrancamos un worker:

```bash
celery -A tareas worker --loglevel=info --concurrency=2
```

```
[2026-10-22 08:46:21,056: INFO/MainProcess] Task tareas.sumar[61e15d75...] received
[2026-10-22 08:46:22,072: INFO/ForkPoolWorker-2] Task tareas.sumar[61e15d75...] succeeded in 1.015s: 5
```

Y desde un tercer programa, consultamos el resultado por su id:

```python
# consultar.py
from celery.result import AsyncResult
from tareas import app

r = AsyncResult("61e15d75-b826-4770-96ba-59cfa6438a03", app=app)
print(r.state, r.result)
```

```
SUCCESS 5
```

**Tres procesos distintos, en tres momentos distintos.** Uno encoló, otro ejecutó, otro leyó el resultado. Ninguno existió al mismo tiempo que los otros. Con `concurrent.futures` esto es imposible, y no por una limitación de la API: es imposible porque el `Future` *es* un objeto en la memoria de un proceso.

Eso es Celery. El resto de la clase explica cómo.

---

## Las tres piezas

Celery no es un servidor. Es una biblioteca que coordina tres cosas, y entender quién es cada una evita el 90% de la confusión inicial.

```
   tu programa              el broker             los workers
  ┌───────────┐          ┌───────────┐          ┌───────────┐
  │  .delay() │─────────>│   cola    │<─────────│  celery   │
  │           │          │  (Redis)  │          │  worker   │
  └───────────┘          └───────────┘          └───────────┘
        │                      ▲                      │
        │   lee el resultado   │   guarda el resultado│
        └──────────────────────┴──────────────────────┘
                     el result backend
```

### El broker: el que guarda la cola

Es un servidor de mensajería. Celery no implementa la cola: la delega. Las dos opciones habituales:

| | Redis | RabbitMQ |
|---|---|---|
| Qué es | base de datos en memoria | broker de mensajería dedicado |
| Instalación | trivial | algo más de configuración |
| Garantías de entrega | buenas | mejores (protocolo AMQP) |
| En esta materia | lo que usamos | mencionado |

Usamos Redis porque se levanta con una línea de Docker y porque además nos sirve de result backend. En producción, cuando las garantías de entrega importan de verdad, RabbitMQ es la opción más sólida.

### El worker: el que ejecuta

Un proceso aparte, que se lanza por línea de comandos y queda esperando trabajo. Cuando arranca imprime algo así:

```
-------------- celery@lenovo v5.6.3
--- ***** -----
-- ******* ---- Linux-6.12.113-x86_64
- *** --- * ---
- ** ---------- [config]
- ** ---------- .> app:         tareas:0x7f7fa0700b10
- ** ---------- .> transport:   redis://localhost:6399/0
- ** ---------- .> results:     redis://localhost:6399/0
- *** --- * --- .> concurrency: 2 (prefork)
--- ***** -----
 -------------- [queues]
                .> celery           exchange=celery(direct) key=celery

[tasks]
  . tareas.lenta
  . tareas.sumar
```

Vale leerlo con calma, porque cada línea es algo que ya vimos:

- **`transport`** y **`results`**: a qué broker se conecta y dónde deja los resultados.
- **`concurrency: 2 (prefork)`**: cuántas tareas puede ejecutar a la vez, y *cómo*. "Prefork" significa que arranca procesos hijos de antemano —exactamente el patrón de la clase 14— y les reparte el trabajo. El default es un proceso por núcleo.
- **`[queues]`**: de qué colas consume. Por default, una sola llamada `celery`.
- **`[tasks]`**: el registro de tareas que este worker *sabe* ejecutar.

Esa última lista es la fuente del error más común de la semana que viene. Un worker solo puede ejecutar las tareas que tiene registradas; si encolás una que él no conoce, el mensaje queda en la cola y nadie lo atiende.

### El result backend: el que guarda la respuesta

Es **opcional**, y vale entender por qué. El broker lleva el trabajo *hacia* el worker; el backend trae el resultado *de vuelta*. Si no te interesa el resultado —mandar un mail, escribir un log, invalidar un caché— no hace falta backend, y conviene no tenerlo: guardar resultados que nadie va a leer es trabajo y memoria regalados.

Nosotros lo configuramos porque queremos ver los estados.

---

## Lo que viaja por la cola

Acá hay una idea que conviene no pasar por alto, porque explica varias reglas que después parecen arbitrarias.

Miremos el mensaje real que quedó en Redis:

```json
{
  "body": "W1syLCAzXSwge30sIHsiY2FsbGJhY2tzIjogbnVsbCwgLi4ufV0=",
  "content-type": "application/json",
  "headers": {
    "task": "tareas.sumar",
    "id": "61e15d75-b826-4770-96ba-59cfa6438a03",
    "retries": 0,
    "argsrepr": "(2, 3)"
  }
}
```

Y el `body`, decodificado de base64:

```
[[2, 3], {}, {"callbacks": null, "errbacks": null, "chain": null, "chord": null}]
```

Es decir: **args, kwargs y opciones**. Nada más.

Lo que viaja es el *nombre* de la tarea —`"tareas.sumar"`— y sus argumentos. **La función no viaja.** El worker ya tiene el código; lo que recibe es la orden de ejecutar algo que él ya sabe hacer, con estos datos.

De ahí salen tres consecuencias prácticas:

1. **Los argumentos tienen que ser serializables a JSON.** Números, strings, listas, diccionarios. No un objeto de tu modelo, no una conexión a la base, no un file descriptor. Es la misma restricción del pickle en la clase 22, pero más estricta.

2. **El worker y quien encola tienen que compartir el código de las tareas.** Si el worker corre en otra máquina, esa máquina necesita el mismo `tareas.py`. El broker no lo distribuye.

3. **Se pasan IDs, no objetos.** La regla de oro: `procesar_usuario.delay(usuario.id)`, nunca `procesar_usuario.delay(usuario)`. El worker busca el objeto en la base cuando le toca — y así trabaja con el dato fresco, no con una copia de hace diez minutos.

---

## AsyncResult: el Future que vive afuera

`delay()` devuelve un `AsyncResult`, y la comparación con el `Future` de la clase 22 es el mejor camino para entenderlo, porque la API es casi la misma:

| | `Future` (clase 22) | `AsyncResult` (hoy) |
|---|---|---|
| Lo devuelve | `submit()` | `delay()` / `apply_async()` |
| Esperar el valor | `result()` | `get()` |
| ¿Ya terminó? | `done()` | `ready()` |
| Estado | `_state` (interno) | `state` |
| Dónde vive el estado | en memoria del proceso | **en el result backend** |
| Se puede recuperar después | no | **sí, por su id** |

Las dos últimas filas son toda la diferencia. Un `Future` muere con su proceso. Un `AsyncResult` es apenas una *vista* sobre algo que está guardado afuera, y por eso se puede reconstruir desde cero con solo el id:

```python
from celery.result import AsyncResult
from tareas import app

r = AsyncResult("61e15d75-b826-4770-96ba-59cfa6438a03", app=app)
print(r.state)     # SUCCESS
print(r.result)    # 5
```

Ese id es lo único que hay que guardar. Es lo que una API devuelve al cliente cuando acepta un trabajo largo: *"tomá este número, consultá con él más tarde"*. Que es, dicho de otro modo, el patrón del `202 Accepted` de la clase 19 — ahora con la infraestructura que lo hace real.

### Los estados

```
PENDING  ──>  STARTED  ──>  SUCCESS
   │                     └─> FAILURE
   │                     └─> RETRY ──> (vuelve a STARTED)
   └─> REVOKED
```

Hay una trampa con `PENDING` que conviene saber de antemano: **significa "no sé nada de esta tarea"**, no "está en la cola". Si consultás un id inventado, Celery contesta `PENDING`. El backend solo guarda estados a partir de que la tarea termina, así que un id inexistente y un id en cola son indistinguibles.

```python
>>> AsyncResult("id-que-no-existe-jamas", app=app).state
'PENDING'
```

No es un bug: el backend no tiene forma de saber que ese id nunca existió. Si necesitás distinguir los dos casos, el id hay que guardarlo vos cuando encolás.

---

## Cuando la tarea falla

Acá Celery se porta mejor que lo que vimos la clase pasada, y vale compararlo explícitamente.

En la clase 22 descubrimos el bug silencioso: si una tarea falla y nadie llama a `result()`, la excepción **se pierde sin dejar rastro**. Celery no hace eso. La excepción se guarda en el backend, con su traceback:

```python
r = dividir.delay(1, 0)

print(r.state)          # FAILURE
print(r.failed())       # True
print(repr(r.result))   # ZeroDivisionError('division by zero')

r.get()                 # relanza: ZeroDivisionError: division by zero
```

Y el traceback del worker viaja hasta el proceso que consulta:

```python
print(r.traceback.strip().splitlines()[-1])
# ZeroDivisionError: division by zero
```

Eso es más de lo que parece. El error ocurrió **en otro proceso, potencialmente en otra máquina**, y sin embargo lo podemos inspeccionar acá. El worker además lo registró en su propio log. Son dos lugares donde queda constancia, contra los cero de un `Future` abandonado.

Lo que sí sigue valiendo de la clase 22: si nadie consulta nunca ese id y el worker loguea a un archivo que nadie lee, el error existe pero no se entera nadie. La diferencia es que acá **la información está**; en un `Future` abandonado ya no.

---

## Escalar: el punto de todo esto

Veamos qué significa concretamente "escalar". Cuatro tareas de 2 segundos, con un worker configurado con `--concurrency=2`:

```python
from celery import group
from tareas import lenta

res = group(lenta.s(2) for _ in range(4)).apply_async()
res.get(timeout=30)
```

Medido: **4.02 s**. Secuencial habrían sido 8 s. Con dos slots de concurrencia, las cuatro tareas se hacen en dos rondas.

Se puede reproducir con los archivos de la clase:

```bash
python3 encolar.py --varias
time python3 consultar.py --esperar    # real 0m4,019s
```

Ahora la parte interesante. Para duplicar la capacidad hay tres caminos:

```bash
# 1. más concurrencia en el mismo worker
celery -A tareas worker --concurrency=4

# 2. otro worker en la misma máquina
celery -A tareas worker --concurrency=2   # en otra terminal

# 3. otro worker en OTRA máquina
celery -A tareas worker --concurrency=2   # apuntando al mismo broker
```

**Las tres funcionan sin cambiar una línea del código que encola.** La tercera es la que no teníamos: el límite deja de ser la máquina. Y no hay que configurar nada para que los workers se coordinen — se reparten la cola solos, porque la cola es del broker, no de ellos.

Esto es, por fin, el reparto de carga que veníamos armando a mano desde la clase 14. Ahí lo hacíamos con un pool de procesos hijos; después con un executor; hoy el pool puede estar distribuido y nosotros no escribimos el reparto.

---

## El entorno: Redis en Docker

Cerramos el círculo con la clase 1. El broker es un servicio, y los servicios se levantan con Docker:

```yaml
# docker-compose.yml
services:
  redis:
    image: redis:7
    ports:
      - "6399:6379"
```

```bash
docker compose up -d
docker compose exec redis redis-cli ping    # PONG
```

Usamos el puerto 6399 en la máquina para no chocar con cualquier Redis que ya tengas corriendo en el 6379. Adentro del contenedor sigue siendo el 6379: es el mapeo `host:contenedor` de la clase 2.

Y la configuración de la app apunta ahí:

```python
from celery import Celery

app = Celery('tareas',
             broker='redis://localhost:6399/0',
             backend='redis://localhost:6399/0')
```

La semana que viene esa URL va a cambiar por `redis://redis:6379/0`, cuando los workers también vivan en Compose y se encuentren por nombre de servicio.

---

## Las tres terminales

Celery se entiende mejor cuando se ve que son procesos independientes. Para trabajar hacen falta tres terminales, y conviene acostumbrarse a eso:

```bash
# Terminal 1: el broker
docker compose up -d

# Terminal 2: el worker (queda ocupada, mostrando logs)
source venv/bin/activate
celery -A tareas worker --loglevel=info --concurrency=2

# Terminal 3: tu programa
source venv/bin/activate
python3 encolar.py
python3 consultar.py <id>
```

El `source venv/bin/activate` va en **cada** terminal: el entorno virtual se activa por terminal, no por máquina. Olvidarlo es la causa del `ModuleNotFoundError: No module named 'celery'` que vas a ver al menos una vez.

Si en la terminal 3 no pasa nada y la tarea queda en `PENDING` para siempre, el orden de revisión es: ¿está el broker arriba?, ¿está el worker conectado al *mismo* broker?, ¿aparece la tarea en la lista `[tasks]` del worker?

---

## Dónde encaja esto en el curso

Celery no es una técnica nueva de concurrencia: es **las que ya vimos, puestas del otro lado de una red**.

| Pieza de Celery | Lo que ya sabés | Clase |
|---|---|---|
| El worker con `--concurrency` | pool de procesos prefork | 14, 22 |
| La cola del broker | `queue.Queue` / `asyncio.Queue` | 10, 21 |
| `AsyncResult` | `Future` | 22 |
| Los mensajes serializados | pickle / framing | 13, 22 |
| El broker como servicio | contenedores | 1, 2 |
| `get()` que relanza la excepción | `result()` que relanza | 22 |

Si hoy te pareció razonable, es porque ya tenías todas las piezas. Lo único realmente nuevo es que **el estado vive afuera del proceso**, y eso es lo que compra las tres propiedades del principio: persistencia, escalado horizontal, y desacople entre quien pide y quien ejecuta.

La contracara, que conviene decir ahora: Celery agrega un servidor más para mantener, latencia de red en cada tarea, y una fuente nueva de fallas.

Ese costo se puede medir. Cuánto tarda solo el acto de encolar —sin esperar el resultado— comparado con el `submit()` de la clase 22:

| | Mediana |
|---|---|
| `sumar.delay(2, 3)` | 2.21 ms |
| `pool.submit(...)` | 0.012 ms |

Unas **190 veces más caro**, y esa plata se paga en cada tarea. (La primera llamada tarda todavía más, unos 186 ms, porque abre la conexión al broker.)

La lectura es la misma de la clase 22 con el `chunksize`: si la tarea es más corta que su propio transporte, el transporte manda. Para cuatro imágenes en una app de escritorio, un `ProcessPoolExecutor` es la respuesta correcta y Celery es una complicación. La pregunta que lo justifica es: *¿necesito que el trabajo sobreviva al proceso, o que los workers estén en otra máquina?* Si las dos respuestas son no, no hace falta.

---

## Conceptos clave

1. **Broker**: el servidor que guarda la cola. Redis o RabbitMQ.
2. **Worker**: proceso aparte que ejecuta tareas; se lanza por CLI y usa prefork.
3. **Result backend**: donde se guardan los resultados. Opcional.
4. **`@app.task`**: decorador que registra una función como tarea ejecutable.
5. **`delay()`**: encola y devuelve enseguida.
6. **`AsyncResult`**: vista sobre el estado de una tarea, recuperable por id.
7. **El id es el recibo**: lo único que hay que guardar para consultar después.
8. **`PENDING` significa "no sé nada"**, no "en cola".
9. **Viaja el nombre de la tarea más los argumentos**, no la función.
10. **Los argumentos deben ser serializables**: pasá IDs, no objetos.
11. **Worker y cliente comparten el código** de las tareas.
12. **`concurrency`**: cuántas tareas a la vez por worker.
13. **Escalado horizontal**: más workers, incluso en otras máquinas, sin tocar el código.
14. **Las excepciones se guardan** con su traceback, no se pierden en silencio.
15. **El costo**: un servicio más, latencia, y más cosas que pueden fallar.

---

## Preparación para la próxima clase

La **clase 24 (Celery II)** es la última del cuatrimestre y tiene dos partes.

Primero, **orquestar todo con Docker Compose**: API, broker y varios workers levantados con un comando, encontrándose por nombre de servicio, y escalados con `--scale worker=3`. Es el cierre del arco que abrimos en la clase 1.

Segundo, lo que hace falta para que esto funcione cuando algo sale mal: **composición de tareas** (encadenar, agrupar, combinar resultados), **reintentos**, **idempotencia**, y cómo mirar lo que está pasando con **Flower**.

Para llegar preparado:

- Hacé que la demostración de las tres terminales te funcione. Si eso no corre, la clase que viene no se sigue.
- Probá levantar dos workers a la vez y mirá cómo se reparten las tareas.
- Repasá la clase 2 (Compose) y la 21 (la cola con workers): la 24 es las dos cosas juntas.
- **El TP2 se entrega el 03/11**, al inicio de la clase 24.

---

## Referencias

- [Celery: First Steps](https://docs.celeryq.dev/en/stable/getting-started/first-steps-with-celery.html) — el tutorial oficial, corto.
- [Celery: Next Steps](https://docs.celeryq.dev/en/stable/getting-started/next-steps.html) — el que sigue, con la estructura de proyecto.
- [Tasks](https://docs.celeryq.dev/en/stable/userguide/tasks.html) — la referencia de tareas y estados.
- [Choosing a Broker](https://docs.celeryq.dev/en/stable/getting-started/backends-and-brokers/) — Redis contra RabbitMQ, con las garantías de cada uno.

---

*Computación II - 2026 - Clase 23*
