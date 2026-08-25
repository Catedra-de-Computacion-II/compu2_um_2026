# Clase 15: UDP

## Introducción: el protocolo que no promete nada

Las tres clases anteriores fueron sobre TCP: un flujo confiable, ordenado, con conexión. Casi todo el trabajo lo hacía el protocolo, y lo nuestro era acomodarnos a él —delimitar mensajes, cosechar hijos, elegir una estrategia de concurrencia.

UDP es lo contrario. Manda un paquete y se olvida. No hay conexión, no hay confirmación, no hay reintento, no hay orden. Si el datagrama se pierde, se perdió y nadie avisa.

Suena a protocolo defectuoso, pero es la base del DNS, del streaming de video, de los juegos en red y de QUIC —o sea, de HTTP/3. La pregunta interesante no es por qué alguien usaría algo tan poco confiable, sino **qué se gana renunciando a las garantías**.

Esta clase responde eso: cómo se programa UDP, qué cuesta implementar confiabilidad encima cuando hace falta, y qué cosas UDP puede hacer que TCP directamente no.

> **Nota:** los archivos `echo_udp.py`, `confiable.py` y `perdidas.py` acompañan la clase. El tercero simula una red que pierde paquetes, porque en localhost no se pierde nada y sin pérdidas la mitad de esta clase no se entiende.

---

## Un socket sin conexión

El cambio es una constante:

```python
import socket

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)   # antes: SOCK_STREAM
```

`SOCK_DGRAM` en vez de `SOCK_STREAM`. Todo lo demás cambia como consecuencia.

### El servidor: dos pasos en vez de cinco

Comparado con TCP, desaparece la mitad de la ceremonia:

```python
#!/usr/bin/env python3
"""Servidor eco UDP."""
import socket

with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(('0.0.0.0', 8080))
    print('Escuchando en 0.0.0.0:8080')

    while True:
        datos, origen = s.recvfrom(4096)
        print(f'{origen}: {datos!r}')
        s.sendto(datos, origen)              # eco al remitente
```

No hay `listen()`. No hay `accept()`. **No hay un socket por cliente**: el mismo socket atiende a todo el mundo.

La razón es que no hay nada que aceptar. En TCP, `accept()` devolvía un socket nuevo porque cada conexión era una entidad con estado propio —la cuádrupla de la clase 12, los buffers, los números de secuencia. En UDP no hay conexión: hay datagramas sueltos que llegan, cada uno con la dirección de quien lo mandó.

Por eso `recvfrom()` devuelve **dos** cosas: los datos y el origen. Sin ese origen no sabrías a quién responderle.

### El cliente: ni siquiera hace falta bind

```python
#!/usr/bin/env python3
"""Cliente eco UDP."""
import socket

with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
    s.settimeout(2.0)
    s.sendto(b'hola', ('localhost', 8080))
    respuesta, origen = s.recvfrom(4096)
    print(f'Recibido de {origen}: {respuesta!r}')
```

No hay `connect()`, y no hace falta: `sendto()` lleva la dirección de destino en cada llamada.

El sistema operativo le asigna un puerto efímero automáticamente en el primer `sendto()`, igual que con TCP. Podés verlo:

```python
s.sendto(b'x', ('localhost', 8080))
print(s.getsockname())          # ('0.0.0.0', 54321) — puerto asignado ahora
```

### El `settimeout()` no es opcional

En TCP, un `recv()` sin timeout se cuelga si el otro lado no responde, pero al menos si el otro lado *cierra*, `recv()` devuelve `b''` y te enterás.

En UDP no hay cierre que detectar. Si el servidor no está, tu `recvfrom()` espera **para siempre** una respuesta que nunca va a llegar. No hay error, no hay señal, no hay nada.

Por eso todo cliente UDP necesita timeout. Es la diferencia entre un programa que reintenta y uno que se cuelga.

---

## connect() en UDP: existe y no hace lo que parece

Hay una función que confunde a todo el mundo:

```python
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.connect(('localhost', 8080))     # ¿pero no era sin conexión?
s.send(b'hola')                    # y ahora send(), no sendto()
datos = s.recv(4096)               # y recv(), no recvfrom()
```

Esto funciona, pero **no establece ninguna conexión**: no se manda un solo paquete, no hay handshake, el otro lado ni se entera.

Lo que hace es fijar una dirección por defecto en el socket local. A partir de ahí:

- Podés usar `send()`/`recv()` sin repetir la dirección
- El kernel **descarta** los datagramas que vengan de cualquier otra dirección
- Empezás a recibir errores ICMP, como *port unreachable*

