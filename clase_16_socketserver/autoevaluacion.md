# Clase 16: socketserver - Autoevaluación

> Completá esta autoevaluación **después** de leer el contenido y hacer los ejercicios.
> No mires las respuestas antes de intentarlo.

---

## Parte 1: La jerarquía

**Pregunta 1.** ¿Cuál es la clase base abstracta de todos los servidores?

a) `TCPServer`
b) `BaseServer`
c) `SocketServer`
d) `BaseRequestHandler`

**Pregunta 2.** ¿Qué dos servidores concretos derivan de la base según el modelo conceptual?

a) `TCPServer` y `UDPServer`
b) `ThreadingServer` y `ForkingServer`
c) `StreamServer` y `DatagramServer`
d) `InetServer` y `UnixServer`

**Pregunta 3.** En el código real de Python, ¿de quién hereda `UDPServer`?

a) De `BaseServer` directamente
b) De `TCPServer`
c) De `UnixDatagramServer`
d) De nadie, es independiente

**Pregunta 4.** ¿Por qué esa herencia, si conceptualmente son hermanos?

a) Es un error del diseño
b) Reutilización de código: aprovecha el manejo de socket y sobrescribe lo que difiere
c) Porque UDP es un caso particular de TCP
d) Por compatibilidad con Python 2

**Pregunta 5.** ¿Qué usa `UnixStreamServer` en lugar de (IP, puerto)?

a) Un número de proceso
b) Una ruta del filesystem
c) Un identificador numérico
d) Una dirección IPv6

**Pregunta 6.** ¿Cómo se configura un servidor de `socketserver`?

a) Por parámetros del constructor
b) Por atributos de clase
c) Por un archivo de configuración
d) Por variables de entorno

**Pregunta 7.** ¿A qué equivale `allow_reuse_address = True`?

a) A permitir varias IPs
b) Al `setsockopt(SO_REUSEADDR, 1)` de la clase 13
c) A habilitar IPv6
d) A aumentar el backlog

**Pregunta 8.** ¿Cuál es el valor por defecto de `allow_reuse_address`?

a) `True`
b) `False`
c) Depende del sistema
d) No tiene default

**Pregunta 9.** ¿A qué corresponde `request_queue_size`?

a) Al tamaño del buffer de recepción
b) Al argumento de `listen()`
c) A la cantidad máxima de clientes
d) Al timeout de las conexiones

**Pregunta 10.** ¿Qué hay que cambiar para que un servidor sea IPv6?

a) Reescribir la clase entera
b) El atributo `address_family` a `AF_INET6`
c) Usar `UnixStreamServer`
d) No se puede

---

## Parte 2: Los handlers

**Pregunta 11.** ¿Dónde va tu lógica de aplicación?

a) En el método `serve_forever()`
b) En el método `handle()` de una clase handler
c) En el constructor del servidor
d) En `process_request()`

**Pregunta 12.** Con `BaseRequestHandler` en TCP, ¿qué es `self.request`?

a) Una tupla (datos, socket)
b) El socket de la conexión
c) Un diccionario con la petición
d) Los bytes recibidos

**Pregunta 13.** ¿Y en UDP?

a) El socket
b) Una tupla (datos, socket)
c) Los bytes recibidos
d) La dirección del cliente

**Pregunta 14.** ¿Qué agrega `StreamRequestHandler`?

a) Concurrencia
b) `rfile` y `wfile`: objetos tipo archivo sobre el socket, con framing por líneas
c) Cifrado
d) Manejo automático de errores

**Pregunta 15.** ¿Sobre qué mecanismo de la clase 13 están construidos `rfile`/`wfile`?

a) `select()`
b) `makefile()`
c) `struct.pack()`
d) `shutdown()`

**Pregunta 16.** ¿Cuántas instancias de handler se crean si se conectan 10 clientes?

a) Una, compartida
b) Diez: una por conexión
c) Depende del mixin
d) Ninguna, son métodos estáticos

**Pregunta 17.** Entonces, ¿dónde se guarda el estado que debe sobrevivir entre conexiones?

