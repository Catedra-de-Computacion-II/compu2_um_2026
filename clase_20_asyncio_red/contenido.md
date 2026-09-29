# Clase 20: Asyncio en red

## Introducción: cerrar el círculo

Este bloque empezó en la clase 12 con la pregunta de cómo hablan dos procesos en máquinas distintas. Desde entonces fuimos acumulando respuestas parciales.

En la 13 escribimos un servidor TCP que atendía **un cliente a la vez**. En la 14 le agregamos concurrencia con threads y procesos, y medimos dónde se rompe. En la 17 vimos que hay otra forma —un solo hilo preguntándole al kernel quién está listo— pero el código quedaba partido en callbacks. En la 18 construimos corrutinas para que ese código se pudiera escribir lineal.

Hoy juntamos las dos últimas piezas: **corrutinas haciendo I/O de red de verdad**.

Vale aclarar qué cambia respecto de la clase 18. Ahí todos los `await` fueron sobre temporizadores: `asyncio.sleep`. Eso alcanzaba para entender el mecanismo, pero esperar tiempo es fácil —el loop solo necesita un reloj. Esperar **datos de la red** requiere que el loop vigile descriptores, que es exactamente lo de la clase 17.

Al final de esta clase van a poder escribir un servidor que atiende cientos de clientes simultáneos, en un hilo, con código que se lee de arriba abajo. Y van a entender por qué funciona.

> **Nota:** los archivos `eco_async.py`, `descargas.py` y `escala.py` acompañan la clase. El último mide 500 clientes concurrentes.

---

## La API de streams

Asyncio ofrece dos niveles para trabajar con red. El de bajo nivel usa protocolos y transportes, y se parece bastante al modelo de callbacks de la clase 17. El de alto nivel se llama **streams**, y es el que vamos a usar.

La idea es que una conexión se representa con dos objetos:

```python
reader, writer = await asyncio.open_connection('localhost', 8080)
```

**`StreamReader`** para leer, **`StreamWriter`** para escribir. Si les suena familiar es porque son los primos asíncronos de `rfile`/`wfile` de la clase 16: la misma abstracción de "archivo sobre un socket", pero con `await`.

### El cliente

```python
#!/usr/bin/env python3
import asyncio

async def main():
    reader, writer = await asyncio.open_connection('localhost', 8080)

    writer.write(b'hola\n')          # NO lleva await
    await writer.drain()             # este sí

    respuesta = await reader.readline()
    print(respuesta)

    writer.close()
    await writer.wait_closed()

asyncio.run(main())
```

Comparado con el cliente de la clase 13, la estructura es la misma: conectar, escribir, leer, cerrar. Lo que cambió es que cada operación que puede esperar lleva `await`, y en esos puntos el loop atiende a otros.

### Por qué `write()` no lleva await pero `drain()` sí

Es la asimetría que más confunde, y tiene explicación.

`writer.write()` **no bloquea nunca**: copia los bytes a un buffer interno y vuelve enseguida. Por eso no necesita `await`.

El problema es qué pasa si escribís más rápido de lo que la red puede mandar. El buffer crece, y si nadie lo frena, crece hasta agotar la memoria.

`await writer.drain()` es el freno: se suspende si el buffer está por encima de cierto umbral, y sigue cuando baja. Es **control de flujo a nivel de aplicación**, el mismo concepto que TCP hace a nivel de protocolo (clase 12).

```python
writer.write(datos)
await writer.drain()        # "esperá si vengo escribiendo demasiado rápido"
```

Si omitís el `drain()`, el programa funciona igual en pruebas chicas y consume memoria sin control cuando el otro extremo es lento. Es un bug que aparece en producción, nunca en desarrollo.

### Leer: el framing otra vez

`StreamReader` ofrece varias formas de leer, y elegir la correcta es el problema de la clase 13 con otra cara:

| Método | Qué hace |
|--------|----------|
| `await reader.read(n)` | Hasta n bytes; puede devolver menos |
| `await reader.readline()` | Hasta el `\n` inclusive |
| `await reader.readexactly(n)` | Exactamente n bytes, o `IncompleteReadError` |
| `await reader.readuntil(sep)` | Hasta el separador que le digas |

Fijate que `readline()` y `readexactly()` son **los dos framings de la clase 13**, ya implementados: delimitador y prefijo de longitud. El buffer que escribimos a mano ahí, acá viene incluido.

