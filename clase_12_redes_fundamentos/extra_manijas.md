# Clase 12: Redes - Extra Manijas

Material opcional para profundizar.

---

## Los ocho fallos de los sistemas distribuidos

En 1994, Peter Deutsch y otros en Sun Microsystems enumeraron las suposiciones falsas que todo programador hace la primera vez que escribe algo en red:

1. La red es confiable
2. La latencia es cero
3. El ancho de banda es infinito
4. La red es segura
5. La topología no cambia
6. Hay un solo administrador
7. El costo de transporte es cero
8. La red es homogénea

Cada una parece obviamente falsa enunciada así, y sin embargo el código que las asume se escribe todos los días. Un `requests.get()` sin timeout asume la 2. Un cliente que no reintenta asume la 1. Un protocolo que manda contraseñas en texto plano asume la 4.

Buena parte de lo que vamos a ver en el bloque de redes es, en el fondo, aprender a no asumir estas cosas.

---

## Por qué el handshake es de tres vías y no de dos

Una pregunta razonable: si el cliente dice "quiero conectarme" y el servidor responde "aceptado", ¿para qué el tercer mensaje?

El problema son los paquetes duplicados con retraso. Imaginá esta secuencia con solo dos pasos:

1. El cliente manda SYN, se pierde en la red (no se pierde: queda demorado en un router).
2. El cliente reintenta, se conecta, hace todo su trabajo, cierra.
3. El SYN original, demorado, finalmente llega al servidor.
4. El servidor responde SYN-ACK y considera la conexión abierta.
5. El cliente ya no está. El servidor queda con una conexión zombi.

El tercer paquete resuelve esto: el servidor no considera abierta la conexión hasta recibir el ACK del cliente, que solo va a llegar si el cliente realmente quiere conectarse ahora.

Este razonamiento —cómo un protocolo se defiende de mensajes viejos que reaparecen— es un ejemplo del tipo de problema que hace difícil el diseño de protocolos distribuidos.

### Los números de secuencia iniciales

Hay un detalle más: cada lado elige un número de secuencia inicial (ISN) aleatorio en el handshake, y no empieza en 0.

La razón original era distinguir segmentos de conexiones viejas de las nuevas sobre la misma cuádrupla. Pero hay una razón de seguridad: si el ISN fuera predecible, un atacante que no puede ver el tráfico podría igualmente inyectar paquetes en una conexión ajena adivinando los números. El *TCP sequence prediction attack* de los 90 explotaba justamente generadores de ISN predecibles.

---

## TIME_WAIT: por qué el puerto queda ocupado

Después de cerrar una conexión, el lado que la cierra primero queda en estado `TIME_WAIT` por el doble del MSL (Maximum Segment Lifetime), típicamente entre 1 y 4 minutos.

Verificalo:

```bash
ss -tan state time-wait
```

Esto explica el `Address already in use` cuando reiniciás un servidor rápido: el puerto sigue asociado a conexiones en TIME_WAIT.

¿Por qué existe este estado?

1. **Paquetes rezagados**: si un segmento de la conexión vieja llega tarde, TIME_WAIT garantiza que no sea interpretado como parte de una conexión nueva sobre la misma cuádrupla.
2. **El último ACK puede perderse**: si el ACK final del cierre se pierde, el otro lado retransmite el FIN. Alguien tiene que estar ahí para responder.

La solución habitual en servidores es `SO_REUSEADDR`:

```python
import socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(('0.0.0.0', 8080))
```

Lo vamos a usar en la clase 13. Vale la pena entender que no está "arreglando un bug": está diciéndole al kernel que acepta el riesgo, que en la práctica es despreciable para un servidor que escucha en un puerto fijo.

---

## MTU, fragmentación y el MSS

La capa de enlace impone un tamaño máximo de trama: el **MTU**. En Ethernet son 1500 bytes.

```bash
ip link show | grep mtu
```

Si un paquete IP supera el MTU del enlace, hay que fragmentarlo, algo costoso y frágil (si se pierde un fragmento, se pierde el paquete entero). TCP lo evita negociando un **MSS** (Maximum Segment Size) en el handshake, típicamente MTU menos 40 bytes de encabezados: 1460.