Ese último punto es el más útil y el menos conocido:

```python
import socket
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.connect(('localhost', 9999))     # puerto donde no hay nadie
s.send(b'hola')
try:
    s.recv(4096)
except ConnectionRefusedError:
    print('El destino avisó que no hay nadie en ese puerto')
```

Con un socket UDP no conectado, ese mismo escenario te deja esperando indefinidamente. Con `connect()`, el ICMP llega hasta tu programa como excepción.

> **Cuidado**: esto funciona en localhost y en redes locales, pero muchos firewalls filtran ICMP en Internet. No construyas tu protocolo asumiendo que el error va a llegar.

---

## Los límites de mensaje se preservan (y eso trae otro problema)

Esta es la ventaja concreta de UDP sobre TCP, y ya la vimos en la clase 12: un `sendto()` es un `recvfrom()`. No hay framing que implementar.

```python
# Cliente
for msg in [b'HOLA', b'COMO', b'ESTAS']:
    s.sendto(msg, destino)

# Servidor: tres recvfrom(), uno por mensaje. Siempre.
```

Comparalo con lo que tuvimos que hacer en la clase 13 —buffer, delimitador o prefijo de longitud— y se entiende por qué DNS eligió UDP.

Pero aparece un problema nuevo: **si el buffer que le pasás a `recvfrom()` es más chico que el datagrama, el resto se pierde**.

```python
datos, origen = s.recvfrom(10)     # llegó un datagrama de 100 bytes
# datos tiene 10 bytes. Los otros 90 se DESCARTAN, no quedan para la próxima.
```

En TCP eso no pasaba: lo que no leías quedaba en el buffer del kernel esperando. En UDP el datagrama se consume entero, y lo que no entró se tira silenciosamente.

La regla práctica: pasar siempre un buffer más grande que el datagrama más grande de tu protocolo. `65535` es el máximo teórico y siempre alcanza:

```python
datos, origen = s.recvfrom(65535)
```

---

## Cuánto se puede mandar de una

Un datagrama UDP puede tener hasta 65507 bytes de payload, pero **poder no es conveniente**.

El límite práctico es el MTU, que vimos en las manijas de la clase 12: típicamente 1500 bytes en Ethernet, menos los encabezados IP (20) y UDP (8), quedan **1472 bytes** que viajan sin fragmentar.

Si mandás más, IP fragmenta el datagrama en varios paquetes. Y acá está el problema: **si se pierde un solo fragmento, se pierde el datagrama entero**. Con 10 fragmentos y 1% de pérdida por paquete, la probabilidad de que el datagrama llegue completo baja a ~90%.

Por eso los protocolos UDP serios se mantienen por debajo del MTU. DNS usa 512 bytes por defecto justamente por esto, y cuando la respuesta no entra, marca el flag TC y el cliente reintenta por TCP.

Verificá el MTU de tu máquina:

```bash
ip link show | grep mtu
```

---

## Implementar confiabilidad encima

Si necesitás garantías, hay que construirlas. Esto es lo que TCP te daba gratis y ahora tenés que escribir vos.

### Retransmisión con timeout

Lo mínimo: mandar, esperar respuesta, reintentar si no llega.

```python
def pedir_con_reintentos(sock, mensaje, destino, intentos=3, timeout=1.0):
    """Manda un mensaje y espera respuesta, reintentando si se pierde."""
    sock.settimeout(timeout)
    for intento in range(1, intentos + 1):
        sock.sendto(mensaje, destino)
        try:
            respuesta, _ = sock.recvfrom(65535)
            return respuesta
        except TimeoutError:
            print(f'Intento {intento}: sin respuesta, reintento')
    return None
```

Funciona, pero tiene dos problemas que no son obvios.

**El timeout fijo es una mala apuesta.** Un segundo es mucho en una red local y poco en una conexión satelital. TCP mide el RTT y ajusta dinámicamente; acá estás adivinando.

**No distinguís qué se perdió.** Si no llega respuesta, puede haberse perdido tu pedido o la respuesta del servidor. En el segundo caso, el servidor ya procesó tu pedido y al reintentar **lo procesa dos veces**. Si el pedido era "transferí $100", el problema es serio.

### Números de secuencia

La solución a lo segundo es numerar los mensajes, de modo que el receptor pueda descartar duplicados y el emisor saber qué respuesta corresponde a qué pedido:

