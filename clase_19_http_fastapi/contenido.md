# Clase 19: HTTP + FastAPI

## Introducción: subir de capa

Todo lo que hicimos hasta acá fue transporte. Sockets, bytes, framing, multiplexing, corrutinas: las cañerías. Sabemos mover datos entre dos procesos, pero nunca acordamos **qué significan** esos datos.

Eso es un protocolo de aplicación, y hoy vemos el que sostiene la web.

HTTP ya lo tocaron en la clase 12, aunque quizás no lo recuerden así: cuando escribieron a mano `GET / HTTP/1.1` con `nc` y un servidor real les contestó. Esa demostración —que HTTP es texto plano que se puede tipear— es el punto de partida de hoy.

La clase tiene dos mitades. En la primera **miramos el protocolo de cerca**: qué viaja, cómo se estructura, por qué está diseñado así. En la segunda **construimos una API** con FastAPI, que es lo que van a usar en el TP2. (*API*, por *Application Programming Interface*, es el conjunto de operaciones que un programa expone para que otros programas las usen. Una API HTTP es eso mismo publicado por la red: en vez de llamar a una función, hacés un pedido.)

En el medio hay una bisagra que conviene anticipar: vamos a ver `http.server`, el servidor HTTP de la biblioteca estándar, que resulta ser `socketserver` de la clase 16 con un handler que entiende HTTP. Nada nuevo bajo el sol — solo capas apiladas.

> **Nota:** los archivos `crudo.py`, `api.py` y `medir.py` acompañan la clase. Para la segunda mitad hace falta instalar FastAPI: hay instrucciones más abajo.

---

## HTTP es texto que podés escribir a mano

Empecemos por donde quedó la clase 12:

```bash
printf 'GET / HTTP/1.1\r\nHost: example.com\r\nConnection: close\r\n\r\n' | nc example.com 80
```

```
HTTP/1.1 200 OK
Date: Mon, 28 Sep 2026 23:50:33 GMT
Content-Type: text/html; charset=utf-8
Transfer-Encoding: chunked
Connection: close

<!doctype html>...
```

Eso es todo el protocolo. Un pedido de texto, una respuesta de texto, sobre una conexión TCP como las que venimos abriendo desde la clase 13.

Que sea legible no es casualidad: HTTP se diseñó en 1991 para que un humano pudiera depurarlo con las herramientas que había. Esa decisión lo hizo fácil de implementar y de extender, y es parte de por qué ganó.

### La estructura de un pedido

```
GET /tareas/42 HTTP/1.1          <- línea de pedido: método, ruta, versión
Host: ejemplo.com                <- headers: metadatos, uno por línea
Accept: application/json
Content-Length: 0
                                 <- línea VACÍA: acá terminan los headers
(cuerpo, si lo hay)
```

Y la respuesta tiene la misma forma:

```
HTTP/1.1 200 OK                  <- línea de estado: versión, código, texto
Content-Type: application/json   <- headers
Content-Length: 27

{"id": 42, "estado": "ok"}       <- cuerpo
```

Tres partes: **línea inicial, headers, cuerpo**, separados el segundo del tercero por una línea vacía.

Ahí aparece algo que ya resolvimos en la clase 13. HTTP corre sobre TCP, que es un flujo de bytes sin límites de mensaje. ¿Cómo sabe el receptor dónde termina un pedido? **Con framing**, y HTTP usa los dos métodos que vimos:

- Los headers terminan con una **línea vacía** — framing por delimitador.
- El cuerpo se mide con **`Content-Length`** — framing por longitud.

No es coincidencia: son las dos únicas formas de delimitar mensajes sobre un flujo, y ya las conocían.

### Los finales de línea importan

El separador de HTTP es `\r\n`, no `\n`. Por eso el `printf` de arriba los escribe explícitos.

Muchos servidores toleran `\n` solo, pero no hay que depender de eso: un servidor estricto rechaza el pedido y el error es desconcertante.

---

## Métodos: qué le pedís al servidor

El método es un verbo que dice qué querés hacer con el recurso:

| Método | Qué significa | ¿Tiene cuerpo? |
|--------|---------------|----------------|
| `GET` | Traeme esto | No |
| `POST` | Creá algo con estos datos | Sí |
| `PUT` | Reemplazá esto completo | Sí |
| `PATCH` | Modificá esta parte | Sí |
| `DELETE` | Borrá esto | No |
| `HEAD` | Como GET pero solo los headers | No |
| `OPTIONS` | ¿Qué puedo hacer acá? | No |