Ahí está el origen de un problema clásico: el **path MTU discovery** roto. Si algún enlace del camino tiene un MTU menor y los mensajes ICMP que lo informan están bloqueados por un firewall mal configurado, las conexiones se establecen bien (los paquetes chicos pasan) pero se cuelgan al transferir datos (los grandes se descartan en silencio). El síntoma —"conecta pero no transfiere"— es desconcertante hasta que se conoce la causa.

---

## El algoritmo de Nagle y el retraso de 40ms

TCP tiene una optimización que a veces molesta. El algoritmo de Nagle acumula datos chicos en lugar de mandar un paquete por cada escritura, para no desperdiciar 40 bytes de encabezado en 1 byte de datos.

El problema aparece al combinarse con los ACK retardados del otro lado: se puede producir un retraso de decenas de milisegundos en aplicaciones interactivas donde cada byte importa.

Se desactiva con `TCP_NODELAY`:

```python
s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
```

Casi todas las aplicaciones interactivas lo desactivan. Es también parte de por qué "TCP es un flujo": el protocolo se reserva el derecho de reagrupar tus escrituras como le convenga.

---

## Ver el estado de una conexión

TCP es una máquina de estados. Los nombres aparecen en `ss` y en la documentación:

```
CLOSED -> SYN_SENT -> ESTABLISHED -> FIN_WAIT_1 -> ... -> TIME_WAIT -> CLOSED
```

```bash
ss -tan                          # todos los estados
watch -n 0.5 'ss -tan | head'    # verlos cambiar en vivo
```

Correr ese `watch` mientras se abre y cierra una conexión con `nc` es una de las formas más directas de ver que la conexión no es un interruptor de dos posiciones sino un ciclo de vida.

---

## Sockets Unix: la red que no sale de la máquina

Existe una familia de sockets que usa la misma API pero no toca la red: `AF_UNIX`. En lugar de (IP, puerto), la dirección es una ruta del filesystem.

```python
import socket

# Servidor
s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
s.bind('/tmp/mi_socket')
s.listen(1)
```

Es más rápido que TCP sobre loopback (no hay encabezados ni checksums) y permite usar los permisos del filesystem como control de acceso. Docker, PostgreSQL y systemd los usan intensamente.

```bash
ls -l /var/run/docker.sock       # el socket del demonio de Docker
ss -x | head                     # sockets Unix activos
```

Que la misma API de sockets sirva para procesos locales y remotos es el mérito principal de la abstracción de Berkeley: el código cambia poco entre un caso y el otro.

---

## Herramientas más allá de lo básico

### mtr: traceroute continuo

```bash
mtr www.um.edu.ar
```

Combina ping y traceroute, actualizando en vivo. Mucho mejor para detectar en qué salto se pierden paquetes.

### socat: netcat con esteroides

```bash
# Proxy TCP que reenvía el puerto 8080 al 80 de otro host
socat TCP-LISTEN:8080,fork TCP:example.com:80
```

Conecta casi cualquier par de cosas: sockets, archivos, procesos, sockets Unix, puertos serie.

### tshark y Wireshark

`tcpdump` está bien para mirar rápido, pero Wireshark decodifica protocolos completos y sigue flujos TCP reensamblados.

```bash
sudo tcpdump -i lo -w captura.pcap port 8080    # capturar a archivo
wireshark captura.pcap                           # analizar después
```

La opción "Follow TCP Stream" de Wireshark reconstruye la conversación completa, lo que es una demostración visual directa de que TCP es un flujo.

---

## Lecturas

- Stevens, *TCP/IP Illustrated, Vol. 1* - el libro definitivo sobre qué pasa en el cable
- [Beej's Guide to Network Programming](https://beej.us/guide/bgnet/) - la introducción práctica más leída
- [RFC 9293](https://www.rfc-editor.org/rfc/rfc9293) - la especificación actual de TCP, que consolida décadas de parches
- [High Performance Browser Networking](https://hpbn.co/) (Grigorik) - gratis online, excelente sobre latencia y protocolos modernos
- [The Eight Fallacies of Distributed Computing](https://nighthacks.com/jag/res/Fallacies.html) - el texto original de Deutsch

---

*Computación II - 2026 - Clase 12*
