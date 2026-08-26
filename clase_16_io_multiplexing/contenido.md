# Clase 16: I/O Multiplexing

## Introducción: esperar por muchos a la vez

La clase 14 terminó con un problema abierto. Vimos cuatro estrategias para atender clientes concurrentes —thread, proceso, pool, `socketserver`— y todas comparten la misma idea: **un recurso del sistema operativo por cada cliente**. Diez mil clientes, diez mil threads.

El problema de fondo es una llamada bloqueante. Cuando hacés `conn.recv(4096)`, tu programa queda detenido hasta que lleguen datos por *esa* conexión. Si querés atender otra al mismo tiempo, necesitás otro hilo de ejecución. De ahí sale todo lo demás.

La pregunta de esta clase es otra: **¿y si en vez de esperar por una conexión, le preguntamos al sistema operativo cuáles de las mil están listas?**

Eso es I/O multiplexing. Un solo hilo, una sola llamada, y el kernel te dice quién tiene datos. Es la idea sobre la que están construidos nginx, Redis, Node.js y —lo que nos importa acá— asyncio.

> **Nota:** los archivos `servidor_select.py`, `servidor_selectors.py`, `chat.py` y `comparar.py` acompañan la clase. El último mide `select`, `poll` y `epoll` con cantidades crecientes de conexiones, y los números explican por qué existe `epoll`.

---

## Antes de empezar: direcciones que vas a escribir en el código

Ustedes ven direccionamiento en detalle en Redes. Acá nos interesa solo lo que hace falta para que un programa funcione: qué escribir en un `bind()`, qué significa lo que devuelve `getsockname()`, y por qué a veces el servidor no es alcanzable.

### El prefijo, en una línea

Cuando veas `192.168.1.37/24`, el `/24` dice que los primeros 24 bits identifican la red y el resto la máquina. De ahí salen dos cosas que sí importan al programar:

```python
import ipaddress

red = ipaddress.ip_network('192.168.1.0/24')
print(ipaddress.ip_address('192.168.1.37') in red)     # True: sale directo
print(ipaddress.ip_address('192.168.2.10') in red)     # False: va al gateway
```

Si el destino está en tu red, el paquete sale por la placa; si no, va al router. Eso explica el problema clásico de dos contenedores que no se ven: están en redes distintas aunque corran en la misma máquina.

Con Docker lo vas a ver seguido:

```bash
ip -4 addr show docker0
# inet 172.17.0.1/16 brd 172.17.255.255 scope global docker0
```

Docker armó una red `172.17.0.0/16` y cada contenedor recibe una dirección de ahí. Por eso se ven entre sí sin configurar nada. En el TP2 vas a leer exactamente esto.

> **Usá `ipaddress`**, no parsees strings ni calcules máscaras a mano. La biblioteca resuelve IPv4 e IPv6 con la misma API.

---

## Una pincelada de IPv6

IPv6 lo tenés completo como material de estudio en `bloque_0_autonomo/ipv6/`, con ejercicios y dos programas para correr. Acá van los tres puntos que te van a morder si los ignorás al programar.

### Las direcciones especiales tienen equivalente

| IPv4 | IPv6 | Significa |
|------|------|-----------|
| `127.0.0.1` | `::1` | Solo esta máquina |
| `0.0.0.0` | `::` | Todas las interfaces |

Los `::` reemplazan a una secuencia de ceros, y solo pueden aparecer **una vez** por dirección (si aparecieran dos, sería ambiguo cuántos ceros representa cada uno).

En una URL van entre corchetes, para no confundir los dos puntos de la dirección con el del puerto: `http://[::1]:8080/`.

### La tupla de dirección tiene cuatro elementos, no dos

Esto rompe código real:

```python
host, puerto = sock.getsockname()      # ValueError con IPv6
```

Un socket IPv6 devuelve `('::1', 8080, 0, 0)` — los dos extras son `flowinfo` y `scope_id`. La forma que funciona con ambas familias:

```python
info = sock.getsockname()
host, puerto = info[0], info[1]
```

Es un bug que no aparece en desarrollo si probás solo con IPv4, y explota el día que alguien se conecta por IPv6.

### No elijas la familia a mano

Lo intuitivo es un `if` que decide entre IPv4 e IPv6. Lo correcto es dejar que el sistema resuelva:

```python
import socket

for familia, tipo, proto, _, direccion in socket.getaddrinfo(
        'ejemplo.com', 80, type=socket.SOCK_STREAM):
    s = socket.socket(familia, tipo, proto)
    try:
        s.connect(direccion)
        break                    # funcionó
    except OSError:
        s.close()                # probar la siguiente
```

`getaddrinfo()` devuelve las dos familias ordenadas por preferencia del sistema, y hay que **probarlas en orden**: tener una dirección IPv6 no garantiza que la ruta funcione. Es la situación de muchas conexiones en Argentina —el ISP da IPv6 pero sin tránsito— y un cliente que no reintenta con IPv4 simplemente falla.

Como cliente, `socket.create_connection()` ya hace todo esto por vos. Es una razón más para usarlo.

### Y para el servidor: dual-stack

Un socket IPv6 puede atender también IPv4, si se lo pedís:

```python
s = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
s.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)   # explícito, siempre
s.bind(('::', 8080))
```

Los clientes IPv4 aparecen con el prefijo `::ffff:` —`::ffff:127.0.0.1` es el mismo cliente que `127.0.0.1`—, así que si filtrás o logueás por IP, normalizalos.

El default de `IPV6_V6ONLY` **varía entre sistemas operativos**: Linux suele traer 0 y Windows 1. Ponelo explícito o tu servidor se va a comportar distinto en la máquina del compañero.

> Todo esto vale igual para lo que sigue: multiplexing funciona sobre cualquiera de las dos familias, porque opera sobre descriptores y no le importa qué protocolo hay debajo.

---

## El problema en concreto

Supongamos que querés atender dos conexiones en un solo hilo. Lo ingenuo:

```python
datos_a = conn_a.recv(4096)      # bloquea acá
datos_b = conn_b.recv(4096)      # nunca llega si A no habla
```

Si el cliente A no manda nada, B queda ignorado aunque esté gritando. El orden lo impone tu código, no la realidad.

La clase 13 mencionó los sockets no bloqueantes como alternativa:

```python
conn_a.setblocking(False)
conn_b.setblocking(False)
while True:
    for conn in (conn_a, conn_b):
        try:
            datos = conn.recv(4096)
        except BlockingIOError:
            pass                  # no había nada, seguimos
```

Esto funciona y nunca se bloquea, pero es **busy-waiting**: el bucle gira a máxima velocidad preguntando "¿y ahora?" millones de veces por segundo. Consume un core entero para no hacer nada.

Lo que falta es poder decirle al kernel: *"dormime hasta que alguno de estos tenga algo"*. Esa llamada existe desde 1983.

---

## select(): el original

```python
import select

listos_lectura, listos_escritura, con_error = select.select(
    lista_para_leer,        # sockets que me interesa leer
    lista_para_escribir,    # sockets donde quiero escribir
    lista_para_errores,     # sockets a vigilar por excepciones
    timeout                 # segundos; None = esperar indefinidamente
)
```

`select()` **bloquea** hasta que al menos uno de los descriptores esté listo, y devuelve tres listas con los que efectivamente lo están. Mientras tanto, tu proceso duerme sin consumir CPU.

Un servidor eco completo, con un solo hilo:

```python
#!/usr/bin/env python3
"""Servidor eco con select(): un hilo, muchos clientes."""
import select
import socket

servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
servidor.bind(('0.0.0.0', 8080))
servidor.listen(128)

# El socket que escucha también se vigila: "listo para leer" significa
# que hay una conexión esperando en accept().
vigilados = [servidor]

while True:
    listos, _, _ = select.select(vigilados, [], [])

    for sock in listos:
        if sock is servidor:
            conn, direccion = servidor.accept()
            conn.setblocking(False)
            vigilados.append(conn)
            print(f'Nuevo cliente: {direccion}')
        else:
            datos = sock.recv(4096)
            if datos:
                sock.sendall(datos)
            else:
                # recv() vacío: el cliente cerró. Sacarlo de la lista.
                vigilados.remove(sock)
                sock.close()
```

Vale la pena detenerse en tres cosas.

**El socket que escucha se vigila igual que los demás.** Que esté "listo para leer" significa que hay una conexión pendiente y que `accept()` no va a bloquear. Es el mismo concepto de disponibilidad aplicado a algo que no son datos.

**No hay threads ni procesos.** Este servidor atiende a cien clientes con un solo hilo de ejecución. No hay locks, no hay race conditions, no hay `fork()` ni zombies. Toda la complejidad de la clase 14 desaparece.

