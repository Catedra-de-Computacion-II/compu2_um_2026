# Clase 16: socketserver - Ejercicios Prácticos

Los archivos `eco_tcp.py`, `eco_udp.py`, `comandos.py` y `personalizado.py` acompañan la clase.

---

## Ejercicio 1: La jerarquía

### 1.1 Explorarla desde Python

```python
import socketserver
for n in ['TCPServer', 'UDPServer', 'UnixStreamServer', 'UnixDatagramServer',
          'ThreadingTCPServer', 'ForkingTCPServer']:
    print(n, '->', getattr(socketserver, n).__bases__)
```

1. Compará la salida con el diagrama de la clase. ¿De quién hereda `UDPServer`?
2. El diagrama muestra `UDPServer` como hermano de `TCPServer`, pero el código dice otra cosa. ¿Es un error del diagrama? Justificá.
3. ¿Qué implica esa herencia? Buscá algún atributo que `UDPServer` reciba de `TCPServer` y que no tenga sentido en UDP.

### 1.2 Los atributos de clase

```python
print(socketserver.TCPServer.allow_reuse_address)
print(socketserver.TCPServer.request_queue_size)
print(socketserver.TCPServer.address_family)
```

4. ¿A qué equivale cada uno de lo que escribimos a mano en la clase 13?
5. `allow_reuse_address` viene en `False`. Levantá un servidor sin cambiarlo, matalo con Ctrl+C y relanzalo de inmediato. ¿Qué error da?
6. Poné `allow_reuse_address = True` y repetí. ¿Desaparece?

### 1.3 IPv6 en una línea

7. Tomá `eco_tcp.py` y hacelo IPv6 cambiando **un solo atributo**. ¿Cuál?
8. Conectate con `nc -6 ::1 8080`. ¿Anda?
9. ¿Qué habría que agregar para que acepte también IPv4? (Pista: clase 15, `IPV6_V6ONLY`.) Mirá `personalizado.py --v6`.

---

## Ejercicio 2: Los handlers

### 2.1 Los tres tipos

```bash
python3 eco_tcp.py
```

1. `EchoHandler` usa `StreamRequestHandler`. ¿Qué le da eso que `BaseRequestHandler` no?
2. Reescribilo con `BaseRequestHandler`. ¿Cuánto código extra necesitás para el framing por líneas?
3. Compará tu versión con `framing.py` de la clase 13. ¿Es el mismo problema?

### 2.2 La asimetría de self.request

```bash
python3 eco_udp.py            # BaseRequestHandler
python3 eco_udp.py --files    # DatagramRequestHandler
```

4. En `EchoUDPCrudo`, ¿qué es `self.request`? ¿Y en un handler TCP?
5. ¿Por qué en UDP hay que pasar `self.client_address` al responder, y en TCP no?
6. ¿Qué esconde `DatagramRequestHandler`? Compará las dos implementaciones del archivo.

### 2.3 Una instancia por conexión

Agregale esto a un handler:

```python
class Contador(socketserver.StreamRequestHandler):
    veces = 0                      # atributo de CLASE

    def handle(self):
        self.n = getattr(self, 'n', 0) + 1      # atributo de INSTANCIA
        Contador.veces += 1
        self.wfile.write(f'instancia={self.n} clase={Contador.veces}\n'.encode())
```

7. Conectate varias veces. ¿Qué pasa con `self.n`? ¿Y con `Contador.veces`?
8. Explicá la diferencia. ¿Cuántos objetos handler se crean si se conectan 10 clientes?
9. Entonces, ¿dónde hay que guardar el estado que debe sobrevivir entre conexiones?

---

## Ejercicio 3: Los mixins (obligatorio)

### Objetivo

Entender cómo los mixins agregan concurrencia sin duplicar la jerarquía, y por qué el orden de herencia importa.

### Parte A: leer el código fuente

```python
import inspect, socketserver
print(inspect.getsource(socketserver.ThreadingMixIn))
```

1. ¿Cuántos métodos define `ThreadingMixIn`? ¿Cuál es el que importa?
2. Buscá `process_request` en `TCPServer` y en `ThreadingMixIn`. ¿Qué hace cada uno?
3. Mirá también `ForkingMixIn`. ¿Dónde cosecha los hijos? ¿Por qué no hay zombies como en la clase 14?

### Parte B: el orden importa

```python
import socketserver

class Correcto(socketserver.ThreadingMixIn, socketserver.TCPServer): pass
class AlReves(socketserver.TCPServer, socketserver.ThreadingMixIn): pass

print([c.__name__ for c in Correcto.__mro__])
print([c.__name__ for c in AlReves.__mro__])
```

4. ¿En qué se diferencian los dos MRO?
5. Levantá un servidor con cada uno y conectá dos clientes lentos. ¿Cuál atiende en paralelo?
6. El que está al revés, ¿lanza algún error? ¿Por qué eso lo hace un bug peligroso?

### Parte C: threads contra procesos

```bash
python3 eco_tcp.py 8080           # threads
python3 eco_tcp.py --fork 8080    # procesos
```

7. Conectá 5 clientes a cada uno y mirá la salida. ¿Qué cambia entre los dos modos?
8. Con `--fork`, ¿cuántos PIDs distintos aparecen? Verificalo también con `ps --ppid $(pgrep -f eco_tcp)`.
9. Contá los threads del proceso en el modo threading: `ls /proc/$(pgrep -f eco_tcp)/task | wc -l`.

