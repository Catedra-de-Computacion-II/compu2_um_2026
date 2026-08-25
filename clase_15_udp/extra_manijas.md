# Clase 15: UDP - Extra Manijas

Material opcional para profundizar.

---

## El checksum opcional (y por qué eso fue mala idea)

El encabezado UDP tiene 8 bytes: puerto origen, puerto destino, longitud y checksum. En IPv4 **el checksum es opcional**: mandar cero significa "no lo calculé".

Era razonable en 1980, cuando calcularlo costaba caro y las redes locales tenían su propia detección de errores. Hoy es un problema: sin checksum, un bit que se corrompe en tránsito llega a tu aplicación como dato válido.

En IPv6 lo hicieron obligatorio, justamente porque IPv6 eliminó el checksum de la capa de red y ya no hay red abajo que cubra el hueco.

Detalle incómodo: el checksum de UDP cubre también un *pseudo-encabezado* con las direcciones IP de origen y destino, que pertenecen a la capa de abajo. Es una violación deliberada de la separación de capas —se hizo para detectar datagramas mal entregados— y es la razón por la que NAT tiene que recalcular el checksum UDP al reescribir direcciones.

---

## Por qué QUIC se construyó sobre UDP

HTTP/3 no usa TCP. Usa QUIC, que corre sobre UDP e implementa por su cuenta lo que TCP ya daba: confiabilidad, orden, control de congestión.

Suena a reinventar la rueda, pero hay tres razones concretas.

**TCP vive en el kernel.** Cambiar su comportamiento requiere actualizar el sistema operativo de todos los intervinientes. Un algoritmo de congestión nuevo tarda una década en desplegarse. QUIC vive en espacio de usuario: se actualiza con el navegador.

**Head-of-line blocking por conexión.** HTTP/2 multiplexa varios streams sobre una conexión TCP, pero si se pierde un segmento, TCP frena **todos** los streams hasta retransmitirlo, aunque los demás no dependan de ese dato. QUIC maneja los streams por separado: uno se frena, los demás siguen.

**Migración de conexión.** Una conexión TCP se identifica por la cuádrupla. Si cambiás de wifi a datos móviles, tu IP cambia y la conexión muere. QUIC identifica las conexiones con un ID propio, así que sobrevive al cambio de red: por eso una videollamada puede seguir cuando salís de casa.

El costo es que todo eso hay que implementarlo bien, y son años de trabajo. No es un argumento para que reimplementes TCP en el TP.

---

## El buffer de recepción y los datagramas que el kernel tira

Un problema real que no se ve en localhost: si los datagramas llegan más rápido de lo que tu programa los lee, el kernel llena el buffer de recepción y **descarta los siguientes en silencio**.

```python
s.getsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF)      # tamaño actual
s.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 4 * 1024 * 1024)
```

Ojo con el resultado: Linux primero **recorta** el pedido a `/proc/sys/net/core/rmem_max` y después **duplica** lo que quedó (la mitad extra es overhead interno). Con el default de 212992, pedir 4 MB devuelve 425984, no 8 MB:

```bash
cat /proc/sys/net/core/rmem_max        # 212992 en un Debian típico
```

Para pasar de ahí hace falta subir el tope del sistema (`sysctl -w net.core.rmem_max=...`), no alcanza con pedir más desde el programa. Verificá siempre con `getsockopt()` lo que quedó, en vez de asumir que el `setsockopt()` te dio lo que pediste.

Podés ver los descartes:

```bash
netstat -su | grep -i "packet receive errors\|receive buffer errors"
cat /proc/net/udp     # la columna 'drops' por socket
```

Si un receptor UDP pierde datos bajo carga y la red está sana, mirá esos contadores antes de culpar a la red. Es casi siempre el receptor que no da abasto.

La solución de fondo no es agrandar el buffer sino leer más rápido: un hilo dedicado que solo hace `recvfrom()` y encola, con el procesamiento en otro lado.

---

## recvmmsg: leer muchos datagramas de una syscall

Con tráfico alto, una syscall por datagrama es caro. Linux ofrece `recvmmsg()`, que lee varios de una vez.

Python no lo expone directamente en `socket`, pero está en `socket.recvmsg_into()` y variantes, y las bibliotecas de alto rendimiento lo usan vía C. Es una de las razones por las que un servidor DNS en C aguanta órdenes de magnitud más consultas que uno en Python puro.

Para dimensionar: una syscall cuesta del orden de 1-2 microsegundos. A un millón de datagramas por segundo, eso es todo tu CPU en cambios de contexto.

