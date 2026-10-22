# Clase 17: I/O Multiplexing

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

`getaddrinfo()` devuelve las dos familias ordenadas por preferencia del sistema, y hay que **probarlas en orden**: tener una dirección IPv6 no garantiza que la ruta funcione.

Es la situación de muchas conexiones en Argentina, y vale la pena entender por qué. Internet no es una red sino miles de redes independientes interconectadas; ninguna alcanza sola a todas las demás, así que cada una le paga a otra más grande para que le lleve el tráfico hacia el resto. Ese servicio se llama **tránsito**. Un ISP (*Internet Service Provider*, tu proveedor de conexión) puede asignarte una dirección IPv6 y tener IPv6 funcionando dentro de su propia red, pero si no contrató tránsito IPv6 hacia afuera, tus paquetes no salen: tenés dirección, pero es una calle sin salida.

Por eso un cliente que se queda con la primera dirección que le dan y no reintenta con IPv4 simplemente falla.

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

`select()` es una llamada al sistema que existe desde 4.2BSD (1983) —la misma versión que trajo los sockets, en la clase 13— y su idea es simple de enunciar: **le entregás una lista de descriptores y te devuelve cuáles están listos**, durmiendo mientras tanto si ninguno lo está.

En Python vive en el módulo `select`, que expone las llamadas del sistema operativo casi sin envolverlas:

```python
import select
```

### La firma

```python
listos_lectura, listos_escritura, con_error = select.select(rlist, wlist, xlist, timeout)
```

Recibe cuatro argumentos:

| Argumento | Qué es |
|-----------|--------|
| `rlist` | Lista de descriptores donde te interesa **leer** |
| `wlist` | Lista donde querés **escribir** |
| `xlist` | Lista a vigilar por **condiciones excepcionales** (casi siempre `[]`) |
| `timeout` | Segundos a esperar como máximo. `None` = indefinidamente; `0` = no esperar nada |

Los tres primeros son listas, y pueden ir vacías. Si solo te interesa leer —el caso más común— pasás `select.select(mis_sockets, [], [])`.

**Qué acepta en esas listas:** objetos socket, archivos, o directamente el número de descriptor. En rigor, cualquier objeto con un método `fileno()`. Nosotros vamos a pasar sockets.

**Qué es `xlist`:** condiciones raras, no errores comunes. Un socket que falla se reporta como "listo para leer" y el error aparece al hacer `recv()`. En la práctica, `[]`.

### Qué devuelve

Una **tupla de tres listas**, en el mismo orden que los argumentos: los que están listos para leer, los listos para escribir, y los que tienen una condición excepcional.

```python
>>> select.select([sock_a, sock_c], [], [], 0)
([], [], [])                                    # nadie listo todavía
```

```python
>>> # después de que llegaran datos a sock_a
>>> select.select([sock_a, sock_c], [], [], 0)
([<socket.socket fd=3, ...>], [], [])           # sock_a tiene algo
```

Un detalle que hace cómodo el uso: **las listas devueltas contienen los mismos objetos que pasaste**, no copias ni descriptores sueltos. Por eso podés comparar con `is` y usarlos directamente:

```python
listos, _, _ = select.select(vigilados, [], [])
for sock in listos:
    if sock is servidor:          # comparación por identidad
        ...
```

### Qué hace mientras tanto

Acá está lo importante, y es lo que lo distingue del bucle de la sección anterior: **`select()` bloquea**. Tu proceso queda dormido, sin consumir CPU, hasta que ocurra alguna de estas tres cosas:

1. Al menos un descriptor queda listo
2. Vence el `timeout`
3. Llega una señal

Si vence el timeout sin novedades, devuelve las tres listas vacías. Ese caso es útil: permite hacer tareas periódicas —limpiar conexiones muertas, actualizar estadísticas— entre espera y espera.

```python
listos, _, _ = select.select(vigilados, [], [], 1.0)
if not listos:
    print('un segundo sin actividad')     # el timeout venció
```

> **Sobre la escritura:** un socket casi siempre está listo para escribir, porque el buffer del kernel tiene lugar. Si ponés tus sockets en `wlist` permanentemente, `select()` va a devolver enseguida y el bucle va a girar sin parar. La regla es registrar interés en escritura **solo cuando tenés datos pendientes** de enviar, algo que vamos a ver más adelante.

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

