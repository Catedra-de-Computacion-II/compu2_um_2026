"""
Clase 24: las tareas, ahora con reintentos e idempotencia.

Diferencia con la clase 23: la URL del broker sale de una variable de
entorno. Adentro de Compose los servicios se encuentran por nombre
('redis'), no por localhost.
"""
import hashlib
import os
import random
import time

from celery import Celery

# En Compose, 'redis' es el nombre del servicio: Docker lo resuelve por DNS
# en la red interna. El default sirve para correr fuera de Compose.
BROKER = os.environ.get('BROKER_URL', 'redis://localhost:6399/0')

app = Celery('tareas', broker=BROKER, backend=BROKER)

# Que el worker reporte STARTED, no solo PENDING -> SUCCESS.
app.conf.task_track_started = True

# Si el worker muere a mitad de una tarea, que no se pierda (ver clase 23,
# extra: acks_late). El precio es que se puede ejecutar dos veces, y por eso
# las tareas de abajo son idempotentes.
app.conf.task_acks_late = True


# ---------------------------------------------------------------------------
# Tareas simples
# ---------------------------------------------------------------------------

@app.task
def hashear(texto):
    """CPU-bound de juguete: hashea muchas veces."""
    h = texto.encode()
    for _ in range(200_000):
        h = hashlib.sha256(h).digest()
    return h.hex()[:16]


@app.task
def esperar(segundos):
    """I/O-bound simulado."""
    time.sleep(segundos)
    return f"espere {segundos}s"


# ---------------------------------------------------------------------------
# Reintentos: la tarea que falla a veces
# ---------------------------------------------------------------------------

@app.task(
    bind=True,                      # self: para poder llamar a self.retry()
    max_retries=3,
    default_retry_delay=2,          # segundos entre intentos
)
def inestable(self, exito_cada):
    """
    Falla aleatoriamente y se reintenta sola.

    bind=True hace que el primer parametro sea 'self', la instancia de la
    tarea. De ahi salen self.request.retries (cuantas veces se reintento)
    y self.retry() (volver a encolarla).
    """
    intento = self.request.retries + 1

    if random.randint(1, exito_cada) != 1:
        print(f"  intento {intento}: fallo")
        # countdown sobreescribe el default_retry_delay.
        # Backoff exponencial: 2s, 4s, 8s...
        raise self.retry(countdown=2 ** self.request.retries)

    print(f"  intento {intento}: exito")
    return f"salio en el intento {intento}"


@app.task(
    bind=True,
    autoretry_for=(ConnectionError,),   # reintenta solo para estas
    retry_backoff=True,                 # backoff exponencial automatico
    retry_kwargs={'max_retries': 3},
)
def descargar(self, url):
    """
    La forma declarativa: autoretry_for en lugar de try/except.

    Mas corto que el anterior y cubre el caso habitual: reintentar los
    errores transitorios (la red) y no los permanentes (un 404).
    """
    if 'roto' in url:
        raise ConnectionError(f"no pude conectar a {url}")
    return f"baje {url}"


# ---------------------------------------------------------------------------
# Idempotencia: la tarea que se puede ejecutar dos veces sin dano
# ---------------------------------------------------------------------------

# Simulamos una base de datos con un dict en memoria del worker.
# En la realidad esto seria Redis o Postgres.
_procesados = {}


@app.task
def cobrar_mal(pedido_id, monto):
    """NO idempotente: ejecutarla dos veces cobra dos veces."""
    actual = _procesados.get('total', 0)
    _procesados['total'] = actual + monto
    return _procesados['total']


@app.task
def cobrar_bien(pedido_id, monto):
    """
    Idempotente: ejecutarla dos veces cobra una sola vez.

    La clave es la marca por pedido_id. Con acks_late=True una tarea se
    puede reejecutar, asi que esta defensa no es opcional.
    """
    if pedido_id in _procesados:
        return f"pedido {pedido_id} ya estaba cobrado (no hice nada)"

    _procesados[pedido_id] = monto
    return f"cobre {monto} del pedido {pedido_id}"


# ---------------------------------------------------------------------------
# Para componer (Canvas)
# ---------------------------------------------------------------------------

@app.task
def sumar(a, b):
    return a + b


@app.task
def duplicar(n):
    """Pensada para encadenar: recibe el resultado de la anterior."""
    return n * 2


@app.task
def total(numeros):
    """Para el chord: recibe la LISTA de resultados del grupo."""
    return sum(numeros)
