# Clase 19: HTTP + FastAPI - Ejercicios Prácticos

Los archivos `crudo.py`, `api.py` y `medir.py` acompañan la clase.

Para la segunda mitad hace falta instalar FastAPI:

```bash
python3 -m venv venv
source venv/bin/activate
pip install fastapi uvicorn httpx
```

> **Windows / PowerShell:** los comandos `curl` de esta guía asumen Linux o macOS. En PowerShell, `curl` es un alias de `Invoke-WebRequest` y no acepta `-X`, `-H` ni `-d`. Usá `curl.exe` en su lugar (escapando las comillas del JSON con `\"`), o `Invoke-RestMethod`, o directamente la interfaz de `/docs`. Hay ejemplos en el apunte.

---

## Ejercicio 1: El protocolo a mano

### 1.1 Hablar HTTP por socket

```bash
printf 'GET / HTTP/1.1\r\nHost: example.com\r\nConnection: close\r\n\r\n' | nc example.com 80
```

1. Identificá en la respuesta las tres partes: línea de estado, headers, cuerpo. ¿Qué las separa?
2. ¿Qué código de estado devolvió? ¿Qué familia es?
3. Sacá el header `Host:` y repetí. ¿Qué pasa? ¿Por qué HTTP/1.1 lo exige?
4. Cambiá `GET /` por `GET /noexiste`. ¿Qué código devuelve ahora?

### 1.2 Los finales de línea

5. Probá el mismo pedido usando `\n` en vez de `\r\n`. ¿Funciona contra `example.com`? ¿Y contra el servidor de `crudo.py`?
6. ¿Por qué es mala idea depender de que un servidor tolere `\n`?

### 1.3 Métodos y sus propiedades

7. ¿Cuáles de estos son **seguros** (no modifican nada): GET, POST, PUT, DELETE, HEAD?
8. ¿Cuáles son **idempotentes**? Explicá por qué `POST` no lo es.
9. Tu cliente manda un `POST` y le vence el timeout sin respuesta. ¿Es seguro reintentar? ¿Y si fuera un `PUT`?
10. Relacioná esto con el problema de deduplicación que vimos en UDP (clase 15).

---

## Ejercicio 2: http.server es socketserver

```bash
python3 crudo.py
```

1. Mirá la primera sección. ¿De qué clase hereda `BaseHTTPRequestHandler`? ¿Qué le aporta eso?
2. ¿Qué mixin usa `ThreadingHTTPServer`? ¿Es el mismo de la clase 16?
3. En el `do_POST` de `crudo.py`, ¿por qué hay que leer exactamente `Content-Length` bytes y no `recv(4096)`?
4. La respuesta dice `HTTP/1.0` aunque pedimos 1.1. Buscá `protocol_version` en la documentación: ¿qué cambia si lo ponés en `HTTP/1.1`?

### 2.1 Tu propio servidor

Levantá el servidor y probalo:

```bash
python3 crudo.py servidor
curl localhost:8080/hola
curl -X POST localhost:8080/ -d 'algo'
```

5. Agregale un `do_DELETE`. ¿Qué código de estado conviene devolver?
6. ¿Qué pasa si mandás un método que no implementaste, como `PATCH`? ¿Qué código devuelve el framework solo?
7. Compará el código de `crudo.py` con `api.py`. Contá las líneas que hacen falta para un endpoint en cada uno.

---

## Ejercicio 3: Una API con FastAPI (obligatorio)

### Objetivo

Construir el esqueleto de la API del TP2, con validación y errores correctos.

### Parte A: lo mínimo

```bash
python3 api.py
```

1. Entrá a `http://localhost:8000/docs`. ¿Quién escribió esa documentación?
2. Probá los endpoints desde ahí. ¿Qué pasa si mandás un `tipo` que no está en la lista?
3. Mirá `http://localhost:8000/openapi.json`. ¿Qué es ese archivo?

### Parte B: la validación

4. Provocá cada uno de estos errores y anotá el código y el mensaje:

```bash
curl localhost:8000/tareas/abc
curl -X POST localhost:8000/tareas -H 'Content-Type: application/json' -d '{"tipo":"volar"}'
curl -X POST localhost:8000/tareas -H 'Content-Type: application/json' -d '{"tipo":"esperar","prioridad":99}'
curl localhost:8000/tareas/999
```

5. ¿Cuáles dan 422 y cuál da 404? ¿Por qué son distintos?
6. En el JSON de error hay un campo `loc`. ¿Qué información da?
7. ¿En qué momento se ejecuta la validación: antes o después de tu función? Comprobalo con un `print`.

