# Clase 13: Sockets TCP - Ejercicios Prácticos

Casi todos los ejercicios necesitan **dos terminales**: una para el servidor y otra para el cliente.

Los archivos `echo_server.py`, `echo_client.py` y `framing.py` acompañan la clase. Empezá corriéndolos para ver el comportamiento esperado antes de escribir código propio.

---

## Ejercicio 1: Primer contacto

### 1.1 Cliente contra netcat

Servidor:

```bash
nc -l 8080
```

Cliente:

```python
#!/usr/bin/env python3
import socket

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect(('localhost', 8080))
    s.sendall(b'hola desde Python\n')
    print(f'Recibido: {s.recv(4096)!r}')
```

1. Corré el cliente. ¿Aparece el mensaje en la terminal del `nc`?
2. Escribí algo en la terminal del `nc` y presioná Enter. ¿Qué imprime el cliente?
3. Sacá la línea del `recv()`. ¿Nota la diferencia el servidor?

### 1.2 Servidor contra netcat

Ahora al revés: escribí un servidor en Python y usá `nc localhost 8080` de cliente.

```python
#!/usr/bin/env python3
import socket

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as srv:
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(('0.0.0.0', 8080))
    srv.listen(5)
    print('Escuchando...')
    conn, dir = srv.accept()
    with conn:
        print(f'Conexión desde {dir}')
        datos = conn.recv(4096)
        conn.sendall(b'ECHO: ' + datos)
```

4. ¿Qué imprime `dir`? Relacionalo con la cuádrupla de la clase 12.
5. El servidor atiende una sola conexión y termina. ¿Qué habría que cambiar para que siga?

### 1.3 SO_REUSEADDR

6. Sacá la línea del `setsockopt`. Corré el servidor, conectate con `nc`, cortá el servidor con Ctrl+C y relanzalo de inmediato. ¿Qué error da?
7. Mientras da ese error, corré `ss -tan state time-wait | head`. ¿Ves el puerto?
8. Volvé a poner la línea. ¿Desaparece el problema?

---

## Ejercicio 2: Entender recv()

### 2.1 Lecturas parciales

Con `echo_server.py` corriendo:

```bash
python3 echo_client.py --parcial
```

1. ¿Cuántas veces se ejecutó el `recv(4)`? ¿Se perdió algún byte?
2. Cambiá el tope a `recv(1)`. ¿Qué pasa? ¿Y con `recv(65536)`?
3. ¿Por qué `recv(65536)` no devuelve necesariamente todo de una vez?

### 2.2 La señal de cierre

```python
#!/usr/bin/env python3
import socket

with socket.create_connection(('localhost', 8080)) as s:
    s.sendall(b'test\n')
    while True:
        datos = s.recv(4096)
        print(f'recv devolvió: {datos!r}')
        # OJO: falta el chequeo de cierre
```

4. Corré esto contra `echo_server.py` y matá el servidor con Ctrl+C. ¿Qué pasa? Cortá con Ctrl+C.
5. Agregá el chequeo que falta. ¿Cuál es?
6. Explicá por qué un `while True` sin ese chequeo consume 100% de CPU.

### 2.3 send() contra sendall()

7. Buscá en la documentación qué devuelve `send()` y qué devuelve `sendall()`.
8. Escribí un cliente que mande 10 MB con `send()` (una sola llamada) e imprima el valor devuelto. ¿Mandó todo?
9. ¿En qué situación `send()` podría ser preferible a `sendall()`?

---

## Ejercicio 3: Framing (obligatorio)

### Objetivo

Implementar las dos estrategias de delimitación de mensajes sobre TCP y comprobar que funcionan cuando el flujo se fusiona o se parte.

### Parte A: el problema

Con `echo_server.py` corriendo en una terminal donde puedas ver su salida:

```bash
python3 echo_client.py --tres
```

1. El cliente hizo tres `sendall()`. ¿Cuántos `recv()` hizo el servidor? Copiá la línea de la salida que lo demuestra.
2. ¿Viola esto el contrato de TCP? Justificá.

### Parte B: framing por delimitador

Implementá un servidor que reciba mensajes terminados en `\n` y responda con el mensaje en mayúsculas, también terminado en `\n`.

```python
#!/usr/bin/env python3
"""Servidor con framing por líneas."""
import socket

def recibir_lineas(sock):
    """Generador de líneas completas.
    PISTA: necesitás un buffer que sobreviva entre llamadas a recv().
    Un recv() puede traer media línea, o tres líneas y media."""
    buffer = b''
    while True:
        pedazo = sock.recv(4096)
        if not pedazo:
            return
        # TODO: acumular en el buffer y entregar TODAS las líneas completas
        # que haya, dejando el resto para la próxima vuelta

# TODO: servidor que use recibir_lineas() y responda en mayúsculas
```

3. Probalo con `nc localhost 8080`, escribiendo varias líneas.
4. Probalo con un cliente que mande `b'uno\ndos\ntres\n'` en un solo `sendall()`. ¿Recibe tres respuestas?
5. Probalo con un cliente que mande la palabra `hola\n` byte por byte, con `time.sleep(0.2)` entre cada uno. ¿Funciona igual?

Los puntos 4 y 5 son los dos casos extremos: todo junto y todo separado. Si tu implementación aguanta los dos, el framing está bien.

### Parte C: framing por longitud

Implementá lo mismo con prefijo de longitud de 4 bytes.

```python
import struct

def recibir_exacto(sock, n):
    """Lee EXACTAMENTE n bytes, o None si cerraron antes.
    PISTA: recv(n) puede devolver menos de n. Hay que insistir."""
    # TODO

def enviar_mensaje(sock, payload: bytes):
    # TODO: struct.pack('!I', len(payload)) + payload

def recibir_mensaje(sock):
    # TODO: leer 4 bytes de cabecera, desempacar, leer esa cantidad
```

