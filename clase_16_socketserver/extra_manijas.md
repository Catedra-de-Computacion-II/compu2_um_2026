# Clase 16: socketserver - Extra Manijas

Material opcional para profundizar.

---

## Leer el código fuente

`socketserver.py` son unas 800 líneas y es de lo más legible de la biblioteca estándar. Vale la pena abrirlo:

```python
import socketserver, inspect
print(inspect.getsourcefile(socketserver))
print(inspect.getsource(socketserver.ThreadingMixIn))
```

`ThreadingMixIn` completo son unas 30 líneas, y lo esencial es este método:

```python
def process_request(self, request, client_address):
    t = threading.Thread(target=self.process_request_thread,
                         args=(request, client_address))
    t.daemon = self.daemon_threads
    ...
    t.start()
```

Eso es todo lo que hace falta para convertir un servidor secuencial en concurrente: reemplazar un método. Es una demostración concreta de por qué conviene que las clases tengan métodos chicos y bien separados — si `TCPServer` hiciera el `accept` y el manejo del cliente en una sola función gigante, no habría dónde enganchar el mixin.

La lección es transferible: cuando diseñes una clase pensada para extenderse, el punto de extensión tiene que ser **un método identificable**, no un fragmento en el medio de otro.

---

## El MRO en detalle

El bug del orden invertido merece entenderse bien, porque el mecanismo aparece en cualquier jerarquía con herencia múltiple.

```python
class Correcto(ThreadingMixIn, TCPServer): pass
class AlReves(TCPServer, ThreadingMixIn): pass
```

Python calcula el **MRO** (Method Resolution Order) con el algoritmo C3, que linealiza el grafo de herencia:

```
Correcto: Correcto -> ThreadingMixIn -> TCPServer -> BaseServer -> object
AlReves:  AlReves  -> TCPServer -> BaseServer -> ThreadingMixIn -> object
```

Al buscar `process_request`, Python recorre esa lista y se queda con el primero que lo define. En `Correcto` gana el mixin; en `AlReves`, `BaseServer` —que lo define como "atender en este mismo hilo"— aparece **antes** que el mixin.

Podés verlo:

```python
for C in (Correcto, AlReves):
    duenio = next(k.__name__ for k in C.__mro__ if 'process_request' in k.__dict__)
    print(C.__name__, '->', duenio)
```

```
Correcto -> ThreadingMixIn
AlReves  -> BaseServer
```

De ahí la convención universal: **los mixins van a la izquierda**. Un mixin es un modificador, y para modificar tiene que interceptar antes que la clase base.

Es también la razón por la que los mixins bien escritos llaman a `super()`: para que la cadena siga hacia la clase base en vez de cortarse.

---

## Timeouts

`BaseServer` y los handlers soportan timeouts, aunque no es obvio.

**En el servidor**, `timeout` afecta a `handle_request()` (una sola petición), no a `serve_forever()`:

```python
class Servidor(socketserver.TCPServer):
    timeout = 5

    def handle_timeout(self):
        print('Pasaron 5 segundos sin conexiones')
```

**En el handler**, `timeout` limita cuánto puede tardar el cliente en mandar datos:

```python
class Handler(socketserver.StreamRequestHandler):
    timeout = 30              # el socket del cliente

    def handle(self):
        try:
            datos = self.rfile.readline()
        except TimeoutError:
            self.wfile.write(b'Te tardaste demasiado\n')
```

Sin eso, un cliente que se conecta y no manda nada ocupa un thread para siempre. Es el vector de un ataque clásico —Slowloris— que tumba servidores abriendo cientos de conexiones que envían un byte cada tanto.

---

## Compartir estado entre procesos con ForkingMixIn

Con `ThreadingMixIn` el estado compartido es un atributo del servidor más un `Lock`. Con `ForkingMixIn` eso no funciona: cada handler vive en un proceso distinto.

La solución son las herramientas de la clase 9:

```python
import multiprocessing as mp
import socketserver

class Servidor(socketserver.ForkingTCPServer):
    allow_reuse_address = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Memoria compartida real, no un atributo común
        self.contador = mp.Value('i', 0)

class Handler(socketserver.StreamRequestHandler):
    def handle(self):
        with self.server.contador.get_lock():      # el lock viene incluido
            self.server.contador.value += 1
            n = self.server.contador.value
        self.wfile.write(f'sos el cliente {n}\n'.encode())
```

Fijate el detalle: el `Value` **tiene que crearse antes del fork**, o sea en el `__init__` del servidor. Un `Value` creado dentro del handler ya está en el proceso hijo y no lo ve nadie más.

Es el mismo razonamiento de qué se hereda en un `fork()` que vimos en la clase 4 y volvió con las señales en la clase 14.

---

## http.server: el ejemplo canónico

`http.server` está construido enteramente sobre `socketserver`, y leerlo muestra cómo se usa el framework en serio:

```python
import http.server, socketserver
print(http.server.HTTPServer.__bases__)          # (socketserver.TCPServer,)
print(http.server.ThreadingHTTPServer.__bases__) # (ThreadingMixIn, HTTPServer)
```

`BaseHTTPRequestHandler` hereda de `StreamRequestHandler` y su `handle()` parsea la línea de petición HTTP, lee los headers, y despacha a un método según el verbo: `do_GET`, `do_POST`, etc.

O sea que cuando escribís esto:

```python
class MiHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'hola')
```

estás completando un template method dentro de otro template method: `socketserver` llama a `handle()`, y el `handle()` de HTTP llama a tu `do_GET()`.

Es exactamente el patrón que vas a ver en la clase 17 con FastAPI, aunque la sintaxis sea otra.

Y para servir un directorio, `python3 -m http.server` es literalmente un `ThreadingHTTPServer` con `SimpleHTTPRequestHandler`.

---

## Cuándo el módulo se queda corto

`socketserver` es de los años 90 y tiene limitaciones que conviene conocer antes de elegirlo:

**No hay control de backpressure.** Si los clientes mandan más rápido de lo que procesás, no hay forma limpia de frenarlos: cada handler bloquea en su thread.

**La configuración por herencia envejeció mal.** Para cambiar tres cosas hay que declarar una subclase. Los frameworks modernos usan composición o parámetros.

**No hay soporte de TLS integrado.** Se puede envolver el socket a mano en `server_bind()`, pero es artesanal:

```python
import ssl

class ServidorTLS(socketserver.TCPServer):
    def server_bind(self):
        contexto = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        contexto.load_cert_chain('cert.pem', 'key.pem')
        self.socket = contexto.wrap_socket(self.socket, server_side=True)
        super().server_bind()
```

**El modelo es un thread o proceso por cliente**, con todos los límites que medimos en la clase 14.

Para un servidor interno, una herramienta o un prototipo, nada de eso importa. Para producción con carga real, se usa asyncio o un framework construido sobre él.

---

## Lecturas

- [`socketserver`](https://docs.python.org/3/library/socketserver.html) - la documentación oficial, con ejemplos de los cuatro servidores
- [Código fuente](https://github.com/python/cpython/blob/main/Lib/socketserver.py) - 800 líneas legibles
- [`http.server`](https://docs.python.org/3/library/http.server.html) - el ejemplo canónico de uso
- [Python MRO](https://docs.python.org/3/howto/mro.html) - el algoritmo C3 en detalle
- *Design Patterns* (GoF) - Template Method
- [Slowloris](https://en.wikipedia.org/wiki/Slowloris_(computer_security)) - por qué importan los timeouts en el handler

---

*Computación II - 2026 - Clase 16*
