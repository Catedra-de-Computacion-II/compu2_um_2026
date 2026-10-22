"""
Clase 24: la API que encola y no hace esperar a nadie.

El patron completo: POST acepta el trabajo y devuelve 202 con un id;
GET consulta el estado con ese id. El cliente puede cerrar la pestana
y volver manana.

Para correr fuera de Compose:
    uvicorn api:api --reload --port 8000

Ojo con 'api:api': el primero es el modulo (api.py), el segundo es el
objeto FastAPI. Aca 'app' ya esta usado por el objeto de Celery.

Adentro de Compose lo levanta el servicio 'api' (ver docker-compose.yml).
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from celery.result import AsyncResult

from tareas import app as celery_app
from tareas import hashear, esperar, descargar

api = FastAPI(title="Plataforma de tareas - Clase 24")


class Trabajo(BaseModel):
    tipo: str          # hashear | esperar | descargar
    dato: str


@api.post("/trabajos", status_code=202)
def crear(trabajo: Trabajo):
    """
    202 Accepted: 'lo recibi, todavia no lo hice'.

    Es el codigo correcto cuando el trabajo es asincronico. Un 200 seria
    mentira (no esta hecho) y un 201 tambien (no hay recurso creado aun).
    """
    tareas = {
        'hashear': hashear,
        'esperar': esperar,
        'descargar': descargar,
    }

    if trabajo.tipo not in tareas:
        raise HTTPException(400, f"tipo invalido: {trabajo.tipo}")

    # 'esperar' recibe un numero; las otras, un string.
    dato = int(trabajo.dato) if trabajo.tipo == 'esperar' else trabajo.dato

    resultado = tareas[trabajo.tipo].delay(dato)

    return {
        "id": resultado.id,
        "estado": resultado.state,
        "consultar_en": f"/trabajos/{resultado.id}",
    }


@api.get("/trabajos/{tarea_id}")
def consultar(tarea_id: str):
    """
    El estado de un trabajo, por su id.

    Ojo: PENDING puede significar 'en cola' o 'este id no existe'. El
    backend no los distingue (clase 23).
    """
    r = AsyncResult(tarea_id, app=celery_app)

    respuesta = {
        "id": tarea_id,
        "estado": r.state,
        "listo": r.ready(),
    }

    if r.state == 'SUCCESS':
        respuesta["resultado"] = r.result
    elif r.state == 'FAILURE':
        respuesta["error"] = str(r.result)
        respuesta["tipo_error"] = type(r.result).__name__
    elif r.state == 'RETRY':
        respuesta["nota"] = "fallo y se esta reintentando"

    return respuesta


@api.get("/salud")
def salud():
    """Para el healthcheck de Compose y para ver si el broker responde."""
    try:
        # inspect() pregunta a los workers que estan vivos
        workers = celery_app.control.inspect().ping() or {}
        return {"api": "ok", "workers": list(workers.keys())}
    except Exception as e:
        return {"api": "ok", "broker": f"error: {e}"}