a) En un atributo de instancia del handler
b) En el objeto servidor (`self.server`)
c) En una variable global
d) No se puede guardar

**Pregunta 18.** ¿Para qué sirve `self.client_address`?

a) Es la dirección del servidor
b) Es la tupla (IP, puerto) del cliente
c) Es el socket del cliente
d) Es el nombre del host

---

## Parte 3: El ciclo de vida

**Pregunta 19.** ¿Cuál es el orden correcto?

a) `handle()`, `setup()`, `finish()`
b) `setup()`, `handle()`, `finish()`
c) `setup()`, `finish()`, `handle()`
d) `finish()`, `setup()`, `handle()`

**Pregunta 20.** ¿Cómo se llama el patrón donde la clase base define el orden y vos completás los huecos?

a) Factory
b) Template method
c) Singleton
d) Observer

**Pregunta 21.** ¿Para qué sirve `verify_request()`?

a) Para validar el contenido del mensaje
b) Para decidir si atender o rechazar la conexión, antes de crear el handler
c) Para verificar el checksum
d) Para autenticar al usuario

**Pregunta 22.** ¿Qué pasa si `handle()` lanza una excepción no capturada?

a) El servidor se cae
b) `handle_error()` la registra y el servidor sigue atendiendo
c) La conexión queda colgada
d) Se reinicia el servidor

**Pregunta 23.** En ese caso, ¿se ejecuta `finish()`?

a) No, se saltea
b) Sí: la limpieza ocurre igual
c) Solo si se captura la excepción
d) Depende del mixin

**Pregunta 24.** ¿Cuándo se ejecutan `server_bind()` y `server_activate()`?

a) Una vez por conexión
b) Una sola vez, al construir el servidor
c) En cada llamada a `serve_forever()`
d) Nunca, son abstractos

---

## Parte 4: Los mixins

**Pregunta 25.** ¿Qué problema resuelven los mixins?

a) La lentitud del servidor
b) Evitar duplicar la jerarquía para cada combinación de protocolo y concurrencia
c) El manejo de errores
d) La compatibilidad con IPv6

**Pregunta 26.** ¿Qué método sobrescribe `ThreadingMixIn`?

a) `handle()`
b) `process_request()`
c) `serve_forever()`
d) `server_bind()`

**Pregunta 27.** ¿Cómo se define `ThreadingTCPServer`?

a) Heredando de `TCPServer` y reescribiendo todo
b) `class ThreadingTCPServer(ThreadingMixIn, TCPServer): pass`
c) Con un parámetro del constructor
d) Con un decorador

**Pregunta 28.** ¿Qué pasa si escribís `class Mio(TCPServer, ThreadingMixIn)`?

a) Da un error de sintaxis
b) No falla, pero el mixin queda inerte y el servidor atiende de a uno
c) Funciona igual
d) Lanza `TypeError` al instanciar

**Pregunta 29.** ¿Por qué pasa eso?

a) Por un bug de Python
b) Por el MRO: se resuelve de izquierda a derecha, y `TCPServer` gana
c) Porque los mixins solo van solos
d) Porque falta el `super()`

**Pregunta 30.** ¿Para qué sirve `daemon_threads = True`?

a) Para correr como demonio del sistema
b) Para que los threads no impidan que el proceso termine con Ctrl+C
c) Para aumentar la prioridad
d) Para limitar la cantidad de threads

**Pregunta 31.** ¿Qué hace `ForkingMixIn` que evita el problema de la clase 14?

a) No usa procesos
b) Cosecha los hijos automáticamente en `collect_children()`: no quedan zombies
c) Usa threads en vez de procesos
d) Ignora SIGCHLD

**Pregunta 32.** Con `ThreadingTCPServer` y estado compartido en el servidor, ¿qué hace falta?

a) Nada
b) Un `Lock`, porque los handlers corren en threads distintos sobre el mismo objeto
c) Un `Manager`
d) Un archivo temporal

**Pregunta 33.** Y con `ForkingTCPServer`, ¿qué pasa con ese estado?

