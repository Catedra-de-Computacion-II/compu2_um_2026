# Clase 16: Direccionamiento IPv4 e I/O Multiplexing - Ejercicios Prácticos

Los archivos `servidor_select.py`, `servidor_selectors.py`, `chat.py` y `comparar.py` acompañan la clase. Empezá corriéndolos para ver el comportamiento esperado.

Casi todos los ejercicios necesitan **dos o tres terminales**.

---

## Ejercicio 0: Direccionamiento IPv4

Repaso previo. Usá `ipaddress` en vez de calcular máscaras a mano.

### 0.1 Leer un prefijo

```python
import ipaddress
red = ipaddress.ip_network('192.168.1.0/24')
```

1. ¿Cuántas direcciones tiene? ¿Cuántos hosts usables? ¿Por qué la diferencia es 2?
2. ¿Cuál es la máscara en notación decimal? ¿Y la dirección de broadcast?
3. Repetí con `/16`, `/26` y `/30`. Completá una tabla de prefijo, direcciones y hosts.
4. ¿Cuál es más grande, un `/24` o un `/30`? Explicá por qué la intuición engaña.

### 0.2 Misma red o no

```python
red = ipaddress.ip_network('192.168.1.0/24')
print(ipaddress.ip_address('192.168.1.37') in red)
print(ipaddress.ip_address('192.168.2.10') in red)
```

5. ¿Qué hace tu sistema distinto en cada caso al mandar un paquete?
6. Dos máquinas, `10.0.0.5/24` y `10.0.1.7/24`, conectadas al mismo switch. ¿Se ven? ¿Por qué?
7. ¿Qué habría que cambiar para que se vean, sin tocar el cableado?

### 0.3 Tu propia red

```bash
ip -4 addr show
ip route
```

8. ¿Cuál es tu dirección y tu prefijo? ¿Cuántas máquinas entran en tu red?
9. ¿Cuál es tu gateway? Verificá con `ipaddress` que está dentro de tu misma red.
10. Si tenés Docker, mirá `docker0`. ¿Qué red usa? ¿Cuántos contenedores podrían convivir ahí?

### 0.4 Dividir

11. Partí `192.168.1.0/24` en cuatro subredes iguales. ¿Qué prefijo tienen? ¿Cuántos hosts cada una?

```python
for sub in ipaddress.ip_network('192.168.1.0/24').subnets(new_prefix=26):
    print(sub)
```

12. Necesitás una subred para 100 hosts. ¿Qué prefijo es el más chico que alcanza? ¿Cuántas direcciones desperdiciás?

---

## Ejercicio 1: Ver el problema antes de la solución

### 1.1 Busy-waiting

Escribí un servidor que atienda dos clientes con sockets no bloqueantes, **sin** usar `select`:

```python
#!/usr/bin/env python3
"""Servidor con polling activo. Funciona, pero mal."""
import socket

srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
srv.bind(('localhost', 8080)); srv.listen(5)
srv.setblocking(False)

conexiones = []
while True:
    try:
        conn, _ = srv.accept()
        conn.setblocking(False)
        conexiones.append(conn)
    except BlockingIOError:
        pass
    for c in list(conexiones):
        try:
            datos = c.recv(4096)
            if datos: c.sendall(datos)
            else: conexiones.remove(c); c.close()
        except BlockingIOError:
            pass
```

1. Corrélo y conectate con `nc`. ¿Funciona?
2. Mirá el consumo de CPU con `top` o `htop` mientras **no hay nadie conectado**. ¿Qué porcentaje usa?
3. ¿Por qué consume tanto si no está haciendo nada?
4. Ahora corré `servidor_select.py` y mirá el consumo con el mismo criterio. ¿Cuál es la diferencia?

### 1.2 El bloqueo

5. En un servidor secuencial de la clase 13, ¿qué pasaba si el primer cliente no mandaba nada? Explicá por qué `select()` resuelve eso sin threads.