---

## SO_REUSEPORT: varios procesos en el mismo puerto

En la clase 14 vimos varias estrategias para atender clientes concurrentemente. Con UDP hay una que TCP también soporta pero se usa menos:

```python
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
s.bind(('0.0.0.0', 8080))
```

Con `SO_REUSEPORT`, **varios procesos pueden hacer bind al mismo puerto** y el kernel reparte los datagramas entre ellos con un hash del origen. No hay proceso maestro que distribuya: el kernel balancea.

No confundir con `SO_REUSEADDR`, que resuelve otra cosa (el TIME_WAIT de la clase 13).

Es la forma moderna de escalar un servidor UDP a varios cores, y evita el cuello de botella de un único hilo leyendo del socket.

---

## Descubrimiento de MTU sin fragmentar

Se puede pedirle al kernel que **no** fragmente y avise si el datagrama no entra:

```python
import socket

IP_MTU_DISCOVER = 10
IP_PMTUDISC_DO = 2

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.setsockopt(socket.IPPROTO_IP, IP_MTU_DISCOVER, IP_PMTUDISC_DO)
s.connect(('8.8.8.8', 53))
try:
    s.send(b'X' * 2000)
except OSError as e:
    print(f'No entra sin fragmentar: {e}')
    print('MTU del camino:', s.getsockopt(socket.IPPROTO_IP, 14))   # IP_MTU
```

Con el flag DF (Don't Fragment) puesto, un router que no pueda reenviar el paquete responde un ICMP *fragmentation needed* indicando el MTU disponible. Esa es la base del *path MTU discovery* que mencionamos en las manijas de la clase 12.

Y también su punto débil: si un firewall filtra esos ICMP, el emisor nunca se entera y los paquetes grandes desaparecen en silencio. Es el "conecta pero no transfiere" clásico.

---

## Amplificación: por qué UDP es el favorito de los ataques DDoS

Un detalle incómodo de UDP: **no hay handshake que verifique el origen**. Podés poner cualquier IP como remitente y el servidor le va a responder a esa, no a vos.

Si además la respuesta es mucho más grande que el pedido, tenés un amplificador:

| Protocolo | Factor de amplificación |
|-----------|------------------------|
| DNS | ~50x |
| NTP (monlist) | ~500x |
| memcached | ~50000x |

Con 1 Mbps de pedidos falsificados hacia servidores memcached abiertos, un atacante genera 50 Gbps hacia la víctima. El ataque de 1.35 Tbps contra GitHub en 2018 fue exactamente esto.

TCP no sirve para amplificar porque el handshake de tres vías exige que el emisor reciba el SYN-ACK: si falsificaste la IP, nunca completás la conexión. El handshake que en la clase 13 parecía solo latencia extra resulta ser también una verificación de origen.

Por eso los protocolos UDP modernos limitan cuánto responden antes de validar al cliente: QUIC no manda más de 3 veces lo que recibió hasta confirmar la dirección.

---

## Herramientas

### iperf3 para medir

```bash
# Servidor
iperf3 -s

# Cliente: 10 Mbps de UDP durante 10 segundos
iperf3 -c localhost -u -b 10M -t 10
```

Reporta pérdida y jitter, que son las dos métricas que importan en UDP y que TCP esconde.

### tcpdump para ver los datagramas

```bash
sudo tcpdump -i lo -n udp port 8080 -X
```

A diferencia de TCP, cada línea es un datagrama completo: no hay handshake ni ACKs mezclados. Es notablemente más fácil de leer.

### socat

```bash
# Reenviar UDP a otro host
socat -u UDP-LISTEN:8080,fork UDP:otrohost:9090
```

---

## Lecturas

- [RFC 768](https://www.rfc-editor.org/rfc/rfc768) - UDP completo en tres páginas
- [RFC 9000](https://www.rfc-editor.org/rfc/rfc9000) - QUIC. Largo, pero la introducción explica bien las motivaciones
- [Cloudflare: memcached DDoS](https://blog.cloudflare.com/memcrashed-major-amplification-attacks-from-port-11211/) - el análisis del ataque de amplificación
- Stevens, *UNIX Network Programming, Vol. 1* - capítulo 8 (UDP) y 22 (opciones avanzadas)
- [High Performance Browser Networking, cap. 3](https://hpbn.co/building-blocks-of-udp/) - UDP y NAT traversal

---

*Computación II - 2026 - Clase 15*
