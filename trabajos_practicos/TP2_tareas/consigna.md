# Trabajo Práctico Nº 2: Plataforma de Tareas Distribuidas

**Computación II — Universidad de Mendoza — 2026**

---

## Información general

| | |
|-|-|
| **Enunciado** | Clase 21 (13/10/2026) |
| **Entrega** | Clase 24 (03/11/2026), al final de la clase |
| **Modalidad** | Individual |
| **Plataforma** | Cualquiera: corre en Docker (Linux, macOS o Windows). Ver 4.1 |
| **Lenguaje** | Python 3.11+ |
| **Entrega** | Repositorio público en GitHub |

---

## Objetivos pedagógicos

Al terminar este TP deberías poder:

1. **Escribir un servidor asíncrono** que atienda muchos clientes concurrentes en
   un solo hilo, sin bloquear el event loop.
2. **Diseñar una API HTTP** y exponerla con FastAPI.
3. **Distribuir trabajo** entre workers, eligiendo la herramienta correcta según
   el tipo de tarea.
4. **Distinguir I/O-bound de CPU-bound** en la práctica, y saber por qué asyncio
   resuelve el primero y no el segundo.
5. **Medir** en vez de suponer: comparar concurrencia real contra secuencial.
6. **Conectar la teoría del cuatrimestre** (sockets, multiplexing, event loop,
   corrutinas) con un sistema que funciona.

---

## Descripción del sistema a construir

Una **plataforma de tareas distribuidas**: un servicio al que se le encargan
trabajos por HTTP, que los ejecuta de forma concurrente y permite consultar su
estado y resultado.

```
   Cliente HTTP
        |
        v
  ┌──────────────────┐        ┌──────────────────┐
  │   API (FastAPI)  │───────>│  Cola de tareas  │
  │  POST /tareas    │        │  (asyncio.Queue) │
  │  GET  /tareas    │        └────────┬─────────┘
  │  GET  /tareas/id │                 │
  │  DEL  /tareas/id │                 v
  └──────────────────┘        ┌──────────────────┐
        ^                     │  Pool de workers │
        │                     │  N corrutinas    │
        └─────────────────────┤  + executor para │
           estado/resultado   │    CPU-bound     │
                              └──────────────────┘
```

### Tipos de tarea obligatorios

El sistema debe soportar al menos estos tres, porque cada uno ejercita algo
distinto:

| Tarea | Naturaleza | Qué ejercita |
|-------|-----------|--------------|
| `descargar` | I/O-bound | Concurrencia asíncrona real |
| `hashear` | CPU-bound | Que asyncio NO sirve para esto |
| `esperar` | I/O simulado | Cancelación y timeouts |

**`descargar`**: recibe una lista de URLs, las descarga concurrentemente y
devuelve por cada una el código de estado, el tamaño y el tiempo que tardó.

**`hashear`**: recibe un texto y una cantidad de iteraciones, y calcula un hash
iterado (por ejemplo, aplicar SHA-256 N veces). Con N suficientemente grande,
bloquea. Ese es el punto.

**`esperar`**: duerme N segundos. Sirve para probar cancelación, timeouts y ver
el estado en vivo.

---

## Requisitos funcionales

### 1. API HTTP (FastAPI)

| Método | Ruta | Qué hace |
|--------|------|----------|
| `POST` | `/tareas` | Encola una tarea. Devuelve su `id` y estado inicial |
| `GET` | `/tareas` | Lista las tareas, con filtro opcional por estado |
| `GET` | `/tareas/{id}` | Estado y resultado de una tarea |
| `DELETE` | `/tareas/{id}` | Cancela una tarea encolada o en ejecución |
| `GET` | `/estadisticas` | Totales por estado, tiempos promedio, workers ocupados |

Los estados posibles son: `pendiente`, `ejecutando`, `completada`, `fallida`,
`cancelada`.

El `POST` debe responder **inmediatamente**, sin esperar a que la tarea termine.
Si tu endpoint tarda lo mismo que la tarea, el diseño está mal.

### 2. Ejecución concurrente

- Un **pool de workers** con cantidad configurable, implementado con corrutinas
  y `asyncio.Queue`.
- Las tareas I/O-bound se ejecutan **concurrentemente**: N descargas simultáneas
  deben tardar aproximadamente lo que la más lenta, no la suma.