---

## Ejercicio 2: select() en detalle

### 2.1 El servidor eco

```bash
python3 servidor_select.py
```

Conectate con tres `nc` en terminales distintas.

1. ¿Cuántos hilos tiene el proceso? Verificalo: `ls /proc/$(pgrep -f servidor_select)/task | wc -l`
2. Escribí en el tercer cliente sin tocar los otros dos. ¿Responde? ¿Por qué no hay que esperar a los demás?
3. Matá un cliente con Ctrl+C. ¿Qué imprime el servidor? Buscá en el código qué línea lo detecta.

### 2.2 El bug de no remover

Comentá la línea `vigilados.remove(sock)` en `servidor_select.py`.

4. Conectate, escribí algo, y cerrá el cliente. ¿Qué pasa con el servidor?
5. Mirá el consumo de CPU. Explicá por qué gira infinitamente. (Pista: ¿qué reporta `select()` sobre un fd cerrado?)
6. Restaurá la línea.

### 2.3 El límite de FD_SETSIZE

```python
import select, socket
relleno = [socket.socket() for _ in range(1100)]
alto = relleno[-1]
print("fd:", alto.fileno())
select.select([alto], [], [], 0)
```

7. ¿Qué error da? Notá que estás vigilando **un solo** socket.
8. Entonces, ¿cuál es exactamente el límite de `select()`: la cantidad de descriptores o el número de cada uno?
9. Repetí lo mismo con `select.poll()`. ¿Falla?
10. ¿Por qué este bug es difícil de encontrar en desarrollo y aparece en producción?

---

## Ejercicio 3: Comparar los tres (obligatorio)

### Objetivo

Medir empíricamente por qué existe `epoll`, y saber interpretar los números.

### Parte A: correr el benchmark

```bash
python3 comparar.py
```

1. Copiá la tabla que te dio en tu máquina.
2. ¿Cómo crece el tiempo de `poll()` entre 100 y 5000 conexiones? Calculá el factor.
3. ¿Cómo crece el de `epoll()`? Compará los dos comportamientos.
4. ¿A partir de qué cantidad falla `select()`? ¿Coincide con lo del ejercicio 2.3?

### Parte B: entender el porqué

5. En el benchmark, solo 3 sockets tienen datos y el resto está ocioso. ¿Por qué esa proporción es realista en un servidor web?
6. Explicá con tus palabras por qué `poll()` es O(n) y `epoll` es O(listos). ¿Qué hace distinto cada uno?
7. Cambiá `ACTIVOS` a un número alto (por ejemplo, la mitad de las conexiones) y volvé a correr. ¿Se achica la ventaja de `epoll`? ¿Por qué?

### Parte C: el caso donde no importa

8. Corré `comparar.py 10 50 100`. Con esas cantidades, ¿vale la pena `epoll`?
9. Entonces, ¿cuándo NO tiene sentido complicarse con multiplexing? Relacionalo con la tabla de la clase 14.

### Parte D: escribirlo

10. Escribí una conclusión de un párrafo, con tus números, que responda: *¿por qué nginx puede atender más conexiones que un Apache con un thread por cliente?*

---

## Ejercicio 4: De select a selectors

Tomá `servidor_select.py` y reescribilo con `selectors`.

1. ¿Qué desaparece del código? (Pensá en la lista `vigilados` y en el diccionario de direcciones.)
2. ¿Qué implementación eligió `DefaultSelector` en tu máquina?

```python
import selectors
print(type(selectors.DefaultSelector()).__name__)
```

3. Forzá el uso de `SelectSelector` en vez del default:

```python
sel = selectors.SelectSelector()
```

¿Cambia el comportamiento con pocos clientes? ¿Y el límite de fds?

4. En `servidor_selectors.py`, ¿qué pasa si sacás el `sel.unregister(conn)` antes del `close()`? Probalo y describí el síntoma.

---

