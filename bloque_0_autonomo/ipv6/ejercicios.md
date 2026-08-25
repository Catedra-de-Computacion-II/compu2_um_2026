# Clase 16: IPv6 - Ejercicios Prácticos

Los archivos `explorar_ipv6.py` y `dual_stack.py` acompañan la clase.

**Antes de empezar**, chequeá tu situación:

```bash
ip -6 addr show                          # ¿tenés direcciones IPv6?
ping6 -c2 2001:4860:4860::8888           # ¿hay ruta a Internet?
```

Si el `ping6` falla con "La red es inaccesible", tenés dirección pero no ruta. **Es lo normal en Argentina y no afecta a ningún ejercicio obligatorio**: todo se prueba sobre `::1`.

---

## Ejercicio 1: Leer y escribir direcciones

### 1.1 Compresión a mano

Comprimí estas direcciones aplicando las dos reglas, **sin usar Python**:

1. `2001:0db8:0000:0000:0000:ff00:0042:8329`
2. `0000:0000:0000:0000:0000:0000:0000:0001`
3. `fe80:0000:0000:0000:0202:b3ff:fe1e:8329`
4. `2001:0db8:0000:0000:0001:0000:0000:0001`

Verificá después con:

```python
import ipaddress
print(ipaddress.ip_address('2001:0db8:...').compressed)
```

5. La cuarta tiene **dos** secuencias de ceros. ¿Por qué no podés poner `::` en las dos? Escribí las dos interpretaciones posibles de `2001:db8::1::1` para mostrar la ambigüedad.

### 1.2 Expandir

Escribí completas (sin comprimir) estas direcciones:

6. `::1`
7. `2001:db8::8a2e:370:7334`
8. `ff02::1`

Verificá con `.exploded`.

### 1.3 Clasificar

```bash
python3 explorar_ipv6.py
```

9. Mirá la sección 2. ¿Por qué `2001:db8::1` aparece como "reservada/privada" y no como global?
10. ¿Por qué `ff02::1` da `is_global=True` en la stdlib aunque sea multicast? ¿Qué te dice eso sobre confiar en un solo flag?

---

## Ejercicio 2: Las direcciones de tu máquina

```bash
ip -6 addr show
```

1. ¿Cuántas direcciones IPv6 tiene tu máquina? Agrupalas por scope (`host`, `link`, `global`).
2. ¿Cuántas interfaces tienen una `fe80::`? Si tenés Docker instalado, ¿por qué hay tantas?
3. ¿Tenés dirección global? ¿Y ruta? Usá el `explorar_ipv6.py` para responder las dos cosas por separado.
4. Buscá el `/64` al final de tu dirección global. ¿Cuántos bits quedan para hosts en tu red? Compará con una red IPv4 doméstica típica (`/24`).

### El scope ID

5. Intentá hacer ping a una link-local sin especificar interfaz:

```bash
ping6 -c1 fe80::1
```

¿Qué error da? ¿Por qué es ambigua?

6. Ahora con la interfaz:

```bash
ping6 -c1 fe80::1%eth0        # cambiá eth0 por la tuya
```

7. En Python, `getsockname()` sobre un socket IPv6 devuelve cuatro elementos. ¿Cuáles son? Corré la sección 5 de `explorar_ipv6.py`.
8. ¿Qué pasa si tu código hace `host, puerto = sock.getsockname()` y el socket es IPv6? Probalo y mirá el error. ¿Cómo se escribe para que funcione con las dos familias?

---

## Ejercicio 3: Servidor dual-stack (obligatorio)

### Objetivo

Escribir un servidor que atienda IPv4 e IPv6 con un solo socket, y entender qué controla ese comportamiento.

### Parte A: ver el problema

Servidor solo IPv4 (como los de las clases 13 y 14):

```python
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind(('0.0.0.0', 8080))
s.listen(5)
```

1. Conectate con un cliente IPv4 (`127.0.0.1`). Funciona.
2. Conectate con un cliente IPv6 (`::1`). ¿Qué pasa? ¿Por qué?

### Parte B: dual-stack

```python
s = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
# TODO: poner IPV6_V6ONLY en 0
s.bind(('::', 8080))
s.listen(5)
```

3. Completá el `setsockopt` que falta. Conectate desde las dos familias.
4. ¿Qué dirección ve el servidor cuando conecta el cliente IPv4? Anotala exactamente.
5. ¿Qué prefijo tiene? ¿Cómo se llaman esas direcciones?

### Parte C: V6ONLY

6. Poné `IPV6_V6ONLY` en **1** y repetí. ¿Qué pasa con el cliente IPv4?
7. Consultá el default de tu sistema:

```bash
cat /proc/sys/net/ipv6/bindv6only
```

8. ¿Por qué conviene poner la opción explícitamente aunque el default te sirva? Pensá en un compañero con otro sistema operativo.

### Parte D: normalizar