- Las tareas CPU-bound **no deben bloquear el event loop**. Tenés que resolverlo
  con `run_in_executor` (o `asyncio.to_thread`) y explicar por qué.

### 3. Cancelación y timeouts

- `DELETE /tareas/{id}` cancela una tarea en ejecución, no solo una encolada.
- Cada tarea tiene un timeout configurable; al vencer, pasa a `fallida` con el
  motivo.
- La cancelación tiene que ser **limpia**: sin corrutinas huérfanas ni recursos
  sin liberar.

### 4. Persistencia mínima

El estado vive en memoria, pero:

- `SIGTERM` y `SIGINT` deben provocar un apagado ordenado: dejar de aceptar
  tareas nuevas, esperar (con límite) a las que están en curso, y volcar el
  estado a `estado_<timestamp>.json`.
- Al arrancar, si existe un volcado previo, reportarlo por log.

### 4.1 Nota sobre plataformas

A diferencia del TP1 —que leía `/proc` y necesitaba una versión aparte para
macOS— este TP usa herramientas multiplataforma y **no requiere una consigna
distinta**. Además corre en Docker, o sea sobre Linux en cualquier sistema.

Si desarrollás fuera del contenedor, hay dos diferencias que conviene conocer:

**`ProcessPoolExecutor` arranca distinto según el sistema.** En Linux usa `fork`;
en macOS y Windows usa `spawn`, que **re-importa el módulo** en cada proceso
hijo. Por eso el arranque tiene que estar protegido:

```python
if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8000)
```

Sin esa guarda, en macOS el programa entra en un bucle de reimportación al crear
el pool. En Linux funciona igual, así que es un error que solo aparece en una de
las dos plataformas.

**`loop.add_signal_handler()` es solo para Unix.** Funciona en Linux y macOS,
pero no en Windows. Si trabajás en Windows sin Docker, usá `signal.signal()` con
un flag que el loop consulte, o directamente desarrollá dentro del contenedor.

### 5. Docker

- `Dockerfile` y `docker-compose.yml`
- Todo levanta con `docker compose up --build`
- La API queda accesible desde el host

---

## Mediciones obligatorias

El README debe incluir **números tuyos**, no estimaciones:

1. **Concurrencia I/O**: tiempo de 20 descargas secuenciales contra 20
   concurrentes. Reportá ambos y el speedup.
2. **El event loop bloqueado**: corré una tarea CPU-bound pesada *sin*
   `run_in_executor` y medí cuánto tarda en responder un `GET /tareas` durante
   ese lapso. Después repetí *con* executor. La diferencia es el punto de la
   materia.
3. **Techo del pool**: subí la cantidad de tareas concurrentes hasta que los
   tiempos se degraden. ¿Dónde está el límite y por qué?

---

## Entregables

### 1. Repositorio público en GitHub

Clonable y ejecutable con `docker compose up --build`, sin pasos extra.

### 2. README.md con el informe

Es central a la evaluación. Debe incluir:

1. **Descripción y uso**: qué hace y cómo se prueba (incluí ejemplos de `curl`)
2. **Diagrama de arquitectura**: componentes y flujo de una tarea
3. **Decisiones de diseño** argumentadas:
   - ¿Por qué `asyncio.Queue` y no `queue.Queue`?
   - ¿Cómo evitás que una tarea CPU-bound congele la API?
   - ¿Cómo implementaste la cancelación, y qué pasa con los recursos a medio usar?
   - ¿Qué pasa si un worker lanza una excepción no capturada?
4. **Las tres mediciones**, con los números y su interpretación
5. **Conceptos del curso aplicados**: relacionar partes del código con clases
   específicas. Por ejemplo:
   > "El pool de workers consume de una `asyncio.Queue` compartida. Es el mismo
   > patrón productor-consumidor de la clase 11, pero con corrutinas en vez de
   > threads: acá no hace falta lock porque el event loop no interrumpe entre
   > `await`s."
6. **Limitaciones conocidas**: qué no hace bien tu sistema
7. **Lo que aprendiste**: 2-3 párrafos personales

### 3. dudas.md (opcional pero bienvenido)

---

## Criterios de evaluación