### Parte C: agregar endpoints

Extendé `api.py`:

8. `PATCH /tareas/{id}` que cambie solo el estado. Necesitás un modelo nuevo con todos los campos opcionales.
9. `GET /estadisticas` que devuelva la cantidad de tareas por estado.
10. Hacé que `POST /tareas` rechace una tarea si ya hay 10 pendientes, con un código de estado apropiado. ¿Cuál elegís y por qué?

### Parte D: los tipos importan

11. Sacale la anotación `: int` al parámetro de `obtener()`. ¿Qué cambia al pedir `/tareas/abc`?
12. Cambiá `prioridad: int` por `prioridad: str` en el modelo. ¿Qué acepta ahora?
13. ¿Qué tres cosas hace FastAPI con cada anotación de tipo?

---

## Ejercicio 4: Dónde está el event loop

```bash
python3 api.py
curl localhost:8000/quien-soy
curl localhost:8000/quien-soy
curl localhost:8000/quien-soy-sync
```

1. ¿En qué thread corre el endpoint `async`? ¿Y el `def` común?
2. Pedí `/quien-soy` dos veces y compará el `id_del_loop`. ¿Hay uno o varios event loops?
3. ¿Por qué el endpoint sincrónico dice que no hay loop corriendo?
4. ¿Quién crea el event loop: FastAPI o uvicorn? ¿Qué es ASGI?
5. Levantá con `uvicorn api:app --workers 3` y pedí `/quien-soy` varias veces. ¿Cambia el `pid`?
6. Con varios workers, ¿qué pasa con el diccionario `tareas`? Probá: creá una tarea y pedila varias veces hasta que dé 404. Explicá por qué.
7. ¿Qué implica eso para el TP2? ¿Dónde debería vivir el estado en un sistema real?

---

## Ejercicio 5: async bien y mal

```bash
python3 medir.py
```

1. Copiá los tres tiempos que te dio.
2. ¿Por qué `/async-mal` tarda el triple? Relacionalo con la regla de la clase 18.
3. ¿Por qué `/sync` anda igual de bien que `/async-bien`, si también usa `time.sleep`?
4. Entonces, ¿cuándo conviene `async def` y cuándo `def`? Escribí la regla.
5. Este endpoint, ¿está bien o mal escrito? Justificá.

```python
@app.get('/datos')
async def datos():
    import requests
    return requests.get('https://api.ejemplo.com/cosas').json()
```

6. Arreglalo de dos formas distintas: una cambiando el `async def`, otra cambiando la biblioteca.
7. Agregale a `medir.py` un cuarto endpoint que haga cálculo pesado (un hash iterado). ¿Cuál de las tres formas conviene para eso? ¿Alguna lo resuelve bien?

---

## Verificación del ejercicio obligatorio

### Ejercicio 3: Una API con FastAPI

- [ ] La API levanta y `/docs` funciona
- [ ] Provocaste los cuatro errores y anotaste código y mensaje
- [ ] Explicaste la diferencia entre 422 y 404
- [ ] Comprobaste que la validación ocurre antes de tu función
- [ ] Agregaste `PATCH /tareas/{id}` con un modelo de campos opcionales
- [ ] Agregaste `GET /estadisticas`
- [ ] Justificaste el código de estado que elegiste para el límite de pendientes
- [ ] Explicaste qué hace FastAPI con las anotaciones de tipo

---

## Ejercicios adicionales

### Cliente HTTP a mano

Sin usar `requests` ni `httpx`: escribí un cliente que abra un socket, mande un `GET`, y parsee la respuesta separando línea de estado, headers y cuerpo. Manejá el caso de `Content-Length` ausente.

### Keep-alive

Con `protocol_version = 'HTTP/1.1'` en el handler de `crudo.py`, mandá **dos** pedidos por la misma conexión sin cerrarla. ¿Cómo sabés dónde termina la primera respuesta y empieza la segunda?

### El esqueleto del TP2

Tomá `api.py` y agregale los endpoints que pide el enunciado: `POST /tareas`, `GET /tareas`, `GET /tareas/{id}`, `DELETE /tareas/{id}`, `GET /estadisticas`. Que devuelvan datos falsos por ahora — la ejecución real viene en las clases siguientes.

### Middleware

Investigá `@app.middleware('http')` y agregá uno que mida cuánto tarda cada pedido y lo devuelva en un header `X-Tiempo`. ¿Dónde se ejecuta respecto de tu endpoint?

---

*Computación II - 2026 - Clase 19*
