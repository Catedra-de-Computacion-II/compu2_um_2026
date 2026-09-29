# Clase 19: HTTP + FastAPI - Autoevaluación

> Completá esta autoevaluación **después** de leer el contenido y hacer los ejercicios.
> No mires las respuestas antes de intentarlo.

---

## Parte 1: El protocolo

**Pregunta 1.** ¿Sobre qué corre HTTP?

a) Sobre UDP
b) Sobre una conexión TCP
c) Directamente sobre IP
d) Sobre un protocolo propio

**Pregunta 2.** ¿Cuáles son las tres partes de un pedido HTTP?

a) Método, ruta y versión
b) Línea inicial, headers y cuerpo
c) Cabecera, datos y checksum
d) Origen, destino y carga

**Pregunta 3.** ¿Qué separa los headers del cuerpo?

a) Un punto y coma
b) Una línea vacía
c) El header `Content-Length`
d) Un byte nulo

**Pregunta 4.** ¿Cómo sabe el receptor dónde termina el cuerpo?

a) Por la línea vacía
b) Por `Content-Length`, o por codificación chunked
c) Porque se cierra la conexión, siempre
d) No se puede saber

**Pregunta 5.** Esos dos mecanismos, ¿a qué corresponden de la clase 13?

a) A nada, son propios de HTTP
b) A los dos tipos de framing: delimitador y prefijo de longitud
c) Al handshake de TCP
d) Al control de flujo

**Pregunta 6.** ¿Qué separador de línea usa HTTP?

a) `\n`
b) `\r\n`
c) `\r`
d) Cualquiera

**Pregunta 7.** ¿Qué significa que `GET` sea **seguro**?

a) Que va cifrado
b) Que no modifica nada en el servidor
c) Que requiere autenticación
d) Que no puede fallar

**Pregunta 8.** ¿Qué significa **idempotente**?

a) Que siempre devuelve lo mismo
b) Que repetirlo da el mismo resultado que hacerlo una vez
c) Que no tiene cuerpo
d) Que es rápido

**Pregunta 9.** ¿Cuál de estos NO es idempotente?

a) `GET`
b) `PUT`
c) `POST`
d) `DELETE`

**Pregunta 10.** Un `POST` falla por timeout. ¿Es seguro reintentarlo?

a) Sí, siempre
b) No: podría crear el recurso dos veces
c) Solo con HTTPS
d) Da igual

**Pregunta 11.** ¿Qué indica un código `4xx`?

a) Error del servidor
b) Error del cliente
c) Redirección
d) Éxito parcial

**Pregunta 12.** ¿Cuál es la respuesta correcta a un `POST` que crea un recurso?

a) 200 OK
b) 201 Created
c) 204 No Content
d) 302 Found

**Pregunta 13.** ¿Y a un `DELETE` exitoso que no devuelve nada?

a) 200
b) 204
c) 404
d) 410

**Pregunta 14.** ¿Por qué `Host` es obligatorio en HTTP/1.1?

a) Por seguridad
b) Porque permite alojar muchos sitios en una misma IP
c) Para el cacheo
d) Para la compresión

**Pregunta 15.** ¿Qué cambió HTTP/1.1 respecto de 1.0 en cuanto a conexiones?

a) Nada
b) La conexión queda abierta por defecto (keep-alive)
c) Usa UDP
d) Abre una conexión por header

---

## Parte 2: http.server

**Pregunta 16.** ¿De qué hereda `HTTPServer`?

a) De `BaseServer` directamente
b) De `socketserver.TCPServer`
c) De `object`
d) De `ThreadingMixIn`

**Pregunta 17.** ¿Y `BaseHTTPRequestHandler`?

a) De `BaseRequestHandler`
b) De `socketserver.StreamRequestHandler`
c) De `DatagramRequestHandler`
d) De nada, es independiente

**Pregunta 18.** ¿Qué le aporta esa herencia?

a) Concurrencia
b) `rfile`/`wfile` con framing por líneas, que es lo que HTTP necesita
c) Cifrado
d) Validación

