# Clase 16: socketserver - Ejercicios Prácticos

Los archivos `eco_tcp.py`, `eco_udp.py`, `comandos.py` y `personalizado.py` acompañan la clase.

---

## Ejercicio 1: Recorrer la progresión

Rehacé los pasos 1 a 6 del contenido **escribiéndolos vos**, sin copiar y pegar. Cada uno arranca del anterior.

### 1.1 El mínimo

Escribí el servidor de 5 líneas del paso 1 y probalo con `nc`.

1. ¿Qué es `self.request`? Imprimí `type(self.request)` para confirmarlo.
2. Agregá un `print(id(self))` en `handle()` y conectate tres veces. ¿Qué observás?
3. ¿Cuántas veces se ejecuta `handle()` si un cliente manda tres mensajes en la misma conexión? Probalo.

### 1.2 El puerto ocupado

4. Conectate una vez, cortá el servidor con Ctrl+C y relanzalo enseguida. ¿Qué error da?
5. Ahora repetí **sin haberte conectado nunca**. ¿Da el mismo error? Explicá la diferencia. (Pista: TIME_WAIT necesita que haya habido una conexión.)
6. Agregá `allow_reuse_address = True` y verificá que desaparece.

### 1.3 Concurrencia

7. Con el servidor secuencial, agregá `time.sleep(3)` en `handle()` y conectá dos clientes. Medí cuánto tarda el segundo.
8. Cambiá a `ThreadingTCPServer` y repetí la medición. Anotá los dos números.
9. Probá con `ForkingTCPServer`. Agregá `print(os.getpid())` al handler: ¿cuántos PIDs distintos aparecen?

### 1.4 Framing

10. Con `BaseRequestHandler` y `recv(1024)`, mandá `printf 'UNO\nDOS\n' | nc localhost 8080`. ¿Qué recibe el servidor?
11. Cambiá a `StreamRequestHandler` iterando `self.rfile`. ¿Qué cambia?
12. ¿Por qué no hay que mezclar `self.rfile` con `self.request.recv()` en el mismo handler?

### 1.5 Estado

13. Implementá el contador con el atributo en el handler. ¿Por qué siempre da 1?
14. Movelo al servidor. ¿Ahora sí cuenta?
15. Sacá el `Lock` y lanzá 200 conexiones rápidas. ¿Se pierde alguna cuenta? (Puede que no: explicá por qué eso **no** significa que el código sea correcto.)

### 1.6 Errores

16. Hacé que `handle()` lance una excepción con cierto input. ¿Se cae el servidor?
17. Agregá `print` en `setup()` y `finish()`. Cuando `handle()` falla, ¿se ejecuta `finish()`? ¿En qué orden respecto de `handle_error()`?
18. Sacá el `super().setup()` de tu `setup()`. ¿Qué se rompe y por qué?

---

## Ejercicio 2: Los mixins (obligatorio)

### Objetivo

Entender cómo un cambio de clase base agrega concurrencia, y por qué el orden de herencia importa.

### Parte A: leer el código

```python
import inspect, socketserver
print(inspect.getsource(socketserver.ThreadingMixIn))
```

1. ¿Cuántos métodos define `ThreadingMixIn`? ¿Cuál es el que produce la concurrencia?
2. Compará `process_request` de `BaseServer` con el del mixin. ¿En qué se diferencian?
3. Mirá `ForkingMixIn`. ¿Dónde cosecha los hijos? ¿Por qué no hay zombies como en la clase 14?
4. ¿Cuánto código propio tiene `ThreadingTCPServer`? Buscá su definición.

### Parte B: el orden

```python
class Bien(socketserver.ThreadingMixIn, socketserver.TCPServer): pass
class Mal(socketserver.TCPServer, socketserver.ThreadingMixIn): pass

for C in (Bien, Mal):
    print(C.__name__, [k.__name__ for k in C.__mro__][:4])
```

5. ¿En qué se diferencian los dos MRO?
6. ¿Qué clase provee `process_request` en cada caso?

```python
for C in (Bien, Mal):
    print(C.__name__, next(k.__name__ for k in C.__mro__ if 'process_request' in k.__dict__))
```

7. Levantá un servidor lento con cada uno y conectá dos clientes. ¿Cuál atiende en paralelo?
8. `Mal`, ¿lanza algún error? ¿Por qué eso lo convierte en un bug peligroso?

### Parte C: forking y memoria

9. Tomá el contador del paso 5 y cambiá a `ForkingTCPServer`. ¿Qué devuelve ahora?
10. Explicá por qué, en términos de lo que vimos en la clase 4 sobre `fork()`.
11. ¿Qué herramienta de la clase 9 haría falta para arreglarlo? Implementalo con `multiprocessing.Value`.
12. ¿Dónde hay que crear ese `Value`: en el handler o en el `__init__` del servidor? ¿Por qué?

### Parte D: daemon_threads

13. Sacá `daemon_threads = True`, conectate con `nc`, dejá el cliente abierto y matá el servidor con Ctrl+C. ¿Qué pasa?
14. Restauralo y repetí. Explicá la diferencia.

---

## Ejercicio 3: UDP

```bash
python3 eco_udp.py
python3 eco_udp.py --files
```

1. En `EchoUDPCrudo`, ¿qué es `self.request`? Imprimí su tipo.
2. ¿Por qué hay que pasar `self.client_address` al `sendto()`, si en TCP no hacía falta?
3. Compará las dos implementaciones del archivo. ¿Qué esconde `DatagramRequestHandler`?
4. ¿Existe `ThreadingUDPServer`? ¿Tiene sentido, si UDP no tiene conexiones? Pensá en un handler que tarde.

---

## Ejercicio 4: Un servidor de verdad

Tomá `comandos.py` y extendelo.

1. Agregá `NICK <nombre>` que guarde un apodo por cliente. ¿Dónde vive ese dato: en el handler o en el servidor? Justificá.
2. Agregá `BROADCAST <texto>` que le mande el mensaje a todos los conectados. Vas a necesitar guardar los sockets, no solo las direcciones.
3. ¿Qué pasa si un cliente se desconecta justo mientras otro le está escribiendo? Manejalo.
4. Agregá un timeout: desconectar a quien no mande nada en 30 segundos. Pista: `StreamRequestHandler` tiene un atributo `timeout`.
5. Con `ForkingTCPServer`, ¿funcionaría el `BROADCAST`? ¿Por qué?

---

## Ejercicio 5: El límite

Prepara la clase 17.

1. Levantá `comandos.py` y abrí 200 conexiones simultáneas.
2. Contá los threads: `ls /proc/$(pgrep -f comandos)/task | wc -l`.
3. Mirá la memoria: `ps -o rss= -p $(pgrep -f comandos)`.
4. Subí a 1000 conexiones. ¿Qué pasa?
5. ¿Resuelve `socketserver` el problema C10K de la clase 14? Justificá con tus números.

---

## Verificación del ejercicio obligatorio

### Ejercicio 2: Los mixins

- [ ] Identificaste qué método sobrescribe cada mixin
- [ ] Explicaste dónde cosecha los hijos `ForkingMixIn`
- [ ] Mostraste los dos MRO y qué clase provee `process_request` en cada uno
- [ ] Comprobaste que el orden invertido no da error pero no concurre
- [ ] Mediste la diferencia entre secuencial y concurrente con clientes lentos
- [ ] Explicaste por qué el estado compartido falla con forking
- [ ] Implementaste la versión con `multiprocessing.Value`
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