Dos propiedades que la especificación define y que conviene entender, porque explican decisiones de diseño reales:

**Seguro** (*safe*): no modifica nada en el servidor. `GET` y `HEAD` lo son. Por eso un buscador puede recorrer links sin miedo, y por eso **nunca** hay que poner una acción destructiva detrás de un `GET`.

**Idempotente**: repetirlo da el mismo resultado que hacerlo una vez. `GET`, `PUT` y `DELETE` lo son; `POST` no. Por eso el navegador te pregunta "¿reenviar formulario?" al recargar: no puede saber si duplicaría la operación.

Esa distinción importa cuando hay reintentos. Si una petición falla por timeout, reintentar un `PUT` es seguro; reintentar un `POST` puede crear dos registros. Es el mismo problema que vimos en la clase 15 con UDP y la deduplicación de mensajes.

---

## Códigos de estado

El número de tres dígitos de la respuesta. La primera cifra dice la familia:

| Familia | Significa | Ejemplos |
|---------|-----------|----------|
| `1xx` | Información | 100 Continue |
| `2xx` | Salió bien | 200 OK, 201 Created, 204 No Content |
| `3xx` | Buscá en otro lado | 301 Moved Permanently, 304 Not Modified |
| `4xx` | Error **del cliente** | 400 Bad Request, 404 Not Found, 422 Unprocessable |
| `5xx` | Error **del servidor** | 500 Internal Server Error, 503 Service Unavailable |

La división entre `4xx` y `5xx` es la más útil en la práctica: dice **de quién es la culpa**. Si tu API devuelve 500 cuando el cliente mandó datos mal, estás mintiendo en el diagnóstico y complicando a quien la usa.

Los que más van a usar en el TP2:

- **200** — todo bien, acá está el resultado
- **201** — creado (respuesta correcta a un `POST` que crea algo)
- **204** — salió bien y no hay nada que devolver
- **404** — no existe ese recurso
- **422** — el pedido está bien formado pero los datos no son válidos
- **500** — se rompió algo del lado del servidor

---

## Headers: los metadatos

Los headers son pares `Nombre: valor` que acompañan al pedido o la respuesta. Hay decenas; estos son los que importan ahora:

| Header | Para qué |
|--------|----------|
| `Host` | A qué sitio le hablás (obligatorio en HTTP/1.1) |
| `Content-Type` | Qué formato tiene el cuerpo: `application/json`, `text/html` |
| `Content-Length` | Cuántos bytes tiene el cuerpo |
| `Accept` | Qué formatos entiende el cliente |
| `Authorization` | Credenciales |
| `Connection` | `close` o `keep-alive` |

**`Host` es obligatorio desde HTTP/1.1** y la razón es histórica: permite que muchos sitios compartan una IP. El servidor lee ese header para saber cuál de los sitios que aloja tiene que responder. Sin eso, cada dominio necesitaría su propia dirección — y ya vimos en la clase 12 lo escasas que son.

### Keep-alive: no cerrar la conexión

En HTTP/1.0, cada pedido abría una conexión TCP y la cerraba al responder. Con el handshake de tres vías de la clase 12, eso significa pagar un ida y vuelta completo **por cada imagen** de una página.

HTTP/1.1 cambió el default: la conexión **queda abierta** para pedidos siguientes, salvo que alguien mande `Connection: close`.

Es una optimización que conocen: es exactamente el argumento de la clase 13 sobre por qué conviene reutilizar conexiones en vez de abrir una por mensaje.

---

## http.server: donde reaparece socketserver

La biblioteca estándar trae un servidor HTTP. Antes de usarlo, mirá de qué está hecho:

```python
import http.server, socketserver

print(http.server.HTTPServer.__bases__)
# (<class 'socketserver.TCPServer'>,)

print(http.server.ThreadingHTTPServer.__bases__)
# (<class 'socketserver.ThreadingMixIn'>, <class 'http.server.HTTPServer'>)

print(http.server.BaseHTTPRequestHandler.__bases__)
# (<class 'socketserver.StreamRequestHandler'>,)
```

**Es el módulo de la clase 16, entero.** `HTTPServer` es un `TCPServer`; `ThreadingHTTPServer` usa el mismo `ThreadingMixIn` que vieron; y el handler hereda de `StreamRequestHandler`, o sea que trae `rfile`/`wfile` con framing por líneas —que es justo lo que HTTP necesita.