Tu servidor loguea la IP de cada cliente. Con dual-stack, el mismo cliente IPv4 aparece como `::ffff:127.0.0.1`.

9. Escribí una función que normalice:

```python
import ipaddress

def normalizar(host):
    """::ffff:1.2.3.4 -> 1.2.3.4; el resto queda igual.
    PISTA: ipaddress tiene un atributo ipv4_mapped."""
    # TODO
```

10. ¿Por qué importa esto si tu servidor tuviera una lista de IPs bloqueadas?

### Parte E: cliente agnóstico

11. Escribí un cliente que use `getaddrinfo()` y pruebe todas las direcciones hasta que una funcione:

```python
def conectar(host, puerto, timeout=5):
    for familia, tipo, proto, _, direccion in socket.getaddrinfo(
            host, puerto, type=socket.SOCK_STREAM):
        # TODO: intentar, y si falla seguir con la próxima
```

12. Probalo contra `localhost`. ¿En qué orden vinieron las direcciones?
13. Corré `python3 explorar_ipv6.py resolver google.com`. ¿Puso IPv6 o IPv4 primero? Si no tenés ruta IPv6, el sistema lo detecta y reordena: verificalo.
14. ¿Por qué es un error elegir la primera dirección y no reintentar con las demás?

### Verificación

Compará tu solución con `dual_stack.py` y corré `python3 dual_stack.py demo`.

---

## Ejercicio 4: getaddrinfo en detalle

```python
import socket
for info in socket.getaddrinfo('google.com', 'http', type=socket.SOCK_STREAM):
    print(info)
```

1. Pasé `'http'` en vez de `80`. ¿Funciona? ¿De dónde saca el número?
2. Mirá `/etc/services`. Buscá tres servicios que conozcas.
3. Filtrá por familia con `socket.getaddrinfo(host, 80, socket.AF_INET6)`. ¿Cuántos resultados da?
4. ¿Qué pasa con un nombre que no existe? ¿Qué excepción?
5. Usá `socket.AF_UNSPEC` explícitamente. ¿Cambia algo respecto de no pasar familia?

---

## Ejercicio 5: UDP sobre IPv6

Todo lo de la clase 15 vale igual, cambiando la familia.

1. Adaptá `echo_udp.py` de la clase anterior para que use `AF_INET6` y `::1`.
2. ¿Cambió algo además de la familia y la dirección?
3. ¿Qué tamaño tiene la tupla que devuelve `recvfrom()` ahora? Comparalo con IPv4.
4. En las manijas de la clase 15 dijimos que el checksum UDP es opcional en IPv4 y obligatorio en IPv6. Buscá por qué: ¿qué eliminó IPv6 del encabezado de red que hace necesario el cambio?

---

## Ejercicio 6: Diferencias del protocolo

1. El encabezado IPv6 es de tamaño fijo (40 bytes) y el de IPv4 variable. ¿Qué ventaja tiene para un router?
2. IPv6 eliminó el checksum de la capa de red. ¿Por qué se podía dar ese lujo?
3. En IPv6 los routers **no fragmentan**: solo el emisor. ¿Qué implica para el path MTU discovery que vimos en la clase 15?
4. El MTU mínimo de IPv6 es 1280 bytes contra 576 de IPv4. ¿Por qué subieron el piso?
5. Investigá qué pasa si un firewall bloquea ICMPv6 completo. ¿Por qué es más grave que bloquear ICMP en IPv4? Nombrá dos funciones que dejarían de andar.

---

## Verificación del ejercicio obligatorio

### Ejercicio 3: Servidor dual-stack

- [ ] Servidor IPv6 con `IPV6_V6ONLY` explícito en 0
- [ ] Atiende clientes IPv4 e IPv6 con un solo socket
- [ ] Identificás la dirección mapeada `::ffff:` en el log
- [ ] Función de normalización que la convierte a IPv4 plana
- [ ] Probaste con `V6ONLY=1` y sabés qué cambia
- [ ] Cliente con `getaddrinfo()` que reintenta con todas las direcciones
- [ ] Explicar por qué no alcanza con probar solo la primera

---

## Ejercicios adicionales

### Migrar el servidor de la clase 14

Tomá `server_threads.py` de la clase anterior y hacelo dual-stack. ¿Cuántas líneas hubo que cambiar?

### Escáner de vecinos link-local

Usando la tabla de vecinos (`ip -6 neigh`), listá los dispositivos IPv6 de tu red local. Compará con `ping6 ff02::1%<interfaz>`, que hace ping a todos los nodos del enlace.

### Comparar encabezados

Capturá tráfico IPv4 e IPv6 con `tcpdump -i lo -n ip6` y `-n ip`, y compará el tamaño de los encabezados en la práctica.

### Servidor que reporta la familia

Servidor que responde al cliente diciéndole por qué familia llegó y con qué dirección lo ve. Útil para diagnosticar problemas de conectividad dual.

---

*Computación II - 2026 - Clase 16*