**Hay que sacar los sockets cerrados de la lista.** Si te olvidás, `select()` te va a reportar ese fd como listo para siempre, y vas a leer de un socket muerto en un bucle infinito.

### Listo no significa "hay muchos datos"

Un malentendido peligroso: que `select()` reporte un socket como listo **solo garantiza que la operación no va a bloquear**. Puede haber 1 byte, o puede que el otro lado haya cerrado.

Por eso el `recv()` posterior sigue necesitando todo lo de la clase 13: chequear el `b''`, manejar lecturas parciales, hacer el framing. Multiplexing resuelve *cuándo* leer, no *cómo*.

### El límite de select(): FD_SETSIZE

`select()` tiene un defecto que viene de 1983 y no se puede arreglar: usa un mapa de bits de tamaño fijo, con capacidad para 1024 descriptores.

Y el detalle importante es cuál es exactamente el límite:

```python
import select, socket
relleno = [socket.socket() for _ in range(1100)]
alto = relleno[-1]
print(alto.fileno())              # 1102
select.select([alto], [], [], 0)  # ValueError: filedescriptor out of range
```

**Un solo socket** rompe `select()`, porque lo que importa no es cuántos descriptores le pasás sino **el número** de cada uno. Si tu proceso abrió muchos archivos antes, un fd con número mayor a 1023 hace fallar la llamada aunque estés vigilando uno solo.

Es un error confuso de diagnosticar: tu servidor anda perfecto en desarrollo y explota en producción cuando hay suficientes archivos abiertos.

### El otro problema: O(n)

Cada llamada a `select()` recibe la lista completa de descriptores, la copia a espacio de kernel, la recorre entera, y devuelve el resultado. Tu código después **también** recorre todo para ver quién quedó listo.

Con 10 conexiones no importa. Con 10.000 de las cuales 3 tienen datos, estás recorriendo 10.000 elementos para encontrar 3, en cada vuelta del bucle. Ese es el corazón del problema C10K.

---

## poll(): sin el límite de 1024

`poll()` llegó en System V y arregla el límite de tamaño usando un array en vez de un mapa de bits:

```python
import select

poller = select.poll()
poller.register(servidor, select.POLLIN)      # POLLIN = listo para leer

while True:
    eventos = poller.poll()          # devuelve [(fd, mascara), ...]
    for fd, mascara in eventos:
        ...
```

Los mismos 1100 sockets que hacían fallar a `select()` funcionan sin problema:

```
select() con fd 1102: ValueError
poll()   con fd 1102: OK
```

Hay una diferencia incómoda en la API: `poll()` trabaja con **números** de descriptor, no con objetos socket. Como necesitás recuperar el socket a partir del número, hay que mantener un diccionario:

```python
conexiones = {}                       # fd -> socket

conn, direccion = servidor.accept()
conexiones[conn.fileno()] = conn
poller.register(conn, select.POLLIN)

# Y al recibir un evento:
sock = conexiones[fd]
```

Las banderas principales:

| Bandera | Significa |
|---------|-----------|
| `POLLIN` | Hay datos para leer (o conexión pendiente) |
| `POLLOUT` | Se puede escribir sin bloquear |
| `POLLHUP` | El otro extremo cerró |
| `POLLERR` | Ocurrió un error |

`POLLHUP` y `POLLERR` llegan aunque no los registres.

**Lo que `poll()` no arregla es el O(n).** Sigue pasando y recorriendo la lista completa en cada llamada.

---

## epoll(): el que resolvió C10K

`epoll` es específico de Linux (2002) y cambia el modelo: en vez de pasar la lista completa cada vez, **el kernel mantiene el conjunto** y vos solo lo modificás cuando algo cambia.

```python
import select

epoll = select.epoll()
epoll.register(servidor.fileno(), select.EPOLLIN)

while True:
    eventos = epoll.poll()           # devuelve SOLO los listos
    for fd, evento in eventos:
        ...
```

La diferencia de fondo es que `epoll.poll()` devuelve únicamente los descriptores listos. Con 10.000 conexiones de las cuales 3 tienen datos, devuelve 3 elementos —no 10.000 que hay que filtrar.

| | Pasar la lista | Recorrer | Límite |
|---|---|---|---|
| `select` | cada llamada | O(n) | 1024 (valor del fd) |
| `poll` | cada llamada | O(n) | ninguno |
| `epoll` | una vez, al registrar | O(eventos listos) | ninguno |