Con 10 conexiones no importa. Con 10.000 de las cuales 3 tienen datos, estás recorriendo 10.000 elementos para encontrar 3, en cada vuelta del bucle. Ese es el corazón del problema **C10K**.

> **C10K** viene de *connection 10.000* —diez mil conexiones simultáneas en una sola máquina—, con la misma abreviatura que Y2K. El nombre lo puso Dan Kegel en un texto de 1999 donde señalaba que el hardware de la época ya daba para eso, pero el software no: con un thread o un proceso por cliente, diez mil clientes son diez mil threads. Lo vimos al cerrar la clase 14; esta clase es la respuesta.

---

## poll(): sin el límite de 1024

`poll()` apareció en System V como reemplazo de `select()`, y resuelve el límite de tamaño usando un array de descriptores en vez de un mapa de bits de tamaño fijo.

El cambio de API es más grande de lo que parece: en vez de pasar las listas en cada llamada, se crea un **objeto poller** al que se le registran los descriptores una vez.

```python
import select

poller = select.poll()                        # crear el objeto
poller.register(servidor, select.POLLIN)      # registrar qué me interesa
```

`register()` recibe el descriptor y una **máscara de eventos**: qué te interesa saber de él.

| Bandera | Significa |
|---------|-----------|
| `POLLIN` | Hay datos para leer, o una conexión pendiente |
| `POLLOUT` | Se puede escribir sin bloquear |
| `POLLHUP` | El otro extremo cerró |
| `POLLERR` | Ocurrió un error |

`POLLHUP` y `POLLERR` llegan siempre, los registres o no.

### Qué devuelve poll()

```python
eventos = poller.poll(timeout_en_milisegundos)
```

Devuelve una **lista de tuplas `(fd, máscara)`**, una por cada descriptor con novedades:

```python
>>> poller.poll(0)
[]                    # nadie listo
>>> # después de que llegaran datos
>>> poller.poll(0)
[(3, 1)]              # el descriptor 3, con máscara 1 (POLLIN)
```

Hay dos cosas ahí que conviene mirar de cerca.

**El primer elemento es un entero, no el socket.** A diferencia de `select()`, que te devolvía los mismos objetos que le pasaste, `poll()` trabaja con números de descriptor. Como necesitás recuperar el socket para hacer `recv()`, hay que mantener un diccionario:

```python
conexiones = {}                          # fd -> socket

conn, direccion = servidor.accept()
conexiones[conn.fileno()] = conn         # guardar la correspondencia
poller.register(conn, select.POLLIN)

# Y al recibir un evento:
for fd, mascara in poller.poll():
    sock = conexiones[fd]                # recuperar el socket
```

**El segundo es una máscara de bits**, no un solo evento. Pueden venir varios combinados con OR, y hay que preguntarlos con `&`:

```python
>>> # el cliente mandó datos y después cerró
>>> poller.poll(0)
[(3, 17)]                    # 17 = 0b10001 = POLLIN | POLLHUP

>>> mascara & select.POLLIN     # ¿hay datos?      -> True
>>> mascara & select.POLLHUP    # ¿además cerró?   -> True
```

Ese caso es real y conviene manejarlo bien: el cliente puede haber dejado datos sin leer **y** haber cerrado la conexión. Si solo mirás `POLLHUP` y cerrás, perdés lo último que mandó.

Otro detalle: el `timeout` de `poll()` va en **milisegundos**, no en segundos como el de `select()`. Es una fuente clásica de errores por factor 1000.

### Lo que arregla y lo que no

El límite de `FD_SETSIZE` desaparece. Los mismos 1100 sockets que hacían fallar a `select()` funcionan sin problema:

```
select() con fd 1102: ValueError
poll()   con fd 1102: OK
```

**Pero el costo O(n) sigue igual.** `poll()` recibe la lista completa de descriptores registrados en cada llamada, la copia a espacio de kernel y la recorre entera. Con 10.000 conexiones de las cuales 3 tienen datos, el kernel revisa las 10.000 para encontrar 3, cada vez.

Eso es lo que va a resolver `epoll`.

