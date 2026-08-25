# Clase 15: UDP - Ejercicios Prácticos

Los archivos `echo_udp.py`, `perdidas.py` y `confiable.py` acompañan la clase. Corrélos antes de empezar para ver el comportamiento esperado.

---

## Ejercicio 1: Primer contacto con datagramas

### 1.1 Servidor y cliente

Terminal 1:

```bash
python3 echo_udp.py servidor 8080
```

Terminal 2:

```bash
python3 echo_udp.py cliente 8080 "hola profe"
```

1. Mirá la salida del servidor. ¿Qué información devuelve `recvfrom()` además de los datos?
2. Corré el cliente tres veces seguidas. ¿Cambia el puerto efímero cada vez? ¿Por qué?
3. Matá el servidor y corré el cliente. ¿Qué pasa? ¿Cuánto tarda en darse cuenta?
4. Sacá el `settimeout(2.0)` del cliente y repetí el punto anterior. ¿Cuánto espera ahora? Cortá con Ctrl+C.

### 1.2 Contra netcat

```bash
nc -u -l 8080
```

5. Conectate con `python3 echo_udp.py cliente 8080`. ¿Recibe el `nc` el mensaje?
6. Escribí una respuesta en la terminal del `nc`. ¿Le llega al cliente?

### 1.3 Sin listen ni accept

7. Compará `echo_udp.py` con `echo_server.py` de la clase 13. ¿Qué llamadas desaparecieron?
8. ¿Por qué un servidor UDP no necesita un socket por cliente? Relacionalo con la cuádrupla de la clase 12.
9. Levantá el servidor y mandale datagramas desde **dos** clientes distintos a la vez. ¿Los atiende a los dos? ¿Hizo falta concurrencia?

El punto 9 es importante: todo el problema de la clase 14 —un cliente bloqueando a los demás— aquí casi no existe. Pensá por qué.

---

## Ejercicio 2: Los límites del datagrama

### 2.1 Se preservan

```bash
python3 echo_udp.py tres 8080
```

1. Tres `sendto()` produjeron ¿cuántos `recvfrom()` en el servidor? Copiá las líneas del log.
2. Compará con lo que pasaba en la clase 13 con TCP. ¿Por qué la diferencia?

### 2.2 El buffer chico trunca (importante)

```python
#!/usr/bin/env python3
import socket

r = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
r.bind(('localhost', 8081))

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.sendto(b'X' * 100, ('localhost', 8081))

datos, _ = r.recvfrom(10)          # buffer de 10 para un datagrama de 100
print(f'primer recvfrom: {len(datos)} bytes')

r.settimeout(1.0)
try:
    datos2, _ = r.recvfrom(65535)
    print(f'segundo recvfrom: {len(datos2)} bytes')
except TimeoutError:
    print('segundo recvfrom: nada')
```

3. ¿Cuántos bytes trajo el primer `recvfrom()`? ¿Y el segundo?
4. ¿Dónde quedaron los 90 bytes restantes?
5. En TCP, ¿qué habría pasado con esos 90 bytes? Explicá la diferencia de fondo.
6. ¿Qué tamaño de buffer conviene usar siempre, y por qué?

---

## Ejercicio 3: Protocolo confiable (obligatorio)

### Objetivo

Implementar sobre UDP las garantías que TCP daba gratis, y medir cuánto cuesta.

### Parte A: ver el problema

```bash
python3 perdidas.py 0.3
```

1. De 200 datagramas enviados, ¿cuántos llegaron?
2. ¿Qué error recibió el emisor por los que se perdieron? Mirá la última línea de la salida.
3. Esa es la característica central de UDP. Enunciala en una frase.

**Pérdidas y desorden reales.** El simulador solo pierde; la red real además reordena. Con `tc` podés verlo (viene en `iproute2`, ya instalado en casi cualquier Linux; si `which tc` falla, probá `/sbin/tc -V`):

```bash
sudo tc qdisc add dev lo root netem loss 20% reorder 25% 50%
python3 perdidas.py 0        # sin pérdida simulada: la pierde la red de verdad
sudo tc qdisc del dev lo root
```

3b. Mirá la línea "Saltos hacia atrás en el orden de llegada". Sin `tc` da 0, porque loopback entrega en orden. ¿Cuánto da ahora? ¿Qué implica para un protocolo que asuma que los mensajes llegan ordenados?

### Parte B: retransmisión

Implementá un cliente que reintente hasta obtener respuesta:

```python
def pedir_con_reintentos(sock, mensaje, destino, intentos=5, timeout=0.5):
    """Manda y reintenta si no llega respuesta.
    PISTA: settimeout() + capturar TimeoutError en un bucle."""
    # TODO
```

4. Probalo contra un servidor eco con pérdidas simuladas. ¿Cuántos intentos necesita en promedio?
5. Subí la probabilidad de pérdida a 0.7. ¿Sigue funcionando? ¿Cuántos intentos?
6. ¿Qué pasa si el timeout es muy corto? ¿Y muy largo? Probá con 0.01 y con 5.0.

### Parte C: el problema del duplicado

Acá está lo interesante. Con solo reintentar hay un bug grave.

7. Si el cliente no recibe respuesta, ¿cómo sabe si se perdió **su pedido** o **la respuesta del servidor**?
8. En el segundo caso, el servidor ya procesó el pedido. Al reintentar, lo procesa de nuevo. Escribí un servidor que cuente cuántas veces ejecuta el trabajo real, y comprobá que con reintentos lo hace de más.
9. ¿Por qué esto es grave si el pedido fuera "transferir $100" y no "poner en mayúsculas"?

