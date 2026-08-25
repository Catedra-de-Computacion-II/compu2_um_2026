# Clase 16: IPv6

## Introducción: la mudanza más larga de la historia

En la clase 12 dijimos que las direcciones IPv4 son 32 bits y que se agotaron, y dejamos IPv6 para más adelante. Llegó el momento.

IPv6 se estandarizó en 1998. Casi treinta años después, todavía convive con IPv4 y la transición sigue sin terminar. Esa lentitud no es anécdota: es lo que define cómo hay que programar hoy. **No podés elegir una familia y olvidarte de la otra**; tenés que escribir código que funcione con las dos.

La buena noticia es que la API de sockets casi no cambia. La mala es que los detalles que sí cambian son exactamente los que rompen programas en producción.

> **Nota:** los archivos `dual_stack.py` y `explorar_ipv6.py` acompañan la clase. Andan aunque no tengas conectividad IPv6 a Internet, que es el caso más común en Argentina.

---

## Por qué se acabaron las direcciones

32 bits dan 4.294.967.296 direcciones. Suena a mucho hasta que se reparte: bloques enteros quedaron asignados a universidades y empresas en los 80, hay rangos reservados que nadie usa, y cada dispositivo con conexión quiere una.

El agotamiento fue oficial y por etapas: IANA repartió su último bloque libre en **febrero de 2011**, y las agencias regionales se fueron quedando sin stock entre 2011 y 2020. Hoy conseguir IPv4 es comprarlas en un mercado secundario.

### NAT: el parche que duró treinta años

Lo que evitó el colapso fue NAT (*Network Address Translation*). Tu router tiene una IP pública y reparte direcciones privadas —las `192.168.x.x` de la clase 12— hacia adentro. Cuando salís a Internet, el router reescribe la dirección de origen y anota la correspondencia en una tabla.

Funciona, y es la razón por la que IPv4 todavía respira. Pero rompe cosas:

**Rompe la conectividad entrante.** Si estás detrás de NAT, nadie de afuera puede iniciar una conexión hacia vos: el router no sabe a qué máquina interna entregar el paquete. Por eso hostear algo en casa requiere abrir puertos a mano.

**Rompe el modelo extremo a extremo.** Internet se diseñó con la idea de que cualquier host puede hablarle a cualquier otro. NAT introduce un intermediario que reescribe paquetes, y las aplicaciones tienen que trabajar alrededor de eso. Las videollamadas P2P necesitan servidores STUN/TURN solo para atravesar NAT.

**Tiene estado.** El router tiene que recordar cada conexión activa. Si la tabla se llena, o si se reinicia, las conexiones se cortan.

IPv6 elimina la necesidad de NAT dándole a cada dispositivo una dirección pública. Eso restaura el modelo original, y también significa que tu heladera es alcanzable desde Internet —por eso el firewall pasa a ser imprescindible, no opcional.

### Por qué IPv6 y no IPv5

IPv5 existió: fue un protocolo experimental de streaming de los 70 (ST, *Internet Stream Protocol*) que consumió el número de versión 5. Cuando hizo falta el sucesor de IPv4, el 5 estaba tomado.

---

## Cómo se escribe una dirección

128 bits, escritos en ocho grupos de cuatro dígitos hexadecimales separados por dos puntos:

```
2001:0db8:85a3:0000:0000:8a2e:0370:7334
```

Son 340 sextillones de direcciones. La comparación habitual: alcanzan para asignarle una a cada átomo de la superficie terrestre y sobran.

Escribir eso completo es insufrible, así que hay dos reglas de compresión.

**Regla 1: quitar ceros a la izquierda de cada grupo.**

```
2001:db8:85a3:0:0:8a2e:370:7334
```

**Regla 2: reemplazar UNA secuencia de grupos en cero por `::`.**

```
2001:db8:85a3::8a2e:370:7334
```

El `::` solo puede aparecer **una vez** por dirección. Si apareciera dos veces, sería ambiguo: no habría forma de saber cuántos grupos de ceros representa cada uno.

Algunos ejemplos que conviene reconocer:

| Dirección | Comprimida | Qué es |
|-----------|-----------|--------|
| `0000:...:0001` | `::1` | Loopback (el `127.0.0.1` de IPv6) |
| `0000:...:0000` | `::` | Sin especificar / todas las interfaces |
| `fe80::...` | | Link-local |
| `2000::/3` | | Unicast global (lo ruteable) |
| `ff00::/8` | | Multicast |