```python
import struct

def enviar_numerado(sock, seq, payload, destino):
    """Prefija el número de secuencia al payload."""
    sock.sendto(struct.pack('!I', seq) + payload, destino)

def recibir_numerado(sock):
    datos, origen = sock.recvfrom(65535)
    (seq,) = struct.unpack('!I', datos[:4])
    return seq, datos[4:], origen
```

Del lado del servidor, guardar los `seq` ya vistos por cliente y descartar repetidos. Del lado del cliente, ignorar respuestas cuyo `seq` no coincida con el pedido en curso —porque una respuesta demorada de un intento anterior puede llegar tarde y confundirte.

Fijate que `struct.pack('!I', ...)` con el `!` de orden de red es lo mismo que usamos para el framing por longitud en la clase 13. Acá no delimita: numera.

### Hasta dónde llegar

Si seguís por este camino —agregás ventana deslizante, control de flujo, control de congestión— vas a terminar reimplementando TCP, casi seguro peor.

La pregunta correcta no es "¿puedo hacer UDP confiable?" sino **"¿qué garantías necesito realmente?"**. Muchos protocolos necesitan solo una parte:

- **DNS**: reintento simple, sin orden ni control de flujo. Una consulta, una respuesta.
- **Streaming de video**: ni siquiera reintenta. Un frame que llega tarde es basura; mejor perderlo y seguir.
- **Juegos en red**: mandan el estado completo cada tick. Si un paquete se pierde, el siguiente ya trae la información actualizada.
- **QUIC (HTTP/3)**: sí implementa confiabilidad completa sobre UDP, para poder cambiar cosas que en TCP están congeladas en el kernel. Son años de trabajo de gente muy especializada.

El patrón del videojuego es el más instructivo: en vez de garantizar que todo llegue, diseñaron el protocolo para que **perder un mensaje no importe**. Eso suele ser mejor idea que reimplementar TCP.

---

## Lo que UDP puede hacer y TCP no

### Broadcast: hablarle a toda la red local

```python
import socket

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)    # hay que pedirlo
s.sendto(b'DISCOVER?', ('255.255.255.255', 8080))
```

Un solo datagrama que llega a todas las máquinas de la red local. TCP no puede hacer esto: una conexión es punto a punto por definición.

Es el mecanismo de descubrimiento de servicios: DHCP lo usa para encontrar un servidor cuando la máquina todavía no tiene IP, y las impresoras de red se anuncian así.

El `SO_BROADCAST` es obligatorio y existe para que no lo hagas sin querer. Los routers no reenvían broadcast, así que no sale de tu red local.

### Multicast: hablarle a un grupo

Broadcast molesta a todas las máquinas, incluso a las que no les interesa. Multicast le habla solo a quienes se suscribieron:

```python
import socket
import struct

GRUPO = '224.0.0.251'
PUERTO = 5353

# Receptor: unirse al grupo
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(('', PUERTO))
mreq = struct.pack('4sl', socket.inet_aton(GRUPO), socket.INADDR_ANY)
s.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

datos, origen = s.recvfrom(65535)
```

Las direcciones `224.0.0.0` a `239.255.255.255` están reservadas para multicast. La del ejemplo, `224.0.0.251`, es la de mDNS —el protocolo detrás de los `.local` y del descubrimiento de dispositivos en tu red.

Emitir es más simple: mandar al grupo y listo.

```python
s.sendto(b'anuncio', (GRUPO, PUERTO))
```

Un emisor, N receptores, un solo paquete en la red. Es la base del streaming a escala en redes corporativas.

---

## Ver las pérdidas de verdad

Un problema didáctico: **en localhost no se pierde nada**. Podés mandar un millón de datagramas y llegan todos, así que la mitad de esta clase parece teórica.

Hay dos formas de ver el comportamiento real.

### Simular pérdidas en el código

El archivo `perdidas.py` que acompaña la clase envuelve el envío y descarta datagramas al azar:

```python
import random

def sendto_con_perdidas(sock, datos, destino, prob_perdida=0.3):
    """Simula una red que pierde el 30% de los paquetes."""
    if random.random() < prob_perdida:
        return len(datos)        # miente: dice que mandó, pero no manda
    return sock.sendto(datos, destino)
```

Mentir sobre el envío es exactamente lo que hace una red que pierde: tu programa cree que mandó, y del otro lado no llega.

### Degradar la red de verdad

En Linux se puede hacer que la interfaz pierda paquetes de verdad, con `tc` (*traffic control*) y su módulo `netem` (*network emulator*):

```bash
# 30% de pérdida en loopback
sudo tc qdisc add dev lo root netem loss 30%

# Volver a la normalidad
sudo tc qdisc del dev lo root
```

