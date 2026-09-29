# Clase 19: HTTP + FastAPI - Extra Manijas

Material opcional para profundizar.

---

## WSGI y ASGI: por qué hicieron falta dos

Antes de ASGI existía **WSGI** (PEP 333, 2003), el estándar que permitió que Flask, Django y Bottle corrieran sobre cualquier servidor —gunicorn, mod_wsgi, waitress— sin adaptarse a cada uno.

Una aplicación WSGI es una función:

```python
def app(environ, start_response):
    start_response('200 OK', [('Content-Type', 'text/plain')])
    return [b'hola']
```

Simple y efectivo, pero con un límite estructural: **es sincrónica**. La firma no tiene forma de suspenderse, así que cada pedido ocupa un thread de principio a fin. Es el modelo de la clase 14, con todos sus techos.

ASGI (2018) rehace el contrato en términos asíncronos:

```python
async def app(scope, receive, send):
    await send({'type': 'http.response.start', 'status': 200,
                'headers': [(b'content-type', b'text/plain')]})
    await send({'type': 'http.response.body', 'body': b'hola'})
```

Tres diferencias que importan:

**Es una corrutina**, así que puede suspenderse y el servidor atiende a otros mientras.

**`receive` y `send` son callables asíncronos**, no un valor de retorno. Eso permite respuestas en partes (streaming) y protocolos donde los mensajes van y vienen.

**El `scope` incluye el tipo de conexión**: `http`, `websocket` o `lifespan`. Por eso WebSockets funcionan en ASGI y no en WSGI: no hay forma de expresar una conexión de larga duración con mensajes bidireccionales en la firma de WSGI.

FastAPI es una aplicación ASGI. En rigor, es una capa sobre **Starlette**, que es quien implementa el protocolo ASGI; FastAPI agrega la validación con Pydantic y la generación de OpenAPI.

---

## Lifespan: código al arrancar y al cerrar

Para el TP2 van a necesitar crear cosas al arrancar —la cola, el pool de workers— y limpiarlas al cerrar. ASGI define un evento `lifespan` para eso, y FastAPI lo expone con un context manager:

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
import asyncio

@asynccontextmanager
async def ciclo_de_vida(app: FastAPI):
    # --- antes de atender el primer pedido ---
    app.state.cola = asyncio.Queue()
    app.state.workers = [
        asyncio.create_task(worker(app.state.cola)) for _ in range(3)
    ]
    yield                                  # acá el servidor atiende
    # --- al cerrar ---
    for w in app.state.workers:
        w.cancel()
    await asyncio.gather(*app.state.workers, return_exceptions=True)

app = FastAPI(lifespan=ciclo_de_vida)
```

El `yield` del medio es el tiempo de vida del servidor: lo de arriba corre una vez al arrancar, lo de abajo al recibir SIGTERM o Ctrl+C.

`app.state` es el lugar previsto para el estado compartido, accesible desde los endpoints con `request.app.state`. Es el equivalente de `self.server` en `socketserver` (clase 16): el estado va en el objeto que sobrevive, no en el que se crea por pedido.

Y la cancelación de los workers es exactamente el mecanismo de la clase 18: `cancel()` inyecta `CancelledError` en el punto de suspensión.

---

## Inyección de dependencias

FastAPI tiene un mecanismo que parece magia y es bastante simple: declarás qué necesita un endpoint y el framework se lo provee.

```python
from fastapi import Depends

async def obtener_cola(request: Request):
    return request.app.state.cola

@app.post('/tareas')
async def crear(nueva: TareaNueva, cola = Depends(obtener_cola)):
    await cola.put(nueva)
    return {'encolada': True}
```

`Depends` le dice a FastAPI: "antes de llamar a `crear`, ejecutá `obtener_cola` y pasame el resultado". Las dependencias pueden anidarse, cachearse por pedido, y usarse para autenticación, conexiones a base de datos o validaciones comunes.

La ventaja real es para probar: en los tests se puede reemplazar una dependencia por otra sin tocar el endpoint.

```python
app.dependency_overrides[obtener_cola] = lambda: cola_falsa
```

---

## Probar una API sin levantar el servidor

FastAPI permite probar endpoints sin abrir un puerto:

```python
from fastapi.testclient import TestClient