**Pregunta 19.** ¿Cómo despacha `BaseHTTPRequestHandler` según el método?

a) Con un `if` en `handle()`
b) Llamando a `do_GET`, `do_POST`, etc., según corresponda
c) Con un diccionario que configurás vos
d) No despacha: hay un handler por método

**Pregunta 20.** ¿Qué devuelve si mandás un método sin `do_` correspondiente?

a) 404
b) 501 Not Implemented
c) 400
d) Se cae el servidor

**Pregunta 21.** En un `do_POST`, ¿por qué hay que leer exactamente `Content-Length` bytes?

a) Por eficiencia
b) Porque después de eso empieza el pedido siguiente en la misma conexión
c) Porque `rfile` no soporta más
d) No hace falta

---

## Parte 3: FastAPI

**Pregunta 22.** ¿Qué hace FastAPI con la anotación `tarea_id: int`?

a) Nada, es documentación
b) Convierte y valida: si no es un entero, devuelve 422 sin ejecutar tu función
c) Solo la muestra en `/docs`
d) La ignora en producción

**Pregunta 23.** ¿Para qué sirve un modelo de Pydantic en un endpoint?

a) Para documentar nada más
b) Para declarar y validar el cuerpo del pedido
c) Para configurar el servidor
d) Para definir la ruta

**Pregunta 24.** ¿Qué código devuelve FastAPI si los datos no pasan la validación?

a) 400
b) 422
c) 500
d) 404

**Pregunta 25.** En ese error, ¿qué indica el campo `loc`?

a) La línea del código
b) Dónde está el dato inválido: cuerpo o ruta, y qué campo
c) El servidor que falló
d) La localización geográfica

**Pregunta 26.** ¿Cómo se devuelve un error propio, como un 404?

a) `return {'error': 'no existe'}`
b) `raise HTTPException(status_code=404, detail='...')`
c) `exit(404)`
d) `self.send_response(404)`

**Pregunta 27.** ¿Quién escribe la documentación de `/docs`?

a) Vos, en un archivo aparte
b) Se genera sola a partir de los tipos y los modelos
c) Un servicio externo
d) No existe

---

## Parte 4: El event loop

**Pregunta 28.** ¿Quién crea y corre el event loop?

a) FastAPI
b) uvicorn
c) Python al importar asyncio
d) El sistema operativo

**Pregunta 29.** ¿Qué es ASGI?

a) Un servidor
b) La interfaz estándar entre un servidor y una aplicación asíncrona
c) Un formato de datos
d) Una biblioteca de validación

**Pregunta 30.** ¿Cuántos event loops hay en un proceso de uvicorn?

a) Uno por pedido
b) Uno solo, en el hilo principal
c) Uno por endpoint
d) Depende de la carga

**Pregunta 31.** ¿En qué thread corre un endpoint `async def`?

a) En un thread nuevo por pedido
b) En el hilo principal, donde está el event loop
c) En un proceso aparte
d) En un AnyIO worker

**Pregunta 32.** ¿Y un endpoint `def` común?

a) En el hilo principal
b) En un threadpool, fuera del event loop
c) No se ejecuta
d) En otro proceso

**Pregunta 33.** ¿Qué hace `uvicorn api:app --workers 4`?

a) Cuatro threads en un proceso
b) Cuatro procesos, cada uno con su event loop
c) Cuatro event loops en un proceso
d) Cuatro conexiones simultáneas

**Pregunta 34.** Con varios workers, ¿qué pasa con un diccionario global?

a) Se comparte entre todos
b) Cada proceso tiene el suyo: los cambios no se ven entre workers
c) Se sincroniza automáticamente
d) Da error

---

## Parte 5: async bien y mal

**Pregunta 35.** Tres pedidos a un endpoint `async def` con `await asyncio.sleep(1)`. ¿Cuánto tardan?

a) ~3 s
b) ~1 s
c) ~0.3 s
d) Depende de los cores

