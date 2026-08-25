# Clase 16: IPv6 - Extra Manijas

Material opcional para profundizar.

---

## Happy Eyeballs: cómo eligen los navegadores

El problema de tener dos familias es real y molesto: si intentás IPv6 primero y la ruta está rota, el usuario espera el timeout completo —decenas de segundos— antes de que se pruebe IPv4. Eso hizo que muchos sitios evitaran IPv6 durante años: activarlo empeoraba la experiencia de los usuarios con IPv6 mal configurado.

La solución se llama **Happy Eyeballs** (RFC 8305) y es más astuta que el bucle secuencial que escribimos en clase:

1. Empezar la conexión IPv6.
2. **No esperar a que falle**: a los ~250 ms, arrancar también la IPv4 en paralelo.
3. Quedarse con la que conecte primero, cancelar la otra.
4. Recordar el resultado para las próximas conexiones a ese host.

El sesgo hacia IPv6 es deliberado: la ventaja de 250 ms hace que IPv6 gane cuando funciona, pero un usuario con IPv6 roto pierde un cuarto de segundo en vez de treinta.

Chrome, Firefox y curl lo implementan. En Python, `socket.create_connection()` **no** lo hace —prueba en serie—, pero asyncio sí:

```python
reader, writer = await asyncio.open_connection(
    'google.com', 80, happy_eyeballs_delay=0.25)
```

El parámetro no aparece en la firma de `open_connection` porque viaja en `**kwds` hasta `loop.create_connection()`, que es donde está documentado junto con `interleave`. Lo vamos a retomar cuando lleguemos a asyncio (clase 19 en adelante).

Es un buen ejemplo de que la solución correcta no siempre es la más simple: el bucle `for` de `getaddrinfo()` es didáctico y correcto, pero en producción la latencia importa.

---

## Cómo se reparten los prefijos

En IPv4 el direccionamiento se volvió una tacañería: un `/24` con 254 hosts es una red doméstica generosa. En IPv6 la lógica es otra.

| Prefijo | Quién lo recibe |
|---------|-----------------|
| `/32` | Un ISP mediano |
| `/48` | Una organización |
| `/56` | Una casa (típico, permite 256 subredes) |
| `/64` | **Una** subred |

El `/64` es casi sagrado: SLAAC lo requiere, porque los últimos 64 bits son el identificador de interfaz. Una subred IPv6 tiene 18 trillones de direcciones, y esa aparente exageración es lo que permite que la autoconfiguración funcione sin coordinación central.

Consecuencia práctica: **no subnetees más allá de `/64`**. Es tentador venir de IPv4 y querer ahorrar direcciones, pero un `/120` rompe SLAAC y no gana nada — no hay escasez que administrar.

Verificá qué prefijo te dio tu ISP:

```bash
ip -6 addr show | grep global
```

Si ves un `/64`, te dieron una sola subred. Con un `/56` podrías armar 256 redes internas.

---

## Escanear una red IPv6 es imposible (y eso cambia la seguridad)

Escanear una red IPv4 doméstica (`/24`) son 254 intentos: cuestión de segundos. Escanear un `/64` son 18.446.744.073.709.551.616 direcciones. A un millón de sondas por segundo, tardarías **medio millón de años**.

Eso mata el escaneo por fuerza bruta, que es la técnica base de reconocimiento en IPv4. Pero no significa que IPv6 sea más seguro, por tres razones:

**Multicast local delata a todos.** `ping6 ff02::1%eth0` hace ping a todos los nodos del enlace y responden todos. Dentro de la red, encontrarlos es trivial.

**Las direcciones no son aleatorias en la práctica.** Los servidores configurados a mano suelen quedar en `::1`, `::2`, `::80`, `::443`. Un atacante prueba esos primero, no todo el espacio.

**Sin NAT, todo es alcanzable.** En IPv4 el NAT hacía de firewall accidental. En IPv6 cada dispositivo tiene dirección pública, así que el firewall pasa de ser una comodidad a ser obligatorio. Una impresora que en IPv4 solo era visible desde la LAN, en IPv6 puede ser alcanzable desde Internet si nadie configuró nada.

La conclusión no es que IPv6 sea peor: es que la seguridad que dependía de un accidente arquitectónico ahora hay que configurarla explícitamente.

---

## Direcciones temporales y privacidad

Si mirás tus direcciones globales puede que haya más de una:

```bash
ip -6 addr show | grep -A1 "scope global"
```

Con las *privacy extensions* activadas, el sistema mantiene:

- Una dirección **estable**, para servicios entrantes
- Varias **temporales**, que rotan (típicamente cada día) y se usan para conexiones salientes