Ese salto de O(n) a O(listos) es lo que hizo posible atender diez mil conexiones, y por eso todos los servidores modernos de Linux lo usan por dentro.

Los equivalentes en otros sistemas: **kqueue** en BSD y macOS, **IOCP** en Windows. La idea es la misma; las APIs, incompatibles entre sí.

---

## selectors: la forma correcta en Python

Escribir código directamente contra `epoll` te ata a Linux. La stdlib resuelve esto con el módulo `selectors`, que elige la mejor implementación disponible en cada sistema:

```python
import selectors

sel = selectors.DefaultSelector()
print(type(sel).__name__)        # EpollSelector en Linux, KqueueSelector en macOS
```

La API es más cómoda porque permite **asociar datos a cada socket** —típicamente la función que lo maneja—, lo que elimina el diccionario manual de `poll()`:

```python
#!/usr/bin/env python3
"""Servidor eco con selectors: portable y sin diccionarios a mano."""
import selectors
import socket

sel = selectors.DefaultSelector()

def aceptar(servidor):
    conn, direccion = servidor.accept()
    conn.setblocking(False)
    # El tercer argumento es dato libre: acá, quién atiende este socket
    sel.register(conn, selectors.EVENT_READ, atender)
    print(f'Nuevo cliente: {direccion}')

def atender(conn):
    datos = conn.recv(4096)
    if datos:
        conn.sendall(datos)
    else:
        sel.unregister(conn)         # antes de cerrar, siempre
        conn.close()

servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
servidor.bind(('0.0.0.0', 8080))
servidor.listen(128)
servidor.setblocking(False)
sel.register(servidor, selectors.EVENT_READ, aceptar)

while True:
    for clave, _mascara in sel.select():
        callback = clave.data            # la función que guardamos
        callback(clave.fileobj)          # el socket
```

Ese `callback(clave.fileobj)` del final es el patrón que conviene mirar con atención: **el bucle no sabe qué hace cada socket**, solo despacha al handler que se registró con él.

Eso tiene nombre —*event loop*— y es, en esencia, lo que hace asyncio por dentro. Cuando en la clase 18 veamos corrutinas, el bucle va a ser reconociblemente este, con `await` en lugar de callbacks.

**`unregister()` antes de `close()`.** Si cerrás un socket sin desregistrarlo, el selector queda con un fd muerto y el comportamiento es indefinido: puede tirar excepción o reportar eventos fantasma. Es el error más común con esta API.

---

## Escribir sin bloquear

Hasta acá vigilamos lecturas. La escritura también puede bloquear: si el buffer de envío del kernel está lleno —lo que vimos en las manijas de la clase 13, cuando `send()` de 10 MB mandaba solo 2,6— un `sendall()` bloqueante detiene todo el servidor.

Con multiplexing eso es inaceptable: **un solo cliente lento congelaría a los mil restantes**.

La solución es mantener un buffer de salida por conexión y registrar interés en escritura solo cuando hay algo pendiente:

```python
pendiente = {}          # socket -> bytes que faltan enviar

def atender(conn):
    datos = conn.recv(4096)
    if not datos:
        sel.unregister(conn); conn.close(); pendiente.pop(conn, None)
        return
    pendiente[conn] = pendiente.get(conn, b'') + datos
    # Ahora me interesa saber cuándo puedo escribir
    sel.modify(conn, selectors.EVENT_READ | selectors.EVENT_WRITE, atender)

def escribir(conn):
    buf = pendiente.get(conn, b'')
    if buf:
        n = conn.send(buf)              # send(), no sendall()
        pendiente[conn] = buf[n:]
    if not pendiente.get(conn):
        # Ya no queda nada: dejar de vigilar escritura
        sel.modify(conn, selectors.EVENT_READ, atender)
```

Fijate que acá **sí se usa `send()` y no `sendall()`**, al revés de lo que dijimos en la clase 13. La razón es que `sendall()` insiste hasta terminar, y eso es exactamente lo que no queremos: preferimos mandar lo que entre ahora y volver después, cuando el selector avise que se puede escribir de nuevo.

Registrar `EVENT_WRITE` permanentemente es un error clásico: un socket casi siempre está listo para escribir, así que el bucle giraría sin parar. Hay que activarlo solo cuando hay datos pendientes.

