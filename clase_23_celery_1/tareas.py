"""
Clase 23: las tareas que ejecutan los workers.

Este archivo lo comparten quien encola y quien ejecuta. El worker necesita
tenerlo para poder registrar las tareas; por la cola solo viaja el nombre.

Para levantar un worker con estas tareas:

    celery -A tareas worker --loglevel=info --concurrency=2

El broker tiene que estar arriba antes (docker compose up -d).
"""
import time

from celery import Celery

# El primer argumento es el nombre del modulo: Celery lo usa para armar
# los nombres de las tareas ('tareas.sumar', 'tareas.lenta', ...).
#
# broker:  donde se guarda la COLA (el trabajo que va hacia el worker)
# backend: donde se guardan los RESULTADOS (lo que vuelve del worker)
#
# El puerto 6399 es el que mapeamos en docker-compose.yml, para no chocar
# con cualquier Redis que ya tengas corriendo en el 6379.
app = Celery(
    'tareas',
    broker='redis://localhost:6399/0',
    backend='redis://localhost:6399/0',
)


@app.task
def sumar(a, b):
    """Una tarea trivial, con un sleep para que se vea que tarda."""
    time.sleep(1)
    return a + b


@app.task
def lenta(segundos):
    """Para medir concurrencia: varias de estas a la vez."""
    time.sleep(segundos)
    return f"dormi {segundos}s"


@app.task
def dividir(a, b):
    """Para ver que pasa cuando una tarea falla. Probala con b=0."""
    return a / b


@app.task
def saludar(nombre):
    """Sin resultado interesante: el caso en que el backend no haria falta."""
    print(f"hola {nombre}")
    return None