Python te ayuda a normalizar:

```python
import ipaddress

a = ipaddress.ip_address('2001:0db8:85a3:0000:0000:8a2e:0370:7334')
print(a.compressed)      # 2001:db8:85a3::8a2e:370:7334
print(a.exploded)        # 2001:0db8:85a3:0000:0000:8a2e:0370:7334
```

### Puertos y URLs: los corchetes

Una dirección IPv6 tiene dos puntos, y un `host:puerto` también. Sin desambiguar, `::1:8080` es imposible de leer.

La convención es encerrar la dirección entre corchetes:

```
http://[2001:db8::1]:8080/ruta
```

En Python, la tupla de dirección resuelve esto sin corchetes, pero cuando construyas URLs o leas configuraciones, los corchetes importan.

---

## Una interfaz, varias direcciones

Este es el cambio conceptual más grande respecto de IPv4. En IPv6 **es normal que una interfaz tenga varias direcciones a la vez**, cada una con un alcance distinto.

Miralo en tu máquina:

```bash
ip -6 addr show
```

Vas a ver algo así:

```
1: lo
    inet6 ::1/128 scope host
2: wlp63s0
    inet6 2803:9800:9842:8187:3fd6:700:a948:d28/64 scope global
    inet6 fe80::e570:5b50:dafb:ec40/64 scope link
```

Tres direcciones, tres alcances:

**`::1` — host.** Loopback, no sale de la máquina.

**`fe80::/10` — link-local.** Se autoconfigura siempre, sin DHCP ni router. Solo vale dentro del segmento de red físico: los routers nunca la reenvían. Es lo que usan los protocolos de descubrimiento de vecinos.

**`2803:...` — global.** Ruteable en Internet, asignada por el router vía autoconfiguración.

La link-local siempre existe, aunque no tengas Internet. Eso la hace útil y también incómoda, por lo que viene ahora.

### El scope ID: por qué `fe80::1` no alcanza

Como toda interfaz tiene una `fe80::`, una dirección link-local sola es ambigua: ¿por cuál interfaz la mando?

Por eso hay que indicar la interfaz con `%`:

```
fe80::e570:5b50:dafb:ec40%wlp63s0
```

Eso es el **scope ID**. Sin él, conectarse a una link-local falla con "Invalid argument".

```bash
ping6 fe80::1                    # error: falta la interfaz
ping6 fe80::1%wlp63s0            # ahora sí
```

Y acá aparece algo que ya vieron sin explicación. En el ejercicio 7 de la clase 12, `getsockname()` devolvía **cuatro** elementos en vez de dos al salir por IPv6:

```python
('2803:9800:9842:8187:3fd6:700:a948:d28', 43792, 0, 0)
#  dirección                                puerto  flowinfo  scope_id
```

Ahí está la explicación: los dos extra son `flowinfo` (casi siempre 0, pensado para QoS y poco usado) y `scope_id` (el índice de la interfaz, distinto de cero justamente en las link-local).

**Consecuencia práctica:** si tu código hace `host, puerto = sock.getsockname()`, se rompe con IPv6. Y es un bug que no aparece en desarrollo si probás solo con IPv4.

```python
info = sock.getsockname()
host, puerto = info[0], info[1]      # funciona con las dos familias
```

---

## Programar con IPv6

### Un socket IPv6

```python
import socket

s = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
s.bind(('::1', 8080))         # ::1 es el localhost de IPv6
s.listen(5)
```

Lo mismo de siempre, cambiando `AF_INET` por `AF_INET6`. Las direcciones especiales tienen su equivalente:

| IPv4 | IPv6 | Significa |
|------|------|-----------|
| `127.0.0.1` | `::1` | Solo esta máquina |
| `0.0.0.0` | `::` | Todas las interfaces |

### La forma incorrecta de soportar las dos familias

Lo intuitivo es duplicar:

```python
# NO hagas esto
if usar_ipv6:
    s = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
    s.connect(('::1', 8080))
else:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(('127.0.0.1', 8080))
```

Además de duplicar código, tenés que decidir vos cuál usar, y esa decisión depende de información que no tenés: si el destino soporta IPv6, si la ruta funciona, si hay firewall en el medio.

### La forma correcta: getaddrinfo()

`getaddrinfo()` traduce un nombre y un servicio a una lista de posibilidades, ordenadas por preferencia del sistema:

```python
import socket

for info in socket.getaddrinfo('google.com', 80, type=socket.SOCK_STREAM):
    familia, tipo, proto, canonname, direccion = info
    print(familia.name, direccion)
```

Salida típica:

```
AF_INET6 ('2800:3f0:4001:war::200e', 80, 0, 0)
AF_INET  ('142.250.79.174', 80)
```

Fijate que devuelve **las dos familias**, y que la tupla de IPv6 tiene cuatro elementos y la de IPv4 dos. La biblioteca ya te está diciendo con qué crear el socket.

El patrón correcto es probar cada resultado hasta que uno funcione:

```python
def conectar(host, puerto, timeout=5):
    """Conecta probando todas las direcciones, IPv6 e IPv4."""
    ultimo_error = None
    for familia, tipo, proto, _, direccion in socket.getaddrinfo(
            host, puerto, type=socket.SOCK_STREAM):
        s = socket.socket(familia, tipo, proto)
        try:
            s.settimeout(timeout)
            s.connect(direccion)
            return s
        except OSError as e:
            s.close()
            ultimo_error = e
    raise ultimo_error
```

Ese bucle es importante: tener dirección IPv6 no garantiza que la ruta funcione. Es exactamente la situación de muchas conexiones en Argentina —el ISP te da una IPv6 global pero sin ruta a Internet— y si tu código no reintenta con IPv4, falla.

### El atajo que ya venían usando

Todo lo anterior ya lo hace `create_connection()`, que usamos desde la clase 13:

```python
with socket.create_connection(('google.com', 80), timeout=5) as s:
    ...
```

Internamente hace `getaddrinfo()` y prueba en orden. Por eso conviene usarlo siempre que seas cliente: te da soporte dual gratis.

Para el servidor no hay atajo equivalente, y ahí entra lo que sigue.

---

## Dual-stack: un socket para las dos familias

Un socket IPv6 puede aceptar conexiones IPv4, si el sistema lo permite. Las conexiones IPv4 aparecen como direcciones **mapeadas**, con el prefijo `::ffff:`:

```
Cliente IPv6 conecta -> el servidor ve  ::1
Cliente IPv4 conecta -> el servidor ve  ::ffff:127.0.0.1
```

Eso lo controla la opción `IPV6_V6ONLY`:

```python
s = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
s.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)   # aceptar ambas
s.bind(('::', 8080))
```

Con `V6ONLY = 0`, un solo socket en `::` atiende IPv6 e IPv4. Con `V6ONLY = 1`, solo IPv6, y necesitás un segundo socket para IPv4.

**El problema es que el valor por defecto varía según el sistema.** En Linux suele ser 0 (dual-stack), en OpenBSD y Windows es 1. Verificalo:

```bash
cat /proc/sys/net/ipv6/bindv6only      # 0 = dual-stack por defecto
```

Nunca dependas del default: **ponelo explícitamente**, para los dos casos. Es una línea que evita que tu servidor se comporte distinto en la máquina del profesor que en la tuya.

### Detectar direcciones mapeadas

Si tu servidor loguea o filtra por IP, las mapeadas te van a confundir: `::ffff:192.168.1.5` y `192.168.1.5` son el mismo cliente escrito distinto.

```python
import ipaddress

def normalizar(host):
    """Convierte ::ffff:1.2.3.4 en 1.2.3.4; deja el resto igual."""
    try:
        a = ipaddress.ip_address(host)
    except ValueError:
        return host
    if a.version == 6 and a.ipv4_mapped:
        return str(a.ipv4_mapped)
    return host
```

---

## Lo que cambió en el protocolo

Además de las direcciones, IPv6 arregló cosas del encabezado IPv4.

**Encabezado de tamaño fijo (40 bytes).** El de IPv4 era variable por las opciones, lo que obligaba a los routers a parsear más. Fijo es más rápido de procesar en hardware.

**Sin checksum en la capa de red.** IPv4 tenía uno y había que recalcularlo en cada salto, porque el TTL cambia. IPv6 lo eliminó: confía en que las capas de arriba y abajo verifican. Esa es la razón por la que el checksum de UDP, opcional en IPv4, **es obligatorio en IPv6** —lo mencionamos en las manijas de la clase 15.

**Los routers no fragmentan.** En IPv4, un router podía fragmentar un paquete demasiado grande. En IPv6 solo el emisor fragmenta, y si el paquete no entra, el router responde ICMPv6 *Packet Too Big*. Esto hace que el *path MTU discovery* de la clase 15 pase de conveniente a obligatorio.