---

## El costo: todo tiene que ser rápido

Multiplexing tiene una contrapartida seria. Como hay **un solo hilo**, cualquier operación lenta detiene a todos los clientes.

```python
def atender(conn):
    datos = conn.recv(4096)
    resultado = calculo_pesado(datos)      # 2 segundos de CPU
    conn.sendall(resultado)
```

Durante esos 2 segundos el servidor no acepta conexiones, no lee de nadie, no responde. Con threads esto no pasaba: el scheduler del sistema operativo repartía el tiempo por vos.

Lo mismo con cualquier llamada bloqueante escondida: una consulta a base de datos, un `open()` sobre un archivo en red, un `socket.gethostbyname()` que espera al DNS. Todas congelan el bucle.

Esta es la **regla de oro del modelo de event loop**: nada que tarde puede correr en el hilo del bucle. El trabajo pesado va a un pool de threads o procesos, y el resultado vuelve al bucle.

Es exactamente el mismo problema que van a tener con asyncio, y la razón por la que existe `run_in_executor`. Vale la pena entenderlo acá, donde el mecanismo está a la vista.

---

## Cuándo usar cada cosa

| Situación | Herramienta |
|-----------|-------------|
| Pocas conexiones, lógica compleja por cliente | Threads (clase 14) |
| Trabajo CPU-bound por conexión | Procesos o pool (clase 14) |
| Miles de conexiones, trabajo liviano | Multiplexing |
| Miles de conexiones, código legible | asyncio (clases 18-20) |
| Código portable | `selectors`, nunca `epoll` directo |

En la práctica, hoy nadie escribe un servidor nuevo con `selectors` a mano: se usa asyncio, que hace esto por debajo con mejor sintaxis. Pero conocer el mecanismo es lo que evita tratar a asyncio como magia, y es lo que te permite diagnosticar cuando algo se comporta raro.

---

## Conceptos clave

1. **El problema es bloquearse en una sola conexión**: multiplexing pregunta por muchas a la vez.
2. **`select()` bloquea hasta que alguno esté listo**: sin busy-waiting, sin consumir CPU.
3. **Listo significa "no va a bloquear"**, no "hay muchos datos": el `recv()` posterior sigue necesitando todos los cuidados de la clase 13.
4. **El límite de `select()` es el número del fd, no la cantidad**: un solo fd mayor a 1023 rompe la llamada.
5. **`poll()` saca el límite pero sigue siendo O(n)**: pasa y recorre la lista completa cada vez.
6. **`epoll` cambia el modelo**: el kernel mantiene el conjunto y devuelve solo los listos. Ese salto resolvió C10K.
7. **Usá `selectors`, no `epoll` directo**: elige la mejor implementación de cada sistema.
8. **`unregister()` antes de `close()`**: un fd cerrado y aún registrado deja el selector en estado indefinido.
9. **Registrar `EVENT_WRITE` permanente hace girar el bucle**: activarlo solo con datos pendientes.
10. **Un solo hilo: nada lento puede correr en el bucle**: es la misma regla que va a valer en asyncio.

---

## Preparación para la próxima clase

En la **clase 17 (HTTP + FastAPI)** subimos de capa. Hasta acá programamos el transporte; ahora vamos a ver el protocolo de aplicación que corre encima y que sostiene toda la web. Vamos a leer HTTP a mano —como hicimos con `nc` en la clase 12— y después a construir una API con FastAPI.

Es también la clase donde se entrega el **enunciado del TP2**.

Para llegar preparado:

- Corré `comparar.py` y guardá los números: los vamos a usar como argumento cuando lleguemos a asyncio.
- Asegurate de entender por qué el bucle de `selectors` es un event loop.

---

## Referencias

- [The C10K problem](http://www.kegel.com/c10k.html) - el texto de Dan Kegel (1999) que planteó el problema
- [`selectors` — documentación de Python](https://docs.python.org/3/library/selectors.html)
- [`select` — documentación de Python](https://docs.python.org/3/library/select.html)
- [select(2)](https://man7.org/linux/man-pages/man2/select.2.html) y [epoll(7)](https://man7.org/linux/man-pages/man7/epoll.7.html) - las man pages
- Stevens, *UNIX Network Programming, Vol. 1* - capítulo 6, el tratamiento clásico

---

*Computación II - 2026 - Clase 16*