`tc` viene en el paquete `iproute2`, que ya está en casi cualquier Linux (es el mismo que trae `ip` y `ss`). Vive en `/sbin`, que no siempre está en el PATH de usuario: si `which tc` no lo encuentra, probá `/sbin/tc -V` antes de instalar nada. Con `sudo` funciona igual, porque root sí tiene `/sbin` en el PATH.

Además de perder, `netem` puede reordenar y duplicar, que son las otras dos cosas que UDP no garantiza y que en loopback nunca vas a ver:

```bash
sudo tc qdisc add dev lo root netem delay 200ms         # latencia
sudo tc qdisc add dev lo root netem duplicate 10%       # duplicados
sudo tc qdisc add dev lo root netem reorder 25% 50%     # desorden
sudo tc qdisc show dev lo                               # ver qué hay activo
```

Si estás en un contenedor sin privilegios, `tc` va a fallar aunque esté instalado: hace falta `NET_ADMIN`. En ese caso usá el simulador de `perdidas.py`.

Con eso andando, corré el cliente con reintentos y vas a ver los timeouts reales. Es la forma honesta de probar un protocolo antes de mandarlo a producción.

> Acordate de sacar la regla cuando termines. Un `tc` olvidado en loopback vuelve loco a cualquiera que use esa máquina después.

---

## Cuándo UDP y cuándo TCP

| Necesitás | Protocolo |
|-----------|-----------|
| Que llegue todo, en orden | TCP |
| Transferir un archivo | TCP |
| Una consulta corta con respuesta corta | UDP |
| Datos que envejecen (audio, video, posición) | UDP |
| Hablarle a muchos a la vez | UDP (broadcast/multicast) |
| Que el dato de hace 200ms ya no sirva | UDP |
| No querer implementar confiabilidad vos | TCP |

El criterio de fondo: **si retransmitir un dato viejo no tiene sentido, TCP te está estorbando**. En una llamada de voz, un paquete que llega 500ms tarde no sirve para nada, pero TCP igual va a retransmitirlo y va a frenar todo lo que venga atrás esperándolo. Eso se llama *head-of-line blocking*, y es la razón principal por la que el audio y el video usan UDP.

---

## Conceptos clave

1. **`SOCK_DGRAM` en vez de `SOCK_STREAM`**: y desaparecen `listen()` y `accept()`.
2. **Un solo socket atiende a todos**: no hay socket por cliente porque no hay conexión.
3. **`recvfrom()` devuelve datos y origen**: sin el origen no sabés a quién responder.
4. **Timeout obligatorio en el cliente**: sin cierre que detectar, un `recvfrom()` sin timeout espera para siempre.
5. **`connect()` en UDP no conecta**: fija destino por defecto, filtra remitentes y habilita errores ICMP.
6. **Un `sendto()` es un `recvfrom()`**: no hay framing que implementar.
7. **Buffer chico trunca el datagrama**: lo que no entra se descarta, no queda para después.
8. **Quedate por debajo del MTU**: fragmentar multiplica la probabilidad de perder el datagrama entero.
9. **Confiabilidad se implementa, y cuesta**: timeout, retransmisión, números de secuencia, deduplicación.
10. **Broadcast y multicast son exclusivos de UDP**: TCP es punto a punto por definición.

---

## Preparación para la próxima clase

En la **clase 16 (IPv6)** volvemos sobre el direccionamiento que dejamos pendiente en la clase 12. Vale para TCP y para UDP: es la capa de abajo. Vamos a ver por qué se agotaron las IPv4, cómo se escribe una dirección IPv6, y cómo se escribe código que funcione con las dos familias sin duplicarlo.

Para llegar preparado:

- Hacé el ejercicio del protocolo confiable: es el que más se usa después.
- Probá el `tc netem` al menos una vez, para ver pérdidas reales y no simuladas.

---

## Referencias

- [RFC 768](https://www.rfc-editor.org/rfc/rfc768) - UDP. Son tres páginas: leelo entero, es el RFC más corto que vas a ver
- [RFC 1035](https://www.rfc-editor.org/rfc/rfc1035) - DNS, el caso de uso canónico de UDP
- [Beej's Guide, capítulo de datagramas](https://beej.us/guide/bgnet/html/#datagram)
- [`socket` — documentación de Python](https://docs.python.org/3/library/socket.html)
- [tc-netem(8)](https://man7.org/linux/man-pages/man8/tc-netem.8.html) - simular pérdidas, latencia y reordenamiento

---

*Computación II - 2026 - Clase 15*