## Ejercicio 5: Escritura no bloqueante

En `servidor_selectors.py`, mirá la función `escribir()`.

1. ¿Por qué usa `send()` y no `sendall()`? Relacionalo con lo que dijimos en la clase 13, donde la recomendación era la opuesta.
2. ¿Qué pasaría si registráramos `EVENT_WRITE` permanentemente, en vez de solo cuando hay datos pendientes? Probalo y mirá el CPU.
3. Un cliente lento no lee lo que le mandamos y su buffer se llena. Con `sendall()`, ¿qué les pasa a los otros 999 clientes? ¿Y con el esquema de buffer + `EVENT_WRITE`?
4. ¿Dónde crece la memoria si un cliente nunca lee? ¿Qué habría que agregar para protegerse?

---

## Ejercicio 6: Chat multiusuario

```bash
python3 chat.py
```

Conectate con tres `nc` y escribí desde varios.

1. Cuando A manda un mensaje, el servidor escribe en los sockets de B y C. ¿Por qué eso **no** necesita un lock, si con threads sí lo necesitaría?
2. En `difundir()`, el mensaje se **encola** en vez de enviarse directo. ¿Qué problema evita eso?
3. Agregale el comando `/nick <nombre>` para cambiar el apodo.
4. Agregale `/lista` que devuelva quiénes están conectados.
5. **Framing**: el chat asume que cada `recv()` trae una línea completa. ¿Es cierto? Relacionalo con la clase 13 y describí en qué caso se rompe.
6. Arreglá el framing usando un buffer por cliente, como en `framing.py` de la clase 13.

---

## Ejercicio 7: El costo del hilo único

Agregá un trabajo pesado al handler de `servidor_selectors.py`:

```python
def atender(conn):
    datos = conn.recv(4096)
    if datos:
        import hashlib
        h = datos
        for _ in range(3_000_000):        # ~2 segundos de CPU
            h = hashlib.sha256(h).digest()
        conn.sendall(h.hex().encode())
```

1. Conectate con dos clientes y mandá algo desde el primero. Mientras procesa, ¿responde el segundo?
2. Comparalo con el `server_threads.py` de la clase 14: ¿pasa lo mismo?
3. Enunciá la regla que se desprende de esto.
4. ¿Cómo lo resolverías sin abandonar el modelo de event loop? (Pista: la respuesta reaparece en el TP2.)

---

## Verificación del ejercicio obligatorio

### Ejercicio 3: Comparar los tres

- [ ] Tabla con los números de tu máquina
- [ ] Factor de crecimiento de `poll` calculado
- [ ] Comportamiento de `epoll` descrito y explicado
- [ ] Punto donde falla `select`, y por qué (valor del fd, no cantidad)
- [ ] Explicación de O(n) contra O(listos)
- [ ] Prueba con `ACTIVOS` alto y su interpretación
- [ ] Conclusión escrita sobre nginx contra Apache

---

## Ejercicios adicionales

### Servidor con timeout

Agregale a `servidor_selectors.py` un timeout de inactividad: desconectar clientes que no mandan nada en 30 segundos. Pista: `sel.select(timeout=...)` devuelve una lista vacía cuando vence.

### Proxy TCP

Con `selectors`, escribí un proxy que reenvíe todo lo que llega al puerto 8080 hacia otro host y puerto, en ambos sentidos. Es un buen ejercicio de vigilar dos sockets relacionados.

### Medir el techo real

Levantá `servidor_selectors.py` y abrí conexiones hasta que algo falle. ¿Cuántas aguanta? Compará con el `ulimit -n` de tu sistema y con lo que medía la clase 14 para threads.

### El self-pipe otra vez

En la clase 6 vimos el patrón self-pipe para señales. Integralo con `selectors`: registrá el extremo de lectura del pipe y manejá `SIGINT` como un evento más del bucle, en vez de con un handler que interrumpe.

---

*Computación II - 2026 - Clase 16*