6. ¿Por qué `recibir_exacto()` no puede ser simplemente `return sock.recv(n)`?
7. Mandá un mensaje que contenga un `\n` en el medio. ¿Funciona? Probá lo mismo con la versión de la parte B.
8. ¿Qué pasa si mandás un mensaje de 0 bytes? ¿Y uno de 5 GB?

### Parte D: comparación

9. Completá la tabla:

| | Delimitador | Longitud |
|---|---|---|
| Contenido binario arbitrario | | |
| Depurable con `nc` | | |
| Hay que saber el tamaño antes | | |

10. HTTP usa delimitador para los headers y longitud (`Content-Length`) para el cuerpo. ¿Por qué esa combinación?

---

## Ejercicio 4: Bytes y encoding

1. ¿Qué error da esto y por qué?

```python
s.sendall('hola')
```

2. Ejecutá:

```python
>>> 'ñ'.encode('utf-8')
>>> 'año'.encode('utf-8')
>>> len('año'), len('año'.encode('utf-8'))
```

¿Por qué difieren los dos números?

3. Provocá el bug del carácter partido:

```python
datos = 'año'.encode('utf-8')
primera_mitad = datos[:2]
print(primera_mitad.decode('utf-8'))    # ?
```

4. ¿Cómo se evita este problema en un cliente real? (La respuesta tiene que ver con el ejercicio 3.)
5. ¿Cuándo es aceptable usar `errors='replace'`?

---

## Ejercicio 5: Errores y timeouts

### 5.1 Conexión rechazada

1. Sin ningún servidor corriendo, ejecutá un cliente. ¿Qué excepción da?
2. Escribí un cliente con reintentos y backoff que espere a que el servidor aparezca:

```python
def conectar_con_reintentos(host, puerto, intentos=5):
    # TODO: capturar ConnectionRefusedError, esperar, reintentar
    # con espera creciente
```

3. Probalo: lanzá el cliente primero y el servidor unos segundos después.

### 5.2 Timeouts

4. Escribí un cliente que se conecte a `echo_server.py`, no mande nada, e intente `recv()`. ¿Qué pasa?
5. Agregale `s.settimeout(3)`. ¿Qué excepción da ahora?
6. ¿Por qué un cliente sin timeout es peligroso en producción?

### 5.3 Servidor robusto

7. Con `echo_server.py` corriendo, conectate con `nc` y matá el `nc` con Ctrl+C abruptamente. ¿El servidor sobrevive?
8. Mirá el `try/except` de `echo_server.py`. ¿Qué excepciones captura y por qué esas?

---

## Ejercicio 6: El límite del servidor secuencial

Este ejercicio prepara la clase 14.

Modificá `echo_server.py` para que tarde en atender:

```python
def atender(conn, direccion):
    import time
    time.sleep(10)          # simula trabajo pesado
    ...
```

1. Levantá el servidor y conectá dos clientes al mismo tiempo (dos terminales con `nc localhost 8080`). Escribí en el segundo. ¿Responde?
2. ¿Cuánto tarda el segundo cliente en ser atendido?
3. Mientras el primero está siendo atendido, corré `ss -tan sport = :8080 or dport = :8080`. Vas a encontrar algo llamativo: la conexión del segundo cliente aparece como `ESTAB`, no rechazada. ¿Quién completó ese handshake, si el servidor nunca llamó a `accept()` para ese cliente?
4. En la línea `LISTEN` de esa misma salida, mirá la columna `Recv-Q`. ¿Qué representa ese número? Conectá un tercer cliente y volvé a mirar.
5. Bajá el `listen()` a `listen(1)` y probá con cuatro clientes. ¿Qué pasa con el cuarto?
6. Lo anterior explica un malentendido frecuente: "el cliente conectó, así que el servidor lo está atendiendo". ¿Por qué es falso?
7. Enumerá tres formas de resolver esto. (Todas las vimos en el bloque de concurrencia.)

---

## Verificación del ejercicio obligatorio

### Ejercicio 3: Framing

Tu implementación tiene que cumplir:

- [ ] Framing por delimitador funcionando
- [ ] Framing por longitud funcionando
- [ ] Ambos sobreviven a recibir todos los mensajes en un solo `sendall()`
- [ ] Ambos sobreviven a recibir un mensaje byte por byte
- [ ] `recibir_exacto()` implementado con bucle, no con un solo `recv()`
- [ ] El framing por longitud maneja contenido con `\n` adentro
- [ ] Manejo correcto del cierre de conexión (`recv()` devuelve `b''`)

Compará tu solución con `framing.py`. No mires antes de intentarlo.

---

## Ejercicios adicionales

### Servidor de comandos

Extendé el servidor por líneas para que entienda comandos: `TIME` devuelve la hora, `ECHO <texto>` devuelve el texto, `QUIT` cierra la conexión. Es, en miniatura, la estructura de SMTP.

### Transferencia de archivos

Cliente que manda un archivo y servidor que lo guarda, usando framing por longitud. Verificá con `md5sum` que llegó íntegro. Probá con un archivo de más de 100 MB.

### Cliente HTTP mínimo

Sin usar `requests` ni `http.client`: conectate al puerto 80, mandá una petición `GET` a mano y parseá la respuesta. Ya lo hiciste con `nc` en la clase 12; ahora en Python.

### getaddrinfo e IPv6

Investigá `socket.getaddrinfo()` y escribí un cliente que pruebe todas las direcciones devueltas hasta que una funcione. Es lo que hace `create_connection()` internamente.

---

*Computación II - 2026 - Clase 13*