Un servidor HTTP completo:

```python
#!/usr/bin/env python3
import http.server
import json

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):                          # se llama para los GET
        cuerpo = json.dumps({'ruta': self.path}).encode()
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(cuerpo)))
        self.end_headers()
        self.wfile.write(cuerpo)

    def do_POST(self):                         # y este para los POST
        n = int(self.headers.get('Content-Length', 0))
        datos = self.rfile.read(n)             # leer exactamente n bytes
        self.send_response(201)
        self.end_headers()
        self.wfile.write(b'creado')

with http.server.ThreadingHTTPServer(('', 8080), Handler) as srv:
    srv.serve_forever()
```

Fijate el mecanismo de despacho: **el handler define `do_GET`, `do_POST`, etc., y el framework llama al que corresponde** según el método del pedido. Es el template method de la clase 16 con una vuelta más: `socketserver` llama a `handle()`, el `handle()` de HTTP parsea el pedido, y después llama a tu `do_GET()`.

Y el `self.rfile.read(n)` del `do_POST` es la clase 13 en acción: hay que leer exactamente `Content-Length` bytes, ni más ni menos, porque después de eso empieza el pedido siguiente en la misma conexión.

Esto funciona, pero para una API real es tedioso: parsear la ruta a mano, validar los datos, serializar JSON, manejar errores. Ahí entra FastAPI.

---

## FastAPI: el salto

### Instalación

```bash
python3 -m venv venv
source venv/bin/activate
pip install fastapi uvicorn
```

`uvicorn` es el servidor que corre la aplicación. FastAPI define *qué* responde; uvicorn se encarga del socket, el protocolo y el event loop.

### La API mínima

```python
#!/usr/bin/env python3
from fastapi import FastAPI

app = FastAPI()

@app.get('/')
def raiz():
    return {'mensaje': 'hola'}

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='127.0.0.1', port=8000)
```

Guardalo como `mi_api.py` y corrélo:

```bash
python3 mi_api.py
```

Hay una segunda forma, que es la que vas a ver en la documentación:

```bash
uvicorn mi_api:app --reload
```

Las dos hacen lo mismo. La diferencia es que `--reload` reinicia el servidor cada vez que guardás el archivo, lo cual es cómodo mientras desarrollás. Para que funcione, uvicorn necesita **el nombre del módulo como string** (`'mi_api:app'`), no el objeto: tiene que poder reimportarlo.

> **Todos los ejemplos que siguen son archivos completos**: copialos, guardalos y corrélos con `python3 archivo.py`. Cada uno arranca en el puerto 8000.

Tres líneas de lógica y tenés un servidor HTTP que devuelve JSON. Comparado con el `http.server` de arriba: no hay `send_response`, ni `Content-Type`, ni `json.dumps`, ni `Content-Length`. El framework lo deduce del valor que devolvés.

El decorador `@app.get('/')` hace dos cosas: registra la función para esa ruta y para ese método. Un `@app.post('/tareas')` registraría otra.

### Parámetros: en la ruta y en la query

```python
#!/usr/bin/env python3
from fastapi import FastAPI

app = FastAPI()

@app.get('/tareas/{tarea_id}')
def obtener(tarea_id: int):              # el tipo NO es decorativo
    return {'id': tarea_id}

@app.get('/tareas')
def listar(estado: str = 'todos', limite: int = 10):
    return {'estado': estado, 'limite': limite}

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='127.0.0.1', port=8000)
```

Lo que llama la atención es el `: int`. En Python normal una anotación de tipo es documentación que nadie verifica. **Acá FastAPI la usa de verdad**: convierte el string de la URL a entero, y si no puede, rechaza el pedido con un 422 antes de ejecutar tu función.

```bash
curl localhost:8000/tareas/abc
```

```json
{"detail":[{"type":"int_parsing","loc":["path","tarea_id"],
  "msg":"Input should be a valid integer, unable to parse string as an integer"}]}
```

Los parámetros que no están en la ruta se leen de la query string: `/tareas?estado=pendiente&limite=5`. Y los que tienen valor por defecto son opcionales.

### Cuerpos con Pydantic

Para recibir JSON se declara un modelo:

```python
#!/usr/bin/env python3
from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI()

class TareaNueva(BaseModel):
    tipo: str = Field(min_length=1)
    prioridad: int = Field(default=1, ge=1, le=5)

@app.post('/tareas', status_code=201)
def crear(tarea: TareaNueva):            # FastAPI ve el tipo y arma el objeto
    return {'recibido': tarea.tipo, 'prioridad': tarea.prioridad}

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='127.0.0.1', port=8000)
```