El motivo es que el esquema original (EUI-64) derivaba el identificador de la MAC, que es única y permanente. Eso significaba que tu dirección IPv6 te seguía entre redes: cambiabas de wifi y los primeros 64 bits cambiaban, pero los últimos 64 te identificaban unívocamente. Un rastreador podía seguirte entre el trabajo, tu casa y el café.

```bash
sysctl net.ipv6.conf.all.use_tempaddr        # 2 = activadas y preferidas
```

Cuando programás un servidor esto importa poco, pero cuando programás un cliente, la dirección de origen que ve el otro extremo puede cambiar entre ejecuciones. No la uses como identidad.

---

## Mecanismos de transición

La migración lleva casi treinta años y hay una fauna de mecanismos intermedios. Vale conocerlos porque te los vas a cruzar en logs y configuraciones.

**Dual-stack.** Correr las dos pilas en paralelo. Es lo que hicimos en clase y lo más común. El costo es operativo: dos configuraciones, dos firewalls, dos conjuntos de bugs.

**Túneles (6in4, 6to4, Teredo).** Encapsular IPv6 dentro de IPv4 para atravesar redes que solo hablan IPv4. Fueron útiles cuando IPv6 era una isla; hoy están mayormente en desuso y varios se consideran obsoletos por problemas de seguridad y rendimiento.

**NAT64 / DNS64.** Para redes *IPv6-only* que necesitan alcanzar servidores IPv4. El DNS64 fabrica una dirección IPv6 sintética para un host que solo tiene IPv4, y el NAT64 traduce en el camino. Es lo que usan las redes móviles modernas: muchos celulares hoy son IPv6-only y ni te enterás.

**464XLAT.** Combinación que permite que aplicaciones que solo hablan IPv4 funcionen sobre una red IPv6-only. Es lo que hace que una app vieja siga andando en tu celular.

El caso móvil es el más notable: T-Mobile, Verizon y varias operadoras funcionan IPv6-only desde hace años, y la mayoría de los usuarios nunca lo notó. La transición avanzó más de lo que parece desde una conexión hogareña argentina.

---

## Medir la adopción real

```bash
# ¿Tu conexión tiene IPv6 funcional?
curl -6 -s https://ifconfig.co 2>&1 | head -1

# Comparar con IPv4
curl -4 -s https://ifconfig.co
```

Google publica estadísticas de qué porcentaje de sus usuarios llega por IPv6: [google.com/intl/en/ipv6/statistics.html](https://www.google.com/intl/en/ipv6/statistics.html). Pasó del 1% en 2012 a más del 40% hoy, con enormes diferencias por país —India y Alemania arriba del 70%, Argentina bastante más abajo.

Esa desigualdad geográfica es la razón por la que no podés asumir IPv6 ni ignorarlo: depende de dónde estén tus usuarios.

---

## Sockets IPv6 en detalle

Algunas opciones que no vimos en clase:

```python
import socket

s = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)

# Límite de saltos (el equivalente del TTL de IPv4)
s.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_UNICAST_HOPS, 64)

# Multicast IPv6: por qué interfaz salir
s.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_MULTICAST_IF, indice_interfaz)

# Recibir información sobre el paquete (interfaz de llegada, dirección destino)
s.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_RECVPKTINFO, 1)
```

El índice de interfaz se obtiene con:

```python
socket.if_nametoindex('eth0')      # -> 2
socket.if_indextoname(2)           # -> 'eth0'
```

Ese índice es exactamente el `scope_id` de la tupla de cuatro elementos. Cuando te conectás a una link-local, en vez de escribir `fe80::1%eth0` podés armar la tupla a mano:

```python
s.connect(('fe80::1', 8080, 0, socket.if_nametoindex('eth0')))
```

Es la misma información, expresada en la API en lugar de en el string.

---

## Lecturas

- [RFC 8200](https://www.rfc-editor.org/rfc/rfc8200) - IPv6, especificación actual
- [RFC 8305](https://www.rfc-editor.org/rfc/rfc8305) - Happy Eyeballs v2
- [RFC 6724](https://www.rfc-editor.org/rfc/rfc6724) - Cómo el sistema elige entre direcciones origen y destino; explica el orden de `getaddrinfo()`
- [RFC 4941](https://www.rfc-editor.org/rfc/rfc4941) - Privacy extensions
- [Estadísticas IPv6 de Google](https://www.google.com/intl/en/ipv6/statistics.html)
- [IPv6 Essentials](https://www.oreilly.com/library/view/ipv6-essentials-3rd/9781449335229/) (Silvia Hagen) - el libro de referencia

---

*Computación II - 2026 - Clase 16*