### Parte D: números de secuencia

Agregá un número de secuencia de 4 bytes antes del payload:

```python
import struct

def empaquetar(seq, payload):
    return struct.pack('!I', seq) + payload      # '!' = orden de red

def desempaquetar(datos):
    (seq,) = struct.unpack('!I', datos[:4])
    return seq, datos[4:]
```

10. Del lado del servidor, guardá los `seq` ya vistos y, si llega un duplicado, **reenviá la respuesta guardada sin volver a hacer el trabajo**. Verificá que el contador del punto 8 ahora coincida con la cantidad real de mensajes.
11. Del lado del cliente, descartá respuestas cuyo `seq` no coincida con el pedido en curso. ¿Por qué hace falta? Pensá en una respuesta demorada de un intento anterior.
12. Compará tu solución con `confiable.py`. Corrélo con `0.6` y mirá la diferencia entre "envíos reales" y "veces que el servidor hizo trabajo".

### Parte E: reflexión

13. Enumerá tres garantías de TCP que tu implementación **todavía no** tiene.
14. ¿En qué momento conviene dejar de agregar confiabilidad sobre UDP y simplemente usar TCP?

---

## Ejercicio 4: connect() en UDP

```python
import socket

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.settimeout(2)
s.connect(('localhost', 9999))     # puerto donde no hay nadie
s.send(b'hola')
try:
    s.recv(4096)
except ConnectionRefusedError:
    print('ConnectionRefusedError')
except TimeoutError:
    print('timeout')
```

1. ¿Qué excepción da? ¿De dónde sale esa información, si UDP no tiene conexión?
2. Sacá el `connect()` y usá `sendto()` / `recvfrom()` contra el mismo puerto vacío. ¿Qué pasa ahora?
3. ¿Por qué la diferencia? ¿Qué hace realmente `connect()` en un socket UDP?
4. Investigá: con `connect()`, ¿qué pasa si otro host te manda un datagrama? Probalo desde otra máquina o con dos puertos locales.
5. ¿Por qué no conviene depender de este mecanismo en Internet?

---

## Ejercicio 5: Broadcast

```python
import socket

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
s.settimeout(2.0)
s.sendto(b'DISCOVER?', ('255.255.255.255', 8082))
try:
    datos, origen = s.recvfrom(4096)
    print(f'{origen} respondió: {datos!r}')
except TimeoutError:
    print('Nadie respondió')
```

1. Sacá la línea del `setsockopt`. ¿Qué error da? ¿Por qué existe esa protección?
2. Escribí el servidor que responde al `DISCOVER?` con el nombre de la máquina.
3. Probalo con un compañero en la misma red. ¿Funciona? ¿Y si están en redes distintas?
4. ¿Por qué los routers no reenvían broadcast?
5. DHCP usa broadcast para que una máquina sin IP encuentre un servidor. Explicá por qué no podría usar TCP.

---

## Ejercicio 6: Fragmentación y MTU

1. Averiguá el MTU de tu interfaz:

```bash
ip link show | grep mtu
```

2. Calculá cuántos bytes de payload UDP entran sin fragmentar. (Restá 20 de IP y 8 de UDP.)
3. Mandá un datagrama de 60000 bytes a un servidor local. ¿Llega?
4. Mandá el mismo datagrama con `tc netem loss 5%` activo. Repetí 20 veces y contá cuántos llegan completos.
5. Compará con datagramas de 1000 bytes bajo la misma pérdida. ¿Por qué la diferencia es mayor que 5%?

El punto 5 es el que importa: explicá con números por qué fragmentar multiplica la probabilidad de perder el datagrama entero.

---

## Verificación del ejercicio obligatorio

### Ejercicio 3: Protocolo confiable

- [ ] Cliente que reintenta con timeout
- [ ] Funciona con 70% de pérdida simulada
- [ ] Servidor que cuenta cuántas veces hace el trabajo real
- [ ] Demostrar que sin deduplicación el servidor procesa de más
- [ ] Números de secuencia implementados con `struct.pack('!I', ...)`
- [ ] Servidor que deduplica y reenvía la respuesta guardada
- [ ] Cliente que descarta respuestas con `seq` incorrecto
- [ ] Explicar tres garantías de TCP que tu implementación no tiene

---

## Ejercicios adicionales

### Servidor de tiempo (estilo RFC 868)

Servidor UDP que responde con la hora actual en segundos desde epoch, empaquetada con `struct.pack('!I', ...)`. Cliente que lo consulta y calcula el desfasaje con su propio reloj.

### Chat multicast

Varios clientes se unen al mismo grupo multicast y lo que escribe uno lo ven todos. Compará el tráfico de red contra hacer lo mismo con N conexiones TCP.

### Medidor de pérdida y jitter

Cliente que manda 1000 datagramas numerados a intervalos fijos y servidor que reporta: cuántos se perdieron, cuántos llegaron desordenados, y la variación de tiempo entre llegadas (jitter). Es, en miniatura, lo que hace una herramienta como `iperf`.

### Traceroute casero

`traceroute` clásico manda datagramas UDP con TTL creciente y escucha los ICMP *time exceeded*. Implementalo con `setsockopt(IPPROTO_IP, IP_TTL, n)` y un socket raw para el ICMP. Necesita privilegios.

---

*Computación II - 2026 - Clase 15*