cliente = TestClient(app)

def test_crear_tarea():
    r = cliente.post('/tareas', json={'tipo': 'esperar', 'prioridad': 2})
    assert r.status_code == 201
    assert r.json()['estado'] == 'pendiente'

def test_no_existe():
    assert cliente.get('/tareas/999').status_code == 404
```

`TestClient` habla ASGI directamente con la aplicación, sin sockets ni red. Es rápido y no depende de puertos libres.

> Según la versión de Starlette, puede aparecer un aviso de deprecación sobre `httpx`. Es informativo y no rompe nada; indica que en el futuro `TestClient` va a usar otra biblioteca por debajo.

Para endpoints `async` con dependencias asíncronas conviene `httpx.AsyncClient` con `ASGITransport`:

```python
import httpx, pytest

@pytest.mark.asyncio
async def test_async():
    transporte = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transporte,
                                 base_url='http://test') as c:
        r = await c.get('/tareas')
        assert r.status_code == 200
```

El TP2 ofrece puntos extra por tests: esto es por dónde empezar.

---

## Sacar el trabajo pesado del loop

La clase mostró que un `def` común va al threadpool. Para control explícito hay dos herramientas:

```python
import asyncio
from concurrent.futures import ProcessPoolExecutor

# Para I/O bloqueante: un thread
@app.get('/archivo')
async def leer_archivo():
    contenido = await asyncio.to_thread(open('grande.txt').read)
    return {'bytes': len(contenido)}

# Para CPU: un proceso, porque el GIL (clase 10)
pool = ProcessPoolExecutor(max_workers=2)

@app.post('/hashear')
async def hashear(datos: str):
    loop = asyncio.get_running_loop()
    resultado = await loop.run_in_executor(pool, calculo_pesado, datos)
    return {'hash': resultado}
```

`asyncio.to_thread()` es lo que usa FastAPI por dentro con los endpoints `def`. Para CPU-bound no alcanza —el GIL no deja que dos threads calculen en paralelo— y hace falta un `ProcessPoolExecutor`.

Es la misma tabla de decisión de la clase 10, ahora dentro de un servidor. El TP2 lo pide explícitamente: la tarea `hashear` tiene que salir del event loop.

---

## HTTP/2 y HTTP/3, en breve

Lo que vimos es HTTP/1.1, que sigue siendo mayoría en APIs internas. Pero hay dos versiones más nuevas que conviene ubicar.

**HTTP/2 (2015)** mantiene la misma semántica —métodos, códigos, headers— pero cambia el transporte: pasa a ser **binario** en vez de texto, permite **multiplexar** varios pedidos en una conexión TCP, y comprime los headers.

El multiplexado resuelve el *head-of-line blocking* de nivel HTTP: en 1.1, con keep-alive, las respuestas tienen que volver en orden, así que una lenta demora a las que siguen. En 2, van intercaladas.

Pero queda un head-of-line blocking más abajo: si se pierde un paquete TCP, **todos** los streams multiplexados esperan la retransmisión, porque TCP entrega en orden.

**HTTP/3 (2022)** resuelve eso cambiando de transporte: corre sobre **QUIC**, que va sobre UDP. Cada stream se retransmite por separado, así que perder un paquete no frena a los demás.

Ahí cierra un círculo de la clase 15: dijimos que implementar confiabilidad sobre UDP era reinventar TCP peor, con la excepción de QUIC. Esta es la excepción — y el motivo es justamente evitar una garantía de TCP (el orden global) que en este caso estorba.

---

## Lecturas

- [RFC 9110](https://www.rfc-editor.org/rfc/rfc9110) - semántica de HTTP, la especificación actual
- [ASGI](https://asgi.readthedocs.io/) - el estándar, corto y legible
- [PEP 3333](https://peps.python.org/pep-3333/) - WSGI, el antecesor sincrónico
- [FastAPI: Bigger Applications](https://fastapi.tiangolo.com/tutorial/bigger-applications/) - cómo organizar una API que crece
- [Starlette](https://www.starlette.io/) - lo que hay abajo de FastAPI
- [HTTP/3 explained](https://http3-explained.haxx.se/) - Daniel Stenberg, el autor de curl

---

*Computación II - 2026 - Clase 19*