### Parte D: el estado no se comparte igual

Agregale a `comandos.py` un contador global y probalo con los dos mixins.

10. Con `ThreadingTCPServer`, el comando `CONTADOR` funciona. ¿Por qué?
11. Cambiá a `ForkingTCPServer` y probá de nuevo. ¿Qué devuelve `CONTADOR`? ¿Por qué?
12. ¿Qué herramienta de la clase 9 haría falta para que funcione con forking?

### Parte E: daemon_threads

13. Sacá `daemon_threads = True` de `eco_tcp.py`. Conectate con `nc`, dejalo abierto y matá el servidor con Ctrl+C. ¿Qué pasa?
14. Restauralo y repetí. ¿Cuál es la diferencia?

---

## Ejercicio 4: El ciclo de vida

```bash
python3 personalizado.py
```

Conectate y mirá la salida.

1. Anotá el orden exacto en que aparecen: `server_bind`, `server_activate`, `verify_request`, `setup`, `handle`, `finish`.
2. ¿Cuáles se ejecutan una sola vez y cuáles por cada conexión?

### 4.1 verify_request

```bash
python3 personalizado.py --bloquear
```

3. Conectate desde localhost. ¿Qué pasa? ¿Se llega a ejecutar `handle()`?
4. Escribí un `verify_request` que rechace después de N conexiones del mismo cliente.
5. ¿Por qué conviene rechazar ahí y no al principio de `handle()`?

### 4.2 handle_error

Con el servidor corriendo, mandá `CRASH`:

```bash
echo "CRASH" | nc localhost 8080
```

6. ¿Se cae el servidor? ¿Qué imprime?
7. Conectate de nuevo después del crash. ¿Sigue funcionando?
8. Mirá el log: ¿se ejecutó `finish()` para la conexión que falló? ¿Por qué es importante?

### 4.3 setup y finish

9. En `comandos.py`, `setup()` y `finish()` llevan la cuenta de conexiones activas. ¿Qué pasaría si esa lógica estuviera dentro de `handle()`?
10. ¿Por qué ambos llaman a `super()`? Sacá el `super().setup()` y mirá qué se rompe.

---

## Ejercicio 5: Estado compartido y sincronización

```bash
python3 comandos.py
```

Conectate con dos o tres clientes y probá `QUIEN` y `CONTADOR`.

1. ¿Dónde vive el estado compartido? ¿Por qué no puede vivir en el handler?
2. `comandos.py` usa un `threading.Lock`. ¿Qué race condition previene? Relacionalo con la clase 11.
3. Sacá el lock y escribí un cliente que abra y cierre 200 conexiones rápido. ¿Se corrompe el contador? (Puede que no: explicá por qué eso no significa que el código sea correcto.)
4. ¿Qué operación del código sería la más propensa a romperse sin lock: incrementar el contador o modificar el set?

---

## Ejercicio 6: El límite que socketserver no resuelve

Este ejercicio prepara la clase 17.

1. Levantá `eco_tcp.py` y abrí 200 conexiones simultáneas con un script.
2. Contá los threads: `ls /proc/$(pgrep -f eco_tcp)/task | wc -l`. ¿Cuántos hay?
3. Subí a 1000. ¿Qué pasa con la memoria del proceso? Mirá con `ps -o rss= -p $(pgrep -f eco_tcp)`.
4. ¿Es `socketserver` una solución al problema C10K de la clase 14? Justificá.
5. ¿Qué habría que cambiar del modelo para atender 10.000 conexiones? (Esa es la clase 17.)

---

## Verificación del ejercicio obligatorio

### Ejercicio 3: Los mixins

- [ ] Identificaste qué método sobrescribe cada mixin
- [ ] Explicaste dónde cosecha los hijos `ForkingMixIn`
- [ ] Mostraste los dos MRO y la diferencia entre ellos
- [ ] Comprobaste que el orden invertido no da error pero no concurre
- [ ] Contaste PIDs con forking y threads con threading
- [ ] Explicaste por qué el estado compartido funciona con threads y no con procesos
- [ ] Probaste el efecto de `daemon_threads`

---

## Ejercicios adicionales

### Servidor de archivos

Un handler que reciba `GET <nombre>` y devuelva el contenido del archivo, con framing por longitud (clase 13). Manejá el caso de archivo inexistente sin que se caiga el servidor.

### Chat con socketserver

Reescribí el `chat.py` de la clase 17 usando `ThreadingTCPServer`. Vas a necesitar mantener la lista de clientes en el servidor y un lock. ¿Cuál de las dos versiones es más simple?

### Timeout de inactividad

`StreamRequestHandler` tiene un atributo `timeout`. Configuralo y agregá un `handle_timeout()`. Probá dejando un cliente conectado sin escribir.

### Comparar con la clase 14

Tomá `server_threads.py` de la clase 14 y `eco_tcp.py` de esta. Contá líneas de cada uno y hacé una tabla de qué resuelve `socketserver` automáticamente.

### Leer el fuente

`socketserver.py` son unas 800 líneas legibles. Leé `BaseServer.serve_forever()` y encontrá el `selector` que usa por dentro. ¿Qué relación tiene con la clase 17?

---

*Computación II - 2026 - Clase 16*
