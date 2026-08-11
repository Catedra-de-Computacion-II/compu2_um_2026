# Clase 12: Redes - Ejercicios Prácticos

Los ejercicios de esta clase se hacen casi todos en la terminal. La idea es observar la red antes de programarla.

Antes de empezar, instalá las herramientas:

```bash
sudo apt install iproute2 dnsutils netcat-openbsd traceroute tcpdump
```

Verificá que `nc -h` diga "OpenBSD netcat": hay otras versiones con banderas distintas.

---

## Ejercicio 1: Reconocimiento de tu propia máquina

### 1.1 Interfaces y direcciones

```bash
ip addr show
```

Respondé:

1. ¿Cuántas interfaces de red tenés? Identificá la de loopback.
2. ¿Cuál es tu IP en la red local? ¿Es una dirección privada? (`192.168.x.x`, `10.x.x.x` o `172.16-31.x.x`)
3. ¿Tenés dirección IPv6? ¿Empieza con `fe80:`? Esa es link-local: solo vale en tu red física.

### 1.2 Rutas

```bash
ip route
```

4. ¿Cuál es tu gateway por defecto (la línea que empieza con `default`)?
5. ¿Qué relación hay entre esa dirección y tu propia IP?

### 1.3 Puertos en escucha

```bash
ss -tlnp
```

6. Listá tres servicios escuchando en tu máquina con su puerto.
7. ¿Cuáles escuchan en `127.0.0.1` y cuáles en `0.0.0.0` o `*`? ¿Qué implica la diferencia para alguien en tu misma red wifi?

---

## Ejercicio 2: Resolución de nombres

```bash
dig www.um.edu.ar
```

1. ¿Qué dirección IP devuelve? Buscá la sección `ANSWER SECTION`.
2. ¿Cuál es el TTL? ¿Qué significa ese número?
3. Corré el mismo comando de nuevo enseguida. ¿Bajó el TTL? ¿Por qué?

Probá con un sitio grande:

```bash
dig google.com +short
```

4. ¿Cuántas direcciones devuelve? ¿Para qué sirve tener varias?

Compará el tiempo de resolución con y sin cache:

```bash
dig google.com | grep "Query time"
dig google.com | grep "Query time"
```

5. ¿Cambió? ¿Quién está cacheando?

---

## Ejercicio 3: Cliente y servidor con netcat

### 3.1 Conversación básica

En una terminal:

```bash
nc -l 8080
```

En otra:

```bash
nc localhost 8080
```

Escribí en cualquiera de las dos y presioná Enter. El texto aparece en la otra.

1. ¿Qué pasa si cerrás el cliente con Ctrl+C? ¿Y si cerrás el servidor?
2. Mientras la conexión está abierta, corré `ss -tnp | grep 8080` en una tercera terminal. Identificá los cuatro valores de la cuádrupla.
3. Levantá el servidor de nuevo e intentá conectar dos clientes a la vez. ¿Funciona? ¿Por qué?

### 3.2 El puerto ocupado

Con el servidor corriendo, abrí otro `nc -l 8080` en otra terminal.

4. ¿Qué error da? Ese error (`Address already in use`) lo vas a ver mucho en la clase que viene.

### 3.3 Loopback contra todas las interfaces

```bash
nc -l 127.0.0.1 8080      # solo loopback
```

Desde la misma máquina funciona. Si tenés otra máquina en la misma red (o una VM), probá conectarte desde ahí: no vas a poder.

Ahora:

```bash
nc -l 0.0.0.0 8080        # todas las interfaces
```

5. Ahora sí se puede desde afuera. Explicá en una oración por qué un servidor de desarrollo suele escuchar en `127.0.0.1`.

---

## Ejercicio 4: HTTP a mano

Vas a hacer manualmente lo que hace el navegador.

```bash
printf 'GET / HTTP/1.1\r\nHost: example.com\r\nConnection: close\r\n\r\n' | nc example.com 80
```

1. ¿Qué código de estado devuelve la primera línea?
2. Identificá tres headers de la respuesta y explicá qué dice cada uno.
3. Sacá el header `Host:` de la petición y probá de nuevo. ¿Qué cambia? ¿Por qué HTTP/1.1 lo exige?
4. Cambiá `GET /` por `GET /noexiste`. ¿Qué código devuelve?

### Sobre los finales de línea

5. Probá con `\n` en lugar de `\r\n`:

```bash
printf 'GET / HTTP/1.1\nHost: example.com\nConnection: close\n\n' | nc example.com 80
```

¿Funciona? Los servidores varían: algunos son tolerantes y otros no. ¿Por qué es mala idea depender de esa tolerancia?

---

## Ejercicio 5: Observar el handshake

Este ejercicio necesita `tcpdump` y privilegios de root.

En una terminal, capturá el tráfico de loopback:

```bash
sudo tcpdump -i lo -n port 8080
```

En otra, levantá un servidor y conectate:

```bash
nc -l 8080
```

```bash
echo "test" | nc localhost 8080
```

1. Identificá en la captura los tres paquetes del handshake. Buscá las banderas `[S]`, `[S.]` y `[.]`.
2. ¿Cuántos paquetes se intercambian en total para mandar la palabra "test"? Compará con el tamaño del dato real.
3. Identificá el cierre. ¿Qué banderas aparecen? (`[F]` es FIN)