FastAPI lee el cuerpo, lo parsea como JSON, lo valida contra el modelo, y te entrega un objeto ya construido. Si algo no cumple, responde 422 con el detalle:

```bash
curl -X POST localhost:8000/tareas -H 'Content-Type: application/json' \
     -d '{"tipo":"x","prioridad":99}'
```

```json
{"detail":[{"type":"less_than_equal","loc":["body","prioridad"],
  "msg":"Input should be less than or equal to 5","input":99}]}
```

El `loc` dice exactamente dónde está el problema: en el cuerpo, campo `prioridad`. Escribir esa validación a mano —y devolver errores así de precisos— serían decenas de líneas por endpoint.

### Errores propios

```python
#!/usr/bin/env python3
from fastapi import FastAPI, HTTPException

app = FastAPI()
tareas = {1: {'id': 1, 'tipo': 'esperar'}}      # datos de ejemplo

@app.get('/tareas/{tarea_id}')
def obtener(tarea_id: int):
    if tarea_id not in tareas:
        raise HTTPException(status_code=404, detail='No existe esa tarea')
    return tareas[tarea_id]

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='127.0.0.1', port=8000)
```

`HTTPException` se lanza como cualquier excepción y FastAPI la convierte en la respuesta correspondiente. Es más limpio que devolver diccionarios de error: podés lanzarla desde cualquier profundidad de llamadas.

### La documentación que se escribe sola

Con el servidor andando, entrá a:

```
http://localhost:8000/docs
```

Hay una interfaz donde se ven todos los endpoints, sus parámetros, los modelos con sus restricciones, y un botón para probarlos.

No la escribió nadie: FastAPI la genera a partir de las anotaciones de tipo y los modelos Pydantic, siguiendo el estándar OpenAPI. El mismo dato —el `: int`, el `ge=1, le=5`— sirve para tres cosas a la vez: validar, documentar y generar la interfaz de prueba.

Eso es lo que distingue a FastAPI de frameworks anteriores, y la razón de su adopción.

---

## Dónde está el event loop

Antes de hablar de `async def`, conviene ubicar las piezas. Cuando corrés `uvicorn mi_api:app`, hay tres capas trabajando, y confundirlas hace que el resto no se entienda.

```
   uvicorn            el servidor: socket, event loop, protocolo HTTP
      |
   ASGI               el contrato entre ambos (una especificación, no código tuyo)
      |
   FastAPI            tu aplicación: rutas, validación, respuestas
```

**uvicorn es el que tiene el event loop.** Es un servidor ASGI: abre el socket, escucha el puerto, parsea HTTP, y —lo que nos importa— **crea y corre el `asyncio` loop**. Es, en esencia, lo que construimos en la clase 17 con `selectors` y refinamos en la 18 con corrutinas, pero implementado en serio.

**FastAPI no tiene event loop propio.** Es una aplicación ASGI: un objeto que uvicorn invoca cuando llega un pedido. FastAPI decide *qué* responder; uvicorn se ocupa de *cómo* moverlo por la red.

**ASGI es el contrato entre los dos.** Las siglas son *Asynchronous Server Gateway Interface*: interfaz asíncrona de pasarela para servidores. No es una biblioteca que instalás, sino una especificación que define cómo un servidor le pasa un pedido a una aplicación asíncrona. Gracias a ese estándar, podés cambiar uvicorn por hypercorn o daphne sin tocar tu código, y correr FastAPI, Starlette o Django sobre el mismo servidor. El nombre viene de **WSGI** (*Web Server Gateway Interface*), el estándar equivalente de 2003 para aplicaciones sincrónicas — lo que permitió que Flask y Django corrieran sobre gunicorn, mod_wsgi o waitress indistintamente. La *A* de adelante marca la diferencia: ASGI agrega asincronía, y con eso la posibilidad de WebSockets y conexiones de larga duración, que en WSGI no se podían expresar.

### Verlo con los propios ojos

No hace falta creerlo. Un endpoint puede preguntar en qué contexto está corriendo:

```python
#!/usr/bin/env python3
import asyncio, os, threading
from fastapi import FastAPI

app = FastAPI()

@app.get('/quien-soy')
async def quien_soy():
    loop = asyncio.get_running_loop()
    return {
        'pid': os.getpid(),
        'thread': threading.current_thread().name,
        'loop': type(loop).__name__,
        'id_del_loop': id(loop),
    }

@app.get('/quien-soy-sync')
def quien_soy_sync():
    try:
        asyncio.get_running_loop()
        estado = 'HAY loop'
    except RuntimeError:
        estado = 'NO hay loop corriendo acá'
    return {'thread': threading.current_thread().name, 'loop': estado}

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='127.0.0.1', port=8000)
```

La salida del endpoint `async`, pedida dos veces:

```json
{"pid":93944,"thread":"MainThread","loop":"_UnixSelectorEventLoop","id_del_loop":140039615234800}
{"pid":93944,"thread":"MainThread","loop":"_UnixSelectorEventLoop","id_del_loop":140039615234800}
```

Tres cosas a mirar:

**Corre en `MainThread`.** No hay un thread por pedido, como en la clase 14: todos los endpoints `async` comparten el hilo principal.

**El `id` del loop es idéntico en ambos pedidos.** Hay **un solo** event loop para toda la aplicación, creado una vez al arrancar. Cada pedido es una tarea más en ese loop.

**Se llama `_UnixSelectorEventLoop`.** El nombre delata la implementación: usa el módulo `selectors` de la clase 17, o sea `epoll` en Linux. El bucle que escribimos a mano está literalmente abajo de FastAPI.

Y el endpoint sincrónico:

```json
{"thread":"AnyIO worker thread","loop":"NO hay loop corriendo acá"}
```

Otro hilo, y sin loop. Eso confirma lo que vamos a ver enseguida: FastAPI manda las funciones `def` a un **threadpool** aparte, fuera del event loop, para que puedan bloquear sin arrastrar a nadie.

### Cuántos procesos

Un solo event loop significa un solo core. Para aprovechar la máquina, uvicorn puede levantar varios procesos:

```bash
uvicorn mi_api:app --workers 4
```

Eso arranca cuatro procesos independientes, **cada uno con su propio event loop**, y el sistema operativo reparte las conexiones entre ellos —el `SO_REUSEPORT` que vimos en las manijas de la clase 17.

Es la combinación que usan los servidores modernos: **procesos para aprovechar los cores, event loop para las conexiones dentro de cada proceso**. Resuelve lo que la clase 14 no podía, sin caer en un thread por cliente.

Y tiene una consecuencia de diseño importante para el TP2: **con varios workers, el estado en memoria no se comparte**. Un diccionario global vive en un proceso y los otros tres no lo ven. Es la misma disyuntiva de `ForkingMixIn` en la clase 16, y la razón por la que en producción el estado va a una base de datos o a Redis.

> Durante el desarrollo se usa `--reload`, que implica **un solo worker**. Por eso un estado en memoria parece funcionar mientras probás y falla al desplegar con varios.

---

## async en FastAPI: por qué ahora tiene sentido

Los endpoints se pueden escribir de dos formas:

```python
#!/usr/bin/env python3
import asyncio
import time

from fastapi import FastAPI

app = FastAPI()

@app.get('/async-bien')
async def async_bien():
    await asyncio.sleep(1)            # cede el control
    return {'ok': True}

@app.get('/async-mal')
async def async_mal():
    time.sleep(1)                     # NO cede: bloquea el event loop
    return {'ok': True}

@app.get('/sync')
def sincronico():
    time.sleep(1)                     # def común: va al threadpool
    return {'ok': True}

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='127.0.0.1', port=8000)
```

La clase pasada construimos el mecanismo que hay detrás del `async def`, así que esto ya no es magia: uvicorn corre un event loop, y cada endpoint `async` es una corrutina que el loop intercala con las demás.

Pero hay un detalle que **no** es obvio, y conviene medirlo. Levantá ese archivo y mandale tres pedidos simultáneos a cada ruta:

```bash
python3 tres_estilos.py &
for r in async-bien async-mal sync; do
  echo -n "  /$r  "
  ( time (for i in 1 2 3; do curl -s localhost:8000/$r & done; wait) ) 2>&1 | grep real
done
```

Los números que da (es lo que mide `medir.py`):

| Endpoint | Cómo está escrito | 3 pedidos |
|----------|-------------------|-----------|
| `/lento-async` | `async def` + `await asyncio.sleep(1)` | **1.06s** |
| `/lento-mal` | `async def` + `time.sleep(1)` | **3.03s** |
| `/lento-sync` | `def` común + `time.sleep(1)` | **1.06s** |

