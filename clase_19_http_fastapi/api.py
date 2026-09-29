#!/usr/bin/env python3
"""Una API con FastAPI: validación, errores y documentación automática.

Es el esqueleto de lo que pide el TP2, con los datos en memoria y sin
concurrencia todavía.

Uso:
    pip install fastapi uvicorn
    python3 api.py

Después:
    http://localhost:8000/docs        <- la documentación se genera sola
    curl localhost:8000/tareas
    curl -X POST localhost:8000/tareas -H 'Content-Type: application/json' \
         -d '{"tipo":"descargar","prioridad":3}'
"""
import asyncio
import os
import threading
from typing import Literal

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

app = FastAPI(
    title='Tareas',
    description='Ejemplo de la clase 19: HTTP + FastAPI',
)

# Estado en memoria. OJO: con --workers > 1 cada proceso tiene el suyo.
tareas: dict[int, dict] = {}
proximo_id = 0


# ---------------------------------------------------------------
# Modelos: Pydantic valida por nosotros
# ---------------------------------------------------------------

class TareaNueva(BaseModel):
    """Lo que el cliente manda en el cuerpo de un POST."""
    tipo: Literal['descargar', 'hashear', 'esperar']
    prioridad: int = Field(default=1, ge=1, le=5,
                           description='1 = más baja, 5 = más alta')


class Tarea(TareaNueva):
    """Lo que devolvemos: lo anterior más lo que agrega el servidor."""
    id: int
    estado: Literal['pendiente', 'ejecutando', 'completada'] = 'pendiente'


# ---------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------

@app.get('/')
async def raiz():
    """FastAPI convierte el dict a JSON y pone los headers por su cuenta."""
    return {'servicio': 'tareas', 'docs': '/docs'}


@app.get('/tareas', response_model=list[Tarea])
async def listar(
    estado: str | None = Query(default=None, description='Filtrar por estado'),
    limite: int = Query(default=10, ge=1, le=100),
):
    """Los parámetros que no están en la ruta se leen de la query string.
    Los tipos NO son decorativos: FastAPI valida y convierte."""
    items = list(tareas.values())
    if estado:
        items = [t for t in items if t['estado'] == estado]
    return items[:limite]


@app.post('/tareas', response_model=Tarea, status_code=201)
async def crear(nueva: TareaNueva):
    """201 Created es la respuesta correcta a un POST que crea algo."""
    global proximo_id
    proximo_id += 1
    tarea = {'id': proximo_id, **nueva.model_dump(), 'estado': 'pendiente'}
    tareas[proximo_id] = tarea
    return tarea


@app.get('/tareas/{tarea_id}', response_model=Tarea)
async def obtener(tarea_id: int):
    """El : int hace que /tareas/abc devuelva 422 sin ejecutar la función."""
    if tarea_id not in tareas:
        raise HTTPException(status_code=404, detail='No existe esa tarea')
    return tareas[tarea_id]


@app.delete('/tareas/{tarea_id}', status_code=204)
async def borrar(tarea_id: int):
    """204 No Content: salió bien y no hay nada que devolver."""
    if tarea_id not in tareas:
        raise HTTPException(status_code=404, detail='No existe esa tarea')
    del tareas[tarea_id]


@app.get('/quien-soy')
async def quien_soy():
    """Dónde corre realmente un endpoint async."""
    loop = asyncio.get_running_loop()
    return {
        'pid': os.getpid(),
        'thread': threading.current_thread().name,
        'loop': type(loop).__name__,
        'id_del_loop': id(loop),        # igual en todos los pedidos
    }


@app.get('/quien-soy-sync')
def quien_soy_sync():
    """Un def común NO corre en el event loop: va a un threadpool."""
    try:
        asyncio.get_running_loop()
        estado = 'HAY loop'
    except RuntimeError:
        estado = 'NO hay loop corriendo acá'
    return {'thread': threading.current_thread().name, 'loop': estado}


if __name__ == '__main__':
    import uvicorn
    # uvicorn es el que crea y corre el event loop; FastAPI solo responde.
    uvicorn.run(app, host='127.0.0.1', port=8000)
