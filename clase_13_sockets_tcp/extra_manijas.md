# Clase 13: Sockets TCP - Extra Manijas

Material opcional para profundizar.

---

## Qué pasa realmente en un send()

`sendall()` no manda nada a la red. Copia tus bytes al **buffer de envío del kernel** y vuelve. Después, el kernel decide cuándo transmitirlos, según la ventana de congestión, el algoritmo de Nagle y el estado del receptor.

De ahí se siguen dos cosas incómodas:

**Que `sendall()` haya vuelto no significa que el otro lado recibió nada.** Solo significa que el kernel se hizo cargo. Si querés confirmación, tiene que dártela la aplicación del otro lado, con un ACK propio a nivel de protocolo. Los ACK de TCP confirman recepción en el kernel remoto, no procesamiento por la aplicación.

**`send()` devuelve menos cuando el buffer se llena.** Es lo que viste en el ejercicio: mandar 10 MB de una llena el buffer (unos pocos MB) y el resto queda sin enviar.

Podés inspeccionar y ajustar los buffers:

```python
import socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
print(s.getsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF))   # bytes
print(s.getsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF))
```

```bash
cat /proc/sys/net/ipv4/tcp_wmem      # mínimo, default, máximo
```

Linux ajusta estos buffers dinámicamente. Tocarlos a mano rara vez mejora las cosas y suele empeorarlas.

---

## El deadlock de los buffers llenos

Un error de diseño clásico, y difícil de diagnosticar porque no hay excepción: los dos procesos simplemente se quedan quietos.

Dos programas se mandan mucho dato entre sí, y ambos escriben todo antes de leer:

```python
# Los dos lados hacen esto, simultáneamente
s.sendall(datos_enormes)      # 100 MB
respuesta = s.recv(4096)
```

La secuencia:

1. A llena el buffer de envío propio y el de recepción de B. `sendall()` bloquea.
2. B hace lo mismo en sentido contrario y también bloquea.
3. Ninguno llega nunca a su `recv()`, así que los buffers no se vacían.
4. Deadlock permanente.

Es el mismo problema de dependencia circular que vimos con locks en la clase 11, con buffers en lugar de mutexes. Las soluciones también se parecen: imponer un orden estricto (protocolo de petición/respuesta donde uno habla y el otro escucha), usar threads separados para lectura y escritura, o multiplexar con `select()` (clase 17).

Es una de las razones por las que los protocolos reales tienen turnos definidos y no dejan que ambos lados hablen a la vez sin control.

---

## Sockets no bloqueantes

Todo lo de la clase usó sockets bloqueantes: `recv()` espera, `accept()` espera. Existe el modo contrario:

```python
s.setblocking(False)
try:
    datos = s.recv(4096)
except BlockingIOError:
    pass          # no había nada listo; seguir con otra cosa
```

En vez de esperar, la llamada falla inmediatamente con `BlockingIOError` (`EAGAIN`/`EWOULDBLOCK` en C) si no hay datos.

Por sí solo esto es poco útil: preguntar en un bucle cerrado "¿hay algo?" quema CPU. Se vuelve potente combinado con `select()`, `poll()` o `epoll()`, que permiten preguntar por muchos sockets a la vez y dormir hasta que alguno esté listo. Eso es la clase 17, y es la base sobre la que está construido asyncio.

`settimeout()` es en realidad un modo intermedio: bloquea, pero con límite.

| Modo | Comportamiento |
|------|----------------|
| `setblocking(True)` (default) | Espera indefinidamente |
| `settimeout(n)` | Espera hasta n segundos |
| `setblocking(False)` | No espera; falla si no hay nada |

---

## El estado de la conexión visto desde adentro

Los sockets exponen bastante información:

```python
conn.getsockname()      # (IP, puerto) de este lado
conn.getpeername()      # (IP, puerto) del otro lado
```

Los cuatro valores de la cuádrupla, disponibles desde el código.

Se puede consultar el estado interno de TCP en Linux:

```python
import socket, struct

info = conn.getsockopt(socket.IPPROTO_TCP, socket.TCP_INFO, 104)
estado = info[0]      # 1 = ESTABLISHED, 8 = CLOSE_WAIT, etc.
```

`TCP_INFO` devuelve una estructura con RTT medido, retransmisiones, tamaño de ventana y más. Es específico de Linux y de bajo nivel, pero es lo que usan las herramientas de monitoreo para saber cómo va una conexión.

Más práctico desde la terminal:

```bash
ss -tin      # -i agrega info interna de TCP: rtt, cwnd, retransmisiones
```

---

## Detectar conexiones muertas

Un problema serio: si el cable se corta o la máquina remota se apaga de golpe, **no llega ningún FIN**. Tu socket queda `ESTABLISHED` para siempre, esperando datos que no van a llegar.

Peor: TCP no manda nada en una conexión ociosa, así que ni te enterás.

Hay dos enfoques.

### TCP keepalive

El kernel manda sondas periódicas:

```python
s.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
s.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, 60)    # tras 60s ocioso
s.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, 10)   # sondear cada 10s
s.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPCNT, 3)      # 3 fallos = muerta
```

Los valores por defecto de Linux son inútiles para casi todo: la primera sonda va a las **dos horas**.

```bash
cat /proc/sys/net/ipv4/tcp_keepalive_time    # 7200 segundos
```

### Heartbeat de aplicación

La alternativa es que el protocolo tenga sus propios mensajes de "seguís ahí". Es más código, pero funciona igual en todas las plataformas, no depende de opciones del kernel, y detecta un caso que keepalive no ve: **el proceso remoto vivo pero colgado**. Keepalive lo responde el kernel, así que una aplicación en deadlock sigue pareciendo sana.

WebSocket, MQTT y casi todos los protocolos de larga duración tienen ping/pong propio por esta razón.

---

## sendfile: copiar sin pasar por tu proceso

Para mandar un archivo, lo obvio es leerlo y escribirlo al socket:

```python
with open('archivo.bin', 'rb') as f:
    while (pedazo := f.read(65536)):
        s.sendall(pedazo)
```

Eso copia los datos del kernel a tu proceso y de vuelta al kernel. Para archivos grandes es desperdicio puro.

Linux ofrece `sendfile()`, que copia directamente dentro del kernel:

```python
with open('archivo.bin', 'rb') as f:
    s.sendfile(f)
```

Es la técnica *zero-copy*, y es parte de por qué nginx sirve archivos estáticos tan rápido. Python la expone directo en `socket.sendfile()`.

---

## AF_UNIX: la misma API sin red

Como vimos de pasada en la clase 12, la misma API sirve para comunicación local:

```python
import socket, os

RUTA = '/tmp/mi_servicio.sock'
if os.path.exists(RUTA):
    os.unlink(RUTA)          # los sockets Unix persisten como archivo

with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as srv:
    srv.bind(RUTA)
    srv.listen(5)
    conn, _ = srv.accept()   # no hay dirección de cliente que mostrar
    with conn:
        conn.sendall(conn.recv(4096))
```

Las diferencias con TCP:

- La dirección es una ruta, no (IP, puerto)
- Hay que borrar el archivo antes de hacer `bind()` si quedó de una ejecución anterior
- No hay handshake ni checksums: es más rápido
- Los permisos del filesystem controlan el acceso
- `accept()` devuelve una dirección vacía

Y dos capacidades que TCP no tiene:

**`SO_PEERCRED`** permite saber qué proceso está del otro lado:

```python
import struct
cred = conn.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, struct.calcsize('3i'))
pid, uid, gid = struct.unpack('3i', cred)
```

Autenticación gratis y confiable, garantizada por el kernel. Es como systemd y Docker verifican quién les habla.

**`SCM_RIGHTS`** permite pasar descriptores de archivo abiertos entre procesos. No el número —que no significaría nada en otro proceso— sino el descriptor real. Un proceso puede abrir un archivo o aceptar una conexión y **entregársela** a otro. Los servidores con reinicio sin caída (*zero-downtime*) hacen exactamente eso: el proceso viejo le pasa el socket que escucha al nuevo.

---

## Cómo se hace de verdad

Todo lo de esta clase es la capa cruda. En producción rara vez se escribe así.

`socketserver`, en la biblioteca estándar, encapsula el bucle de `accept`:

```python
import socketserver

class Handler(socketserver.StreamRequestHandler):
    def handle(self):
        for linea in self.rfile:               # framing por líneas gratis
            self.wfile.write(b'ECHO: ' + linea)

with socketserver.ThreadingTCPServer(('', 8080), Handler) as srv:
    srv.serve_forever()                        # y concurrente, de paso
```

Ese ejemplo resuelve en diez líneas lo que la clase entera construyó a mano, incluida la concurrencia de la clase 14.

¿Por qué entonces hacerlo a mano? Porque cuando `socketserver` (o Flask, o gRPC) se comporta raro, la única forma de entender qué pasa es saber qué hay abajo. Los bugs de red se diagnostican en la capa cruda aunque el código de producción viva varias capas más arriba.

En orden de abstracción creciente: `socket` → `socketserver` → `asyncio` (clase 19+) → frameworks como FastAPI (clase 18).

---

## Lecturas

- [Beej's Guide to Network Programming](https://beej.us/guide/bgnet/) - el mejor tutorial de sockets; en C, pero la API es la misma
- [Socket Programming HOWTO](https://docs.python.org/3/howto/sockets.html) - guía oficial, con buenos consejos sobre framing
- Stevens, *UNIX Network Programming, Vol. 1* - la referencia canónica, capítulos 3 a 6
- [The C10K problem](http://www.kegel.com/c10k.html) - el texto de 1999 sobre servir 10.000 conexiones simultáneas; explica por qué existe `epoll` y, en última instancia, asyncio
- [`socketserver`](https://docs.python.org/3/library/socketserver.html) - lo que usarías en vez de escribir el bucle a mano

---

*Computación II - 2026 - Clase 13*