**Pregunta 36.** Los mismos tres, pero el endpoint es `async def` con `time.sleep(1)`. ¿Cuánto?

a) ~1 s
b) ~3 s
c) Igual que el anterior
d) Falla

**Pregunta 37.** ¿Por qué?

a) `time.sleep` es más lento
b) No cede el control: bloquea el event loop y con él todos los pedidos
c) Porque lanza excepción
d) Por el GIL

**Pregunta 38.** Y si el endpoint es `def` común con `time.sleep(1)`, ¿cuánto tardan los tres?

a) ~3 s
b) ~1 s, porque FastAPI lo manda a un threadpool
c) Falla
d) ~9 s

**Pregunta 39.** Entonces, ¿qué conviene si tu función usa una biblioteca bloqueante como `requests`?

a) `async def`, siempre
b) `def` común, para que vaya al threadpool
c) No usar FastAPI
d) Es indistinto

**Pregunta 40.** ¿Cuál es el caso peligroso?

a) Un `def` común
b) Un `async def` con código bloqueante adentro: no avisa y degrada todo
c) Un `async def` bien escrito
d) Usar muchos workers

---

## Respuestas

<details>
<summary>Ver respuestas (intentá primero)</summary>

| # | Respuesta | Comentario |
|---|-----------|------------|
| 1 | b | Es un protocolo de aplicación sobre TCP |
| 2 | b | Línea inicial, headers, cuerpo |
| 3 | b | Una línea vacía |
| 4 | b | `Content-Length` o chunked |
| 5 | b | Delimitador y prefijo de longitud |
| 6 | b | CRLF, no solo `\n` |
| 7 | b | No modifica estado |
| 8 | b | Repetirlo no cambia el resultado |
| 9 | c | `POST` crea algo nuevo cada vez |
| 10 | b | Podría duplicar el recurso |
| 11 | b | Culpa del cliente |
| 12 | b | 201 Created |
| 13 | b | 204 No Content |
| 14 | b | Varios sitios por IP |
| 15 | b | Keep-alive por defecto |
| 16 | b | `TCPServer`, de la clase 16 |
| 17 | b | `StreamRequestHandler` |
| 18 | b | `rfile`/`wfile` con framing |
| 19 | b | Template method, un nivel más |
| 20 | b | 501, verificado |
| 21 | b | Keep-alive: sigue otro pedido |
| 22 | b | Valida de verdad, no decora |
| 23 | b | Declarar y validar el cuerpo |
| 24 | b | 422 Unprocessable |
| 25 | b | Ubicación exacta del error |
| 26 | b | `HTTPException` |
| 27 | b | Se genera de los tipos (OpenAPI) |
| 28 | b | uvicorn, el servidor ASGI |
| 29 | b | El contrato servidor-aplicación |
| 30 | b | Uno por proceso |
| 31 | b | MainThread, verificado |
| 32 | b | AnyIO worker thread |
| 33 | b | Procesos con loop propio |
| 34 | b | No se comparte memoria |
| 35 | b | ~1 s: se solapan |
| 36 | b | ~3 s: medido |
| 37 | b | Bloquea el loop único |
| 38 | b | ~1 s: threadpool |
| 39 | b | `def` común |
| 40 | b | El bug silencioso |

</details>

---

## Resultado de la autoevaluación

| Puntaje | Diagnóstico |
|---------|-------------|
| 35-40 correctas | Excelente. Avanzá a la clase 20 (Asyncio en red) |
| 28-34 | Buen nivel. Repasá los temas donde fallaste |
| 20-27 | Nivel intermedio. Rehacé el ejercicio 3 (la API) y el 5 |
| < 20 | Repasá el contenido completo. Consultá con el docente antes de la próxima clase |

> Las preguntas 28 a 34 son las que más importan para el TP2: dónde vive el event loop y qué implica tener varios workers. Y la 40 describe el bug que más cuesta diagnosticar en un servidor async.

---

*Computación II - 2026 - Clase 19*