El primero es lo esperado: las tres esperas se solapan.

El segundo es el bug de la clase 18 con otra ropa. `time.sleep()` dentro de una corrutina no cede el control, así que bloquea el event loop y **con él, todos los pedidos**. Tres segundos en vez de uno.

El tercero sorprende: un `def` común anda **igual de bien** que el async bien escrito. La razón es que FastAPI detecta que la función no es corrutina y la manda a un **threadpool**, fuera del event loop. Ahí puede bloquear sin molestar a nadie.

La conclusión es contraintuitiva y vale la pena decirla claro:

> **Un `def` común es mejor que un `async def` mal escrito.** Si tu función hace algo bloqueante y no tenés una alternativa asíncrona, escribila como `def` normal y dejá que FastAPI la mande al threadpool.

La regla práctica:

| Tu función | Escribila como |
|------------|----------------|
| Solo espera I/O con bibliotecas async (`httpx`, `asyncpg`) | `async def` |
| Usa bibliotecas bloqueantes (`requests`, DB sincrónica) | `def` |
| Hace cálculo pesado | `def` (y para el TP2, un executor) |
| No hace nada lento | cualquiera |

Lo peligroso es el caso del medio escrito mal: `async def` con algo bloqueante adentro. Eso no da error, no avisa, y degrada todo el servidor.

---

## Conceptos clave

1. **HTTP es texto plano sobre TCP**: se puede escribir a mano con `nc`.
2. **Pedido y respuesta tienen tres partes**: línea inicial, headers, cuerpo.
3. **HTTP usa los dos framings de la clase 13**: línea vacía para los headers, `Content-Length` para el cuerpo.
4. **Los separadores son `\r\n`**, no `\n`.
5. **`GET` es seguro e idempotente**; `POST` no es ninguna de las dos, y por eso reintentar puede duplicar.
6. **`4xx` es culpa del cliente y `5xx` del servidor**: mentir ahí complica a quien usa tu API.
7. **`Host` es obligatorio en HTTP/1.1** y es lo que permite varios sitios por IP.
8. **`http.server` es `socketserver` con un handler HTTP**: `BaseHTTPRequestHandler` hereda de `StreamRequestHandler`.
9. **FastAPI usa las anotaciones de tipo para validar de verdad**, no como documentación.
10. **Pydantic valida el cuerpo** y devuelve 422 con la ubicación exacta del error.
11. **`/docs` se genera solo** a partir de los tipos y modelos.
12. **El event loop lo tiene uvicorn, no FastAPI**: uvicorn es el servidor ASGI; FastAPI es la aplicación.
13. **Hay un solo event loop por proceso**, en el hilo principal: verificable por el `id()` del loop.
14. **`--workers N` son N procesos con N loops**, y entre ellos no se comparte memoria.
15. **Un `def` común va a un threadpool** (AnyIO worker thread), fuera del loop; un `async def` corre en el event loop.
16. **`async def` con código bloqueante adentro es peor que un `def` común**: medido, 3.03s contra 1.06s.

---

## Preparación para la próxima clase

En la **clase 20 (Asyncio en red)** volvemos al hilo que quedó abierto. En la 18 construimos el event loop y vimos `await` sobre temporizadores; hoy usamos un framework que lo esconde. La clase que viene hacemos **I/O de red asíncrono directamente**: `open_connection`, `start_server`, y el servidor eco de la clase 13 reescrito en versión asíncrona.

Ahí se cierra el círculo del bloque: los sockets de la 13, la concurrencia de la 14, el multiplexing de la 17 y las corrutinas de la 18, todo junto.

Hoy además se entrega el **enunciado del TP2**.

Para llegar preparado:

- Levantá `api.py` y jugá con `/docs` hasta que te resulte natural.
- Corré `medir.py` y entendé por qué el `async def` mal escrito es el peor de los tres.

---

## Referencias

- [RFC 9110](https://www.rfc-editor.org/rfc/rfc9110) - semántica de HTTP: métodos, códigos, headers
- [MDN: HTTP](https://developer.mozilla.org/es/docs/Web/HTTP) - la referencia práctica, en español
- [FastAPI](https://fastapi.tiangolo.com/) - documentación oficial, con un tutorial muy bueno
- [Pydantic](https://docs.pydantic.dev/) - validación y modelos
- [`http.server`](https://docs.python.org/3/library/http.server.html) - el de la stdlib, construido sobre socketserver

---

*Computación II - 2026 - Clase 19*