Y `read()` tiene la misma trampa de siempre: devuelve lo que haya, y `b''` significa que el otro lado cerró.

```python
while True:
    datos = await reader.read(4096)
    if not datos:                    # el chequeo de siempre
        break
```

---

## El servidor: una corrutina por cliente

```python
#!/usr/bin/env python3
import asyncio

async def manejar(reader, writer):
    """Se ejecuta una vez por conexión, como el handle() de la clase 16."""
    direccion = writer.get_extra_info('peername')
    print(f'+ {direccion}')

    while True:
        datos = await reader.readline()
        if not datos:
            break
        writer.write(datos)
        await writer.drain()

    print(f'- {direccion}')
    writer.close()
    await writer.wait_closed()

async def main():
    servidor = await asyncio.start_server(manejar, '0.0.0.0', 8080)
    async with servidor:
        await servidor.serve_forever()

asyncio.run(main())
```

Miralo al lado del `server_threads.py` de la clase 14. La estructura es **idéntica**: una función que atiende a un cliente, y algo que la invoca por cada conexión.

La diferencia está en qué es ese "algo". En la 14 era un `threading.Thread`; acá, `start_server` crea una **Task** —lo que vimos en la clase 18— por cada cliente. Cientos de tareas en un hilo, en vez de cientos de threads.

Y como todas comparten el hilo, **no hay locks**. Un contador compartido entre clientes no necesita protección:

```python
conectados = 0

async def manejar(reader, writer):
    global conectados
    conectados += 1              # sin Lock: nadie interrumpe entre awaits
    ...
```

Esto merece una aclaración importante, porque es fácil sacar la conclusión equivocada.

---

## Por qué no hacen falta locks (y cuándo sí)

En la clase 11 vimos que `contador += 1` no es atómico: es leer, sumar, guardar, y un thread puede interrumpir en el medio.

Con corrutinas eso no pasa, porque **el cambio de contexto solo ocurre en un `await`**. Entre dos `await` consecutivos, tu código corre sin interrupciones. Si la sección crítica no tiene ningún `await` adentro, es atómica por construcción.

Pero cuidado con el caso contrario:

```python
# MAL: hay un await en el medio de la sección crítica
async def transferir(origen, destino, monto):
    saldo = cuentas[origen]              # leo
    await registrar_en_log(monto)        # <- acá puede correr otro
    cuentas[origen] = saldo - monto      # escribo un valor que quizás quedó viejo
```

Entre la lectura y la escritura hay un punto de suspensión, y otra tarea puede haber modificado `cuentas[origen]`. **Es exactamente la race condition de la clase 11**, solo que los puntos donde puede ocurrir son visibles: están marcados con `await`.

Para esos casos, asyncio tiene sus propias primitivas —`asyncio.Lock`, `Semaphore`, `Event`, `Queue`— con la misma semántica que las de `threading` pero para corrutinas:

```python
lock = asyncio.Lock()

async def transferir(origen, destino, monto):
    async with lock:                      # async with, no with
        saldo = cuentas[origen]
        await registrar_en_log(monto)
        cuentas[origen] = saldo - monto
```

La regla, entonces: **no hacen falta locks salvo que la sección crítica contenga un `await`**. Y a diferencia de los threads, podés verificarlo leyendo el código.

---

## Concurrencia de clientes: el número que importa

La pregunta de la clase 14 era cuántos clientes simultáneos aguanta un servidor. Medimos threads, procesos y pools, y todos tenían un techo.

Con asyncio, 500 clientes concurrentes contra un servidor eco:

```
500 clientes atendidos en 0.21s
threads del proceso: 1
```

Un hilo, 500 conexiones, doscientos milisegundos.

Vale la pena detenerse en el contraste. En la clase 14, 500 clientes significaban 500 threads: unos 4 MB de stack cada uno —2 GB de memoria— más el costo de que el scheduler del kernel reparta tiempo entre todos. Acá cada cliente es un objeto Task de unos pocos cientos de bytes.

Esa es la respuesta al problema C10K que planteamos en la 14 y explicamos en la 17. No se resolvió haciendo los threads más baratos, sino **cambiando qué representa una conexión**: de un hilo de ejecución del sistema operativo a una estructura de datos en tu programa.

---

## Clientes concurrentes: descargar muchas cosas a la vez