---

## epoll(): el que resolvió las diez mil conexiones

`epoll` es específico de Linux (2002) y cambia el modelo de fondo: en vez de pasarle la lista completa en cada llamada, **el kernel mantiene el conjunto** y vos solo lo modificás cuando algo cambia.

La API se parece a la de `poll()` —un objeto donde registrás— pero con esa diferencia adentro:

```python
import select

epoll = select.epoll()                              # crear
epoll.register(servidor.fileno(), select.EPOLLIN)   # registrar (una vez)

while True:
    eventos = epoll.poll(timeout_en_segundos)
    for fd, mascara in eventos:
        ...

epoll.close()                                       # liberar (es un fd real)
```

Las banderas son las mismas de `poll()` con otro prefijo: `EPOLLIN`, `EPOLLOUT`, `EPOLLHUP`, `EPOLLERR`. Y el valor numérico coincide —`POLLIN` y `EPOLLIN` valen 1— porque debajo son las mismas constantes del kernel.

El retorno también es igual: una lista de tuplas `(fd, máscara)`, con el descriptor como entero, así que vale el mismo diccionario `fd -> socket` que en `poll()`.

> **Un detalle que muerde:** el `timeout` de `epoll.poll()` va en **segundos** (acepta decimales), mientras que el de `poll.poll()` va en **milisegundos**. La misma espera de 300 ms se escribe `epoll.poll(0.3)` y `poller.poll(300)`. Confundirlos da esperas mil veces más largas o más cortas de lo que pensabas.

Dos cosas más que lo diferencian: `epoll` **es un descriptor de archivo en sí mismo** —por eso hay que cerrarlo, y por eso se lo puede anidar dentro de otro selector—, y acepta tanto el número de descriptor como el objeto socket en `register()`.

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

Eso tiene nombre —*event loop*— y es, en esencia, lo que hace asyncio por dentro. Cuando en la clase 19 veamos corrutinas, el bucle va a ser reconociblemente este, con `await` en lugar de callbacks.

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
3. **Devuelve una tupla de tres listas** (lectura, escritura, excepciones) con los mismos objetos que le pasaste.
4. **Listo significa "no va a bloquear"**, no "hay muchos datos": el `recv()` posterior sigue necesitando todos los cuidados de la clase 13.
5. **El límite de `select()` es el número del fd, no la cantidad**: un solo fd mayor a 1023 rompe la llamada.
6. **`poll()` saca el límite pero sigue siendo O(n)**: pasa y recorre la lista completa cada vez.
7. **`poll()` y `epoll()` devuelven `(fd, máscara)`**: un entero, no el socket, así que hace falta un diccionario `fd -> socket`.
8. **La máscara puede traer varios eventos combinados con OR**: `POLLIN|POLLHUP` significa "hay datos y además cerró"; preguntá con `&`.
9. **Ojo con las unidades del timeout**: `select` y `epoll` usan segundos; `poll` usa milisegundos.
10. **`epoll` cambia el modelo**: el kernel mantiene el conjunto y devuelve solo los listos. Ese salto resolvió C10K.
11. **Usá `selectors`, no `epoll` directo**: elige la mejor implementación de cada sistema.
12. **`unregister()` antes de `close()`**: un fd cerrado y aún registrado deja el selector en estado indefinido.
13. **Registrar `EVENT_WRITE` permanente hace girar el bucle**: activarlo solo con datos pendientes.
14. **Un solo hilo: nada lento puede correr en el bucle**: es la misma regla que va a valer en asyncio.

---

## Preparación para la próxima clase

En la **clase 18 (De yield a asyncio)** seguimos el hilo que acabamos de abrir. El bucle de `selectors` que escribimos hoy *es* un event loop; lo que falta es la otra mitad: las corrutinas, las funciones que pueden pausarse y retomar. Vamos a construirlas desde `yield` hasta llegar a `async`/`await`, y recién ahí asyncio va a parecer inevitable en lugar de mágico.

Después, en la **clase 19 (HTTP + FastAPI)**, subimos de capa: el protocolo de aplicación que corre encima del transporte que venimos programando. Es también la clase donde se entrega el **enunciado del TP2**.

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

*Computación II - 2026 - Clase 17*