Si no podés usar `tcpdump`, dibujá el diagrama de secuencia que esperarías ver y verificá contra el diagrama del contenido.

---

## Ejercicio 6: TCP es un flujo (obligatorio)

### Objetivo

Comprobar empíricamente que TCP no preserva los límites de los mensajes.

### Parte A: observar el problema

Servidor:

```bash
nc -l 8080 | od -c
```

Cliente, mandando tres "mensajes" rápido:

```bash
python3 -c "
import socket
s = socket.create_connection(('localhost', 8080))
s.send(b'HOLA')
s.send(b'COMO')
s.send(b'ESTAS')
s.close()
"
```

1. ¿Cómo llegaron los datos al servidor? ¿Se distinguen los tres envíos?
2. Ahora agregá una pausa entre los envíos:

```python
import socket, time
s = socket.create_connection(('localhost', 8080))
for msg in [b'HOLA', b'COMO', b'ESTAS']:
    s.send(msg)
    time.sleep(1)
s.close()
```

¿Cambió algo? ¿Podés confiar en ese comportamiento?

### Parte B: la pregunta

3. Si los tres envíos llegan juntos, ¿es un bug de TCP? Justificá con lo que dice el contenido sobre el contrato de TCP.
4. Proponé dos formas de delimitar mensajes sobre un flujo de bytes. Para cada una, decí qué pasa si un mensaje contiene el delimitador.

### Parte C: UDP para contrastar

Acá usamos un receptor en Python en vez de `nc -u`, porque necesitamos ver cada `recvfrom` por separado.

Servidor (`udp_srv.py`):

```python
#!/usr/bin/env python3
"""Receptor UDP: imprime cada datagrama que llega."""
import socket

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.bind(('localhost', 8080))
s.settimeout(5)

print("Esperando datagramas (5s de timeout)...")
try:
    while True:
        datos, origen = s.recvfrom(4096)
        print(f"recv: {datos!r} de {origen}")
except socket.timeout:
    print("(timeout, fin)")
```

Cliente:

```bash
python3 -c "
import socket
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
for msg in [b'HOLA', b'COMO', b'ESTAS']:
    s.sendto(msg, ('localhost', 8080))
"
```

5. ¿Cuántas veces se ejecutó el `recvfrom`? Compará con lo que pasó en TCP.
6. ¿Por qué UDP preserva los límites y TCP no? Relacionalo con lo que garantiza cada protocolo.
7. Notá que el servidor UDP no hace `listen()` ni `accept()`. ¿Por qué no le hacen falta?

---

## Ejercicio 7: Puertos efímeros

```bash
cat /proc/sys/net/ipv4/ip_local_port_range
```

1. ¿Cuál es el rango de puertos efímeros de tu sistema? Compará con el rango 49152-65535 que define IANA: en Linux **no** coinciden. Buscá por qué Linux usa un rango propio y qué implica que el estándar sea una recomendación y no una imposición.

Abrí varias conexiones a la vez y observá los puertos de origen:

```bash
python3 -c "
import socket
conns = [socket.create_connection(('example.com', 80)) for _ in range(5)]
for c in conns:
    print(c.getsockname())
input('Enter para cerrar...')
"
```

2. ¿Qué puertos de origen se asignaron? ¿Están dentro del rango que viste en el punto 1? ¿Siguen algún patrón?
3. Mirá bien la salida de `getsockname()`. Si tu conexión salió por IPv6, la tupla tiene **cuatro** elementos en vez de dos (los dos extra son flowinfo y scope id). ¿Cuál es tu caso? Forzá el otro con `socket.AF_INET` o `socket.AF_INET6` y compará.
4. Con esas conexiones abiertas, corré `ss -tn state established` en otra terminal. Verificá que cada conexión tiene su cuádrupla única.
5. Sabiendo el tamaño del rango efímero: ¿cuántas conexiones simultáneas puede abrir tu máquina **hacia el mismo servidor y puerto**? ¿Y hacia servidores distintos? Esta es la razón por la que un balanceador de carga puede quedarse sin puertos.

---

## Verificación del ejercicio obligatorio

### Ejercicio 6: TCP es un flujo

Tenés que poder responder:

- [ ] Mostrar una corrida donde los tres envíos llegan agrupados
- [ ] Explicar por qué eso no viola el contrato de TCP
- [ ] Explicar por qué agregar `sleep` no es una solución
- [ ] Proponer dos esquemas de delimitación y sus problemas
- [ ] Mostrar que UDP preserva los límites
- [ ] Explicar a qué se debe la diferencia

---

## Ejercicios adicionales

### Escaneo de puertos propio

Usando `nc -z`, escribí un script que pruebe qué puertos del 1 al 1024 están abiertos en `localhost`. Compará el resultado con `ss -tlnp`.

> Hacelo solo contra tu propia máquina. Escanear puertos de sistemas ajenos sin autorización es, además de descortés, ilegal en muchas jurisdicciones.

### Servidor de archivos improvisado

Con `nc`, transferí un archivo de una terminal a otra. Verificá con `md5sum` que llegó íntegro.

### Medir el costo del handshake

Escribí un script que mida cuánto tarda `socket.create_connection()` hacia un servidor local y hacia uno remoto. ¿De dónde sale la diferencia?

---

*Computación II - 2026 - Clase 12*