| Ítem | Peso |
|------|------|
| **Funcionalidad**: la API responde, las tareas se ejecutan, los estados son correctos | 25% |
| **Asincronismo**: concurrencia real, event loop nunca bloqueado, cancelación limpia | 30% |
| **Mediciones**: las tres, con números propios e interpretación | 15% |
| **README**: justifica decisiones y conecta con la teoría | 20% |
| **Código limpio**: estructura clara, manejo de errores, PEP 8 razonable | 10% |
| **Bonus**: extensiones opcionales | +10% |

### Lo que vamos a preguntar al corregir

- "Mostrame dónde tu código podría bloquear el event loop."
- "¿Qué pasa si cancelo una tarea justo cuando está a mitad de una descarga?"
- "¿Por qué tu pool de workers no necesita un `Lock`?"
- "Si te mando 10.000 tareas de golpe, ¿qué se rompe primero?"
- "¿Qué diferencia hay entre `asyncio.gather` y un `for` con `await` adentro?"
- "¿Por qué `time.sleep()` en una corrutina es un bug y `asyncio.sleep()` no?"

**Si no podés explicar tu propio código, no aprueba** — aunque funcione perfecto.

---

## Restricciones

- **Sin frameworks de colas** (Celery, RQ, Dramatiq): la cola la implementás vos
  con `asyncio`. Celery es bonus, y solo *además* de lo obligatorio.
- **Sin base de datos**: el estado va en memoria más el volcado a JSON.
- **Nada de `time.sleep()`** dentro de una corrutina.
- **Sin `requests`** para las descargas: usá algo asíncrono (`aiohttp`, `httpx`
  en modo async) y justificá la elección.

---

## Extensiones opcionales (bonus)

Siempre después de que lo obligatorio esté sólido. Hasta +2% cada una, +10% total:

1. **WebSocket** `/eventos`: notificar cambios de estado en tiempo real
2. **Prioridades**: cola con prioridad, y explicar cómo evitás inanición
3. **Reintentos**: con backoff exponencial para tareas fallidas
4. **Rate limiting**: limitar tareas por cliente
5. **Métricas**: endpoint en formato Prometheus
6. **Tests**: con `pytest-asyncio`, especialmente de cancelación
7. **Celery**: reimplementar el pool con Celery y comparar con tu versión
8. **Tarea propia**: un cuarto tipo de tarea que te parezca interesante

---

## Cronograma sugerido

| Semana | Hasta | Tarea |
|--------|-------|-------|
| 1 | 20/10 | Diseño y esqueleto: la API con endpoints que devuelvan datos falsos, la cola y los workers consumiendo |
| 2 | 27/10 | Las tres tareas andando de verdad, con el executor para `hashear`. Cancelación, timeouts y apagado ordenado |
| 3 | 03/11 | Las tres mediciones, el README, y los bonus que lleguen a hacer |

> **Sobre el tiempo:** este TP se entrega más tarde de lo previsto y quedan tres
> semanas. La contrapartida es que **todo lo necesario ya se vio**: el event loop
> (clase 18), la API (19), I/O asíncrono de red (20), y colas, cancelación y
> executors (21). No hay que esperar a ninguna clase para avanzar, se puede
> encarar entero desde el primer día.
>
> Las clases que siguen agregan contexto —`concurrent.futures` en detalle y
> Celery— pero no hacen falta para lo obligatorio.

---

## Cómo trabajar con IA

Vale lo mismo que en el TP1: usala como tutor, no como escriba. Ver
`prompt_tutor_ia.md` en la carpeta del TP1.

No nos importa quién escriba el código. Nos importa que **vos entiendas qué hace
y por qué**.

---

## Material de referencia

### Del curso

- Clase 13-14: Sockets TCP y servidores concurrentes
- Clase 17: I/O Multiplexing (`select`, `epoll`) — la base del event loop
- Clase 18: De yield a asyncio — generadores, `send()`, corrutinas
- Clase 19: HTTP y FastAPI
- Clase 20-21: Asyncio en red y avanzado
- Clase 22: `concurrent.futures`
- Bloque 0: Python avanzado (generadores, context managers, decoradores)

### Externa

- [Documentación de asyncio](https://docs.python.org/3/library/asyncio.html)
- [FastAPI](https://fastapi.tiangolo.com/)
- [aiohttp](https://docs.aiohttp.org/) / [httpx](https://www.python-httpx.org/)
- [PEP 492](https://peps.python.org/pep-0492/) — de dónde salieron `async`/`await`

---

*Trabajo Práctico Nº 2 — Computación II — 2026*