El otro uso frecuente es del lado del cliente: pedir varias cosas en paralelo.

```python
import asyncio

async def bajar(nombre, demora):
    await asyncio.sleep(demora)          # simula la latencia de red
    return f'{nombre} listo'

async def main():
    resultados = await asyncio.gather(
        bajar('a', 1.0),
        bajar('b', 1.5),
        bajar('c', 0.5),
    )
    print(resultados)

asyncio.run(main())
```

Tarda 1.5 segundos —lo que la más lenta—, no 3.0. Es el patrón que el TP2 pide para la tarea `descargar`.

### Con HTTP real

Para HTTP asíncrono hace falta una biblioteca que hable el protocolo sin bloquear. `requests` **no sirve**: es sincrónica, y ya vimos en la clase 19 qué pasa cuando eso entra en una corrutina.

```python
import asyncio
import httpx

async def bajar(cliente, url):
    respuesta = await cliente.get(url)
    return url, respuesta.status_code, len(respuesta.content)

async def main():
    async with httpx.AsyncClient(timeout=10) as cliente:
        urls = ['https://example.com', 'https://httpbin.org/get']
        resultados = await asyncio.gather(*(bajar(cliente, u) for u in urls))
        for url, codigo, tam in resultados:
            print(f'{codigo}  {tam:>6} bytes  {url}')
```

Dos detalles que importan:

**El cliente se crea una vez y se reutiliza**, con `async with`. Crear uno por pedido descarta el pool de conexiones y pierde el keep-alive de la clase 19.

**Siempre timeout.** Sin él, una URL que no responde deja la tarea colgada para siempre. Es la falacia número 2 de las que vimos en la clase 12.

### Limitar la concurrencia

Lanzar mil descargas simultáneas no es buena idea: agota descriptores, satura la red, y probablemente el servidor del otro lado te bloquee.

La herramienta es un semáforo, igual que en la clase 11:

```python
limite = asyncio.Semaphore(10)           # máximo 10 a la vez

async def bajar_con_limite(cliente, url):
    async with limite:
        return await cliente.get(url)
```

Con eso podés encolar mil tareas y solo diez estarán activas en cada momento. El resto espera su turno sin consumir nada.

---

## Timeouts y cancelación

Dos cosas que el TP2 pide explícitamente y que conviene ver juntas, porque están relacionadas.

### Timeout

```python
try:
    async with asyncio.timeout(5):       # Python 3.11+
        datos = await reader.read(4096)
except TimeoutError:
    print('el cliente no mandó nada en 5 segundos')
```

También existe `asyncio.wait_for(corrutina, timeout=5)`, que es la forma anterior y sigue funcionando.

Lo interesante es **cómo** implementa el timeout: cuando vence, **cancela** la tarea. O sea que el timeout es un caso particular de cancelación.

### Cancelación

```python
tarea = asyncio.create_task(trabajo_largo())
await asyncio.sleep(1)
tarea.cancel()

try:
    await tarea
except asyncio.CancelledError:
    print('cancelada')
```

`cancel()` no mata nada de inmediato: **inyecta un `CancelledError` en el próximo punto de suspensión**. De ahí se siguen dos consecuencias importantes.

**Una tarea que no cede no se puede cancelar.** Si está calculando sin `await`, el `cancel()` queda pendiente hasta que llegue a uno. Es la misma regla de la clase 18 vista desde otro ángulo.

**La limpieza se hace con `try/finally`**, porque la excepción atraviesa la corrutina como cualquier otra:

```python
async def manejar(reader, writer):
    try:
        while True:
            datos = await reader.readline()
            if not datos:
                break
            writer.write(datos)
            await writer.drain()
    except asyncio.CancelledError:
        print('me cancelaron en el medio')
        raise                             # importante: volver a lanzarla
    finally:
        writer.close()                    # esto corre siempre
        await writer.wait_closed()
```

Ese `raise` del medio no es opcional. Si capturás `CancelledError` y no la relanzás, le estás mintiendo a quien pidió la cancelación: la tarea sigue viva y el `await tarea` nunca termina.

Por eso, desde Python 3.8, `CancelledError` hereda de `BaseException` y no de `Exception`: para que un `except Exception:` distraído no se la coma sin querer.

---

## Apagado ordenado

El TP2 pide que `SIGTERM` y `SIGINT` provoquen un cierre limpio. Con asyncio hay una forma prolija:

```python
import asyncio
import signal

async def main():
    servidor = await asyncio.start_server(manejar, '0.0.0.0', 8080)
    loop = asyncio.get_running_loop()
    cerrar = asyncio.Event()

    for s in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(s, cerrar.set)     # el loop maneja la señal

    async with servidor:
        await cerrar.wait()                        # esperar el pedido de cierre
        print('cerrando...')

    # acá el servidor ya no acepta conexiones nuevas
```

`loop.add_signal_handler()` es mejor que `signal.signal()` de la clase 6: en vez de un handler que interrumpe en cualquier momento —con todos los problemas de async-signal-safety que vimos ahí—, el loop recibe la señal y ejecuta el callback **entre** tareas, en un momento seguro.

Por debajo usa `signal.set_wakeup_fd`, que es el patrón self-pipe de la clase 6 hecho biblioteca.

---

## Cuándo asyncio no es la respuesta

Después de ver 500 clientes en un hilo es tentador usarlo para todo. La tabla de decisión sigue siendo la de siempre:

| Situación | Herramienta |
|-----------|-------------|
| Muchas conexiones, trabajo liviano | **asyncio** |
| Pocas conexiones, lógica compleja | threads (clase 14) |
| Trabajo CPU-bound | procesos (clase 9) |
| Bibliotecas que solo tienen versión sincrónica | threads, o `to_thread` |
| Un servidor simple que anda y ya | `socketserver` (clase 16) |

Y el costo que ya conocen: **todo el ecosistema tiene que ser asíncrono**. Una sola llamada bloqueante —`requests`, un driver de base de datos sincrónico, un `open()` de un archivo grande— arruina la ventaja. Para esos casos está `asyncio.to_thread()`, pero si la mayoría de tu código es así, quizás asyncio no sea la herramienta.

---

## Conceptos clave

1. **`open_connection` y `start_server`** son la API de alto nivel: streams en vez de callbacks.
2. **`reader`/`writer` son los primos async de `rfile`/`wfile`** de la clase 16.
3. **`write()` no lleva `await`, `drain()` sí**: el primero copia a un buffer, el segundo hace control de flujo.
4. **Omitir `drain()` consume memoria sin límite** con un cliente lento; no falla en pruebas.
5. **`readline()` y `readexactly()` son los dos framings de la clase 13**, ya implementados.
6. **`start_server` crea una Task por cliente**, no un thread.
7. **No hacen falta locks si la sección crítica no tiene `await` adentro**; si lo tiene, hay `asyncio.Lock`.
8. **500 clientes en un hilo, 0.21 s**: esa es la respuesta al problema C10K.
9. **`gather` para clientes concurrentes**, y `Semaphore` para acotar cuántos a la vez.
10. **Siempre timeout** en operaciones de red.
11. **`cancel()` inyecta `CancelledError` en el próximo `await`**: una tarea que no cede no se cancela.
12. **Relanzá `CancelledError` si la capturás**, y limpiá con `finally`.
13. **`loop.add_signal_handler()`** es la forma limpia de manejar señales: el self-pipe de la clase 6, hecho biblioteca.

---

## Preparación para la próxima clase

En la **clase 21 (Asyncio avanzado)** vamos a lo que falta para el TP2: colas y patrón productor-consumidor con `asyncio.Queue`, `TaskGroup` y concurrencia estructurada, sincronización async en detalle, y cómo sacar el trabajo pesado del loop con executors.

Para llegar preparado:

- Corré `escala.py` y guardá el número de clientes que aguanta tu máquina.
- Reescribí el servidor de comandos de la clase 16 en versión asíncrona. Vas a necesitar casi todo lo de hoy.

---

## Referencias

- [asyncio streams](https://docs.python.org/3/library/asyncio-stream.html) - la API que usamos hoy
- [asyncio: desarrollo con asyncio](https://docs.python.org/3/library/asyncio-dev.html) - errores frecuentes, vale la pena leerla entera
- [httpx](https://www.python-httpx.org/async/) - el cliente HTTP asíncrono
- [The C10K problem](http://www.kegel.com/c10k.html) - el texto que planteó el problema que hoy resolvimos
- Caleb Hattingh, *Using Asyncio in Python* - el libro corto y práctico sobre el tema

---

*Computación II - 2026 - Clase 20*
