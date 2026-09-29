# Clase 20: Asyncio en red - Extra Manijas

Material opcional para profundizar.

---

## El nivel de abajo: transportes y protocolos

Los streams que usamos hoy son la capa cómoda. Debajo hay otra API, más vieja y más parecida a lo que vimos en la clase 17:

```python
import asyncio

class EcoProtocolo(asyncio.Protocol):
    def connection_made(self, transport):
        self.transport = transport
        print('conectado:', transport.get_extra_info('peername'))

    def data_received(self, datos):          # callback, no corrutina
        self.transport.write(datos)

    def connection_lost(self, exc):
        print('desconectado')

async def main():
    loop = asyncio.get_running_loop()
    servidor = await loop.create_server(EcoProtocolo, '0.0.0.0', 8080)
    async with servidor:
        await servidor.serve_forever()
```

Fijate que no hay ningún `await` adentro del protocolo: son **callbacks**, exactamente el modelo de la clase 17. El event loop llama a `data_received` cuando hay datos, igual que nuestro bucle llamaba al handler registrado.

Los streams están construidos encima de esto: `StreamReader` es un protocolo que acumula en un buffer y despierta a la corrutina que estaba esperando.

¿Cuándo usar el nivel bajo? Cuando necesitás control fino sobre el flujo, o para protocolos donde los streams no encajan. Es más rápido —no hay corrutina por conexión— pero volvés al código partido en pedazos. Para casi todo, streams.

---

## Backpressure: el problema que resuelve drain()

Vale la pena entender bien por qué existe `drain()`, porque el bug que evita es de los que solo aparecen en producción.

Cuando hacés `writer.write(datos)`, los bytes van a un buffer del transporte. Si el otro extremo lee lento —o no lee—, ese buffer crece. Sin límite.

```python
# Un servidor que manda datos a un cliente lento
while True:
    writer.write(generar_megabyte())      # sin drain
    # el buffer crece indefinidamente
```

El transporte tiene dos umbrales configurables:

```python
transport.set_write_buffer_limits(high=64 * 1024, low=16 * 1024)
```

Cuando el buffer supera `high`, el transporte marca que está saturado; cuando baja de `low`, se libera. `drain()` consulta ese estado: si está saturado, se suspende hasta que baje.

```python
writer.write(datos)
await writer.drain()        # solo se suspende si hace falta
```

En condiciones normales `drain()` vuelve inmediatamente y no cuesta nada. Solo frena cuando efectivamente venís escribiendo más rápido de lo que el otro consume — que es exactamente cuando querés frenar.

Es el mismo concepto que el control de flujo de TCP (clase 12), una capa más arriba: TCP frena al kernel emisor, `drain()` frena a tu corrutina.

---

## Servir sobre sockets Unix

Todo lo de la clase funciona igual con `AF_UNIX`, que vimos en las manijas de la clase 13:

```python
servidor = await asyncio.start_unix_server(manejar, path='/tmp/mi.sock')
reader, writer = await asyncio.open_unix_connection('/tmp/mi.sock')
```

Sin handshake, sin checksums, con los permisos del filesystem como control de acceso. Para comunicación entre procesos de la misma máquina es notablemente más rápido que TCP sobre loopback.

Es lo que usan varios servidores en producción: nginx recibe HTTP por TCP y le habla a la aplicación por un socket Unix.

---

## Un event loop más rápido

Asyncio permite reemplazar la implementación del loop. La alternativa más conocida es **uvloop**, escrita sobre libuv —la misma biblioteca de Node.js:

```python
import asyncio, uvloop

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
# desde Python 3.12:
# asyncio.run(main(), loop_factory=uvloop.new_event_loop)
```

Los benchmarks suelen mostrar entre 2 y 4 veces más throughput en servidores de red. No cambia tu código: es el mismo asyncio con otro motor debajo.

uvicorn lo usa automáticamente si está instalado, y por eso conviene `pip install uvicorn[standard]` en vez de `uvicorn` a secas.

Vale la advertencia habitual: esto importa cuando el cuello de botella es el loop, que casi nunca es el caso en una aplicación típica. Medí antes de optimizar.

---

## Depurar código asíncrono

El modo debug del loop detecta los errores más comunes:

```python
asyncio.run(main(), debug=True)
```

Con eso, asyncio avisa de:

- Corrutinas que tardan más de 100 ms sin ceder (el bug de la clase 18)
- Corrutinas creadas y nunca esperadas
- Tasks destruidas mientras estaban pendientes
- Excepciones que nunca fueron consultadas

También se activa con la variable de entorno `PYTHONASYNCIODEBUG=1`.

Para inspeccionar en vivo qué tareas hay:

```python
for t in asyncio.all_tasks():
    print(t.get_name(), t.get_coro())
```

Y desde Python 3.12, `asyncio.Task` permite nombres, lo que ayuda muchísimo a leer los tracebacks:

```python
asyncio.create_task(trabajo(), name='worker-3')
```

Un traceback de asyncio puede ser confuso porque la pila no refleja quién lanzó la tarea. Nombrarlas es la forma barata de orientarse.

---

## El error de las tareas huérfanas

Ya lo mencionamos en la clase 18, pero en un servidor es más fácil cometerlo:

```python
async def manejar(reader, writer):
    asyncio.create_task(registrar_en_log(...))     # fuego y olvido
    ...
```

Esa task no está referenciada por nadie. El recolector de basura puede llevársela antes de que termine, y el trabajo se pierde silenciosamente.

La forma correcta:

```python
tareas_en_curso = set()

def lanzar(corrutina):
    t = asyncio.create_task(corrutina)
    tareas_en_curso.add(t)
    t.add_done_callback(tareas_en_curso.discard)
    return t
```

Desde Python 3.11, `TaskGroup` resuelve esto de raíz: las tareas viven dentro del bloque y nadie las pierde.

---

## Qué pasa con los archivos

Una limitación que sorprende: **asyncio no hace I/O de archivos asíncrono**.

```python
with open('grande.txt') as f:
    datos = f.read()        # BLOQUEA el event loop
```

La razón es la de la clase 17: un archivo regular siempre se reporta "listo" para `select`/`epoll`, aunque leerlo implique esperar al disco. El mecanismo de multiplexing no sirve para archivos.

Las salidas:

```python
# Mandar la lectura a un thread
datos = await asyncio.to_thread(Path('grande.txt').read_text)

# O usar aiofiles, que hace lo mismo por debajo
import aiofiles
async with aiofiles.open('grande.txt') as f:
    datos = await f.read()
```

Ninguna es I/O asíncrono de verdad: las dos usan threads. El I/O de archivos realmente asíncrono necesita `io_uring`, que mencionamos en las manijas de la clase 17 y todavía no está en la stdlib.

---

## Lecturas

- [asyncio: transports and protocols](https://docs.python.org/3/library/asyncio-protocol.html) - el nivel de abajo
- [asyncio: desarrollo con asyncio](https://docs.python.org/3/library/asyncio-dev.html) - modo debug y errores comunes
- [uvloop](https://github.com/MagicStack/uvloop) - el loop alternativo
- [httpx](https://www.python-httpx.org/async/) - cliente HTTP asíncrono
- Caleb Hattingh, *Using Asyncio in Python* (O'Reilly) - corto y muy práctico
- [Trio](https://trio.readthedocs.io/) - otra biblioteca async, con ideas que asyncio fue adoptando

---

*Computación II - 2026 - Clase 20*