a) Lo mismo que con threads
b) No se comparte: cada proceso tiene su copia y los cambios se pierden
c) Se corrompe
d) Se sincroniza solo

---

## Parte 5: Alcance

**Pregunta 34.** ¿Para qué NO sirve `socketserver`?

a) Servidores internos y herramientas
b) Prototipos
c) Miles de conexiones simultáneas
d) Protocolos de texto simples

**Pregunta 35.** ¿Qué módulo de la biblioteca estándar está construido sobre `socketserver`?

a) `socket`
b) `http.server`
c) `asyncio`
d) `selectors`

**Pregunta 36.** ¿Qué usa `serve_forever()` internamente para esperar conexiones?

a) Un `accept()` bloqueante
b) Un selector con timeout, lo que le permite responder a `shutdown()`
c) Un thread aparte
d) Polling activo

**Pregunta 37.** ¿Resuelve `socketserver` el problema C10K de la clase 14?

a) Sí, completamente
b) No: sigue siendo un thread o proceso por cliente, con los mismos límites
c) Sí, con `ForkingMixIn`
d) Solo en Linux

---

## Respuestas

<details>
<summary>Ver respuestas (intentá primero)</summary>

| # | Respuesta | Comentario |
|---|-----------|------------|
| 1 | b | `BaseServer` define la interfaz |
| 2 | a | TCP y UDP, cada uno con su variante Unix |
| 3 | b | Verificable con `UDPServer.__bases__` |
| 4 | b | Reutilización, no relación conceptual |
| 5 | b | Una ruta, como los sockets Unix de la clase 13 |
| 6 | b | Atributos de clase, estilo de la época |
| 7 | b | El `SO_REUSEADDR` de siempre |
| 8 | b | `False`: hay que activarlo a mano |
| 9 | b | El backlog de `listen()` |
| 10 | b | Un solo atributo |
| 11 | b | En `handle()` |
| 12 | b | El socket |
| 13 | b | Tupla: la asimetría que más confunde |
| 14 | b | `rfile`/`wfile` con framing por líneas |
| 15 | b | `makefile()` |
| 16 | b | Una instancia por conexión |
| 17 | b | En el servidor |
| 18 | b | (IP, puerto) del cliente |
| 19 | b | setup, handle, finish |
| 20 | b | Template method |
| 21 | b | Rechazar antes de crear el handler |
| 22 | b | El servidor no se cae |
| 23 | b | Verificado: `finish()` corre igual |
| 24 | b | Una sola vez, al construir |
| 25 | b | Evitar la explosión combinatoria de clases |
| 26 | b | `process_request()`, uno solo |
| 27 | b | Solo la combinación, sin cuerpo |
| 28 | b | Bug silencioso: no falla, no concurre |
| 29 | b | El MRO resuelve de izquierda a derecha |
| 30 | b | Ctrl+C no queda esperando clientes |
| 31 | b | `collect_children()` |
| 32 | b | Es la clase 11 otra vez |
| 33 | b | Los procesos no comparten memoria |
| 34 | c | Para eso está asyncio |
| 35 | b | `http.server` |
| 36 | b | Un selector: la clase 17 ya está adentro |
| 37 | b | Mismos límites que la clase 14 |

</details>

---

## Resultado de la autoevaluación

| Puntaje | Diagnóstico |
|---------|-------------|
| 33-37 correctas | Excelente. Avanzá a la clase 17 (I/O Multiplexing) |
| 27-32 | Buen nivel. Repasá los temas donde fallaste |
| 19-26 | Nivel intermedio. Rehacé el ejercicio 3 (mixins) |
| < 19 | Repasá el contenido completo. Consultá con el docente antes de la próxima clase |

> Las preguntas 16, 17, 28, 32 y 33 son las que más importan en la práctica: son los errores que rompen código real. La 28 en particular es un bug que no da error y te deja un servidor secuencial creyendo que es concurrente.
>
> Si fallaste varias, volvé sobre la progresión del contenido y rehacé los pasos escribiendo el código vos, en vez de leerlo.

---

*Computación II - 2026 - Clase 16*