**MTU mínimo de 1280 bytes**, contra 576 de IPv4. Todo enlace IPv6 debe soportar al menos eso.

**ICMPv6 es imprescindible.** En IPv4 se podía bloquear ICMP y casi todo seguía andando. En IPv6, ICMPv6 hace el descubrimiento de vecinos (el reemplazo de ARP), la autoconfiguración y el path MTU discovery. **Bloquearlo rompe la red.** Es un error clásico de configuración de firewall.

### Autoconfiguración: direcciones sin DHCP

Una máquina IPv6 puede conseguir dirección sin servidor: manda un *Router Solicitation*, el router responde con el prefijo de la red, y la máquina se arma la dirección combinando ese prefijo con un identificador propio.

Al principio ese identificador derivaba de la MAC (formato EUI-64), lo cual era un problema de privacidad: tu dirección te seguía entre redes y era rastreable. Por eso existen las *privacy extensions* (RFC 4941), que generan identificadores aleatorios que rotan. Es lo que hace tu sistema hoy por defecto, y explica por qué podés ver varias direcciones globales en la misma interfaz: una estable y otras temporales.

---

## Probar sin conectividad IPv6

Un obstáculo práctico: en Argentina muchos ISP todavía no dan IPv6 funcional. Podés tener dirección global y no tener ruta.

Verificá tu situación:

```bash
ip -6 addr show                          # ¿tenés direcciones?
ping6 -c2 2001:4860:4860::8888           # ¿llegás al DNS de Google?
```

Si el `ping6` dice "La red es inaccesible", tenés dirección pero no ruta. **No importa para esta clase**: loopback IPv6 (`::1`) funciona siempre, y todos los ejercicios están pensados para correr localmente.

Para probar contra Internet IPv6 sin tenerlo, hay servicios públicos de túnel (Hurricane Electric), pero queda fuera del alcance de la materia.

---

## Conceptos clave

1. **IPv4 se agotó en 2011**: NAT lo estiró treinta años, al costo de romper el modelo extremo a extremo.
2. **128 bits, hexadecimal, con `::` una sola vez**: la compresión es obligatoria de entender para leer direcciones.
3. **`::1` es el nuevo `127.0.0.1`, `::` el nuevo `0.0.0.0`**.
4. **Una interfaz tiene varias direcciones**: link-local siempre, global si hay router.
5. **Las link-local necesitan scope ID**: `fe80::1%eth0`, si no son ambiguas.
6. **La tupla de dirección IPv6 tiene 4 elementos**: desempaquetar en 2 rompe el código.
7. **Usá `getaddrinfo()`, no elijas la familia a mano**: y como cliente, `create_connection()` ya lo hace.
8. **Tener IPv6 no garantiza que funcione**: hay que reintentar con IPv4, no asumir.
9. **Poné `IPV6_V6ONLY` explícitamente**: el default varía entre sistemas.
10. **Las conexiones IPv4 a un socket dual aparecen como `::ffff:`**: normalizalas antes de loguear o filtrar.
11. **No bloquees ICMPv6**: a diferencia de IPv4, la red deja de funcionar.

---

## Preparación para la próxima clase

En la **clase 17 (I/O Multiplexing)** volvemos al problema que dejó abierto la clase 14: cómo atender muchos clientes sin un thread ni un proceso por cada uno. La respuesta es `select()`, `poll()` y `epoll()`, que permiten esperar por muchos sockets a la vez en un solo hilo. Es la base sobre la que está construido asyncio.

Para llegar preparado:

- Hacé el ejercicio del servidor dual-stack: lo vamos a reusar.
- Repasá por qué el servidor secuencial de la clase 13 no escalaba, y qué costo tenía cada solución de la 14.

---

## Referencias

- [RFC 8200](https://www.rfc-editor.org/rfc/rfc8200) - IPv6, la especificación actual
- [RFC 4291](https://www.rfc-editor.org/rfc/rfc4291) - Arquitectura de direccionamiento: los tipos y prefijos
- [RFC 4941](https://www.rfc-editor.org/rfc/rfc4941) - Privacy extensions
- [`ipaddress` — documentación de Python](https://docs.python.org/3/library/ipaddress.html) - para manipular direcciones sin parsear strings a mano
- [Test IPv6](https://test-ipv6.com/) - diagnóstico de tu conectividad desde el navegador

---

*Computación II - 2026 - Clase 16*
