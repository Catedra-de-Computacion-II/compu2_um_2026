# Clase 16: I/O Multiplexing - Extra Manijas

Material opcional para profundizar.

---

## Level-triggered contra edge-triggered

`epoll` tiene dos modos de notificación, y confundirlos produce bugs muy difíciles de encontrar.

**Level-triggered (LT)** es el default y el comportamiento de `select` y `poll`: mientras haya datos sin leer, cada llamada te lo vuelve a reportar. Si leés 10 de 100 bytes, la próxima llamada te avisa de nuevo.

**Edge-triggered (ET)** avisa **una sola vez**, cuando el estado *cambia*. Si llegan 100 bytes y leés 10, no te vuelve a avisar hasta que lleguen datos nuevos. Los 90 restantes quedan ahí, y tu programa no se entera.

```python
ep.register(fd, select.EPOLLIN | select.EPOLLET)     # edge-triggered
```

Con ET, la regla es obligatoria: **leer en bucle hasta `BlockingIOError`**.

```python
while True:
    try:
        datos = conn.recv(4096)
        if not datos:
            break                    # cerró
        procesar(datos)
    except BlockingIOError:
        break                        # ya no hay más: ahora sí esperar el próximo evento
```

¿Para qué existe ET? Reduce la cantidad de despertadas del proceso, lo que importa a escala grande. nginx lo usa. Pero para casi todo lo demás, LT es más simple y menos propenso a errores, y por eso es el default.

El bug típico de ET es un cliente que "se cuelga" con datos a medio leer: el servidor los tiene en el buffer del kernel y nunca vuelve a mirarlos.

---

## El thundering herd

Un problema clásico cuando varios procesos vigilan el mismo socket que escucha.

Con un servidor pre-forked —N procesos, todos con `accept()` sobre el mismo fd heredado— llega una conexión y el kernel despierta a **todos**. Todos corren a hacer `accept()`, uno gana, y los N-1 restantes vuelven a dormir habiendo gastado un cambio de contexto para nada. Con 100 procesos y muchas conexiones por segundo, es puro desperdicio.

Linux tiene dos soluciones:

**`EPOLLEXCLUSIVE`** (kernel 4.5+): al registrar, pide que se despierte a uno solo.

```python
ep.register(fd, select.EPOLLIN | select.EPOLLEXCLUSIVE)
```

**`SO_REUSEPORT`** (kernel 3.9+): permite que varios procesos hagan `bind()` al *mismo* puerto, cada uno con su propio socket que escucha, y el kernel reparte las conexiones entre ellos.

```python
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
```

Esto último es más interesante de lo que parece: permite escalar a varios cores sin un proceso distribuidor, y hasta reiniciar un servidor sin perder conexiones —el proceso nuevo hace bind al mismo puerto mientras el viejo termina de atender lo que tiene.

Es lo que usan nginx y los servidores Go modernos para aprovechar todos los cores.

---

## Vigilar cosas que no son sockets

Un descriptor es un descriptor. `select` y compañía funcionan con cualquier cosa que tenga uno, y Linux expone bastante como fd:

**`timerfd`**: un temporizador como descriptor. Tu event loop puede esperar tiempo igual que espera datos, sin un `sleep` aparte.

**`signalfd`**: señales como descriptor. Es la versión moderna del self-pipe de la clase 6: en vez de un handler que interrumpe en cualquier momento, las señales llegan como eventos ordinarios del bucle.

**`eventfd`**: un contador para despertar el bucle desde otro thread. Es la forma canónica de que un worker le avise al event loop que terminó.

**`inotify`**: cambios en el filesystem como eventos.

Python expone algunos en `os`:

```python
import os, select

# eventfd: despertar el bucle desde otro thread
efd = os.eventfd(0)
sel_fd = select.epoll()
sel_fd.register(efd, select.EPOLLIN)

# Desde otro thread:
os.eventfd_write(efd, 1)      # el bucle se despierta
```

Esto es lo que permite que un event loop sea el único punto de espera del programa: tiempo, señales, red y avisos de otros threads, todo por el mismo mecanismo. Asyncio hace exactamente eso.

Lo que **no** anda bien con multiplexing es el I/O de archivos comunes: un archivo regular siempre se reporta "listo", aunque leerlo implique esperar al disco. Por eso asyncio usa un thread pool para archivos, y por eso existe `io_uring`.

---

## io_uring: lo que viene después de epoll

`epoll` te dice *cuándo* podés hacer una operación; después la hacés vos con una syscall. Con mucho tráfico, esas syscalls se acumulan.

`io_uring` (Linux 5.1, 2019) cambia el modelo: dos colas circulares compartidas entre tu proceso y el kernel. Vos ponés operaciones en la de envío, el kernel deja los resultados en la de recepción, y en el caso ideal **no hay syscall por operación**.

Diferencias de fondo:

| | `epoll` | `io_uring` |
|---|---|---|
| Qué informa | "podés leer" | "ya leí, acá están los datos" |
| Syscalls | una por operación | idealmente ninguna |
| Archivos regulares | no sirve | sí funciona |

Todavía no está en la stdlib de Python, pero hay bindings de terceros y varios runtimes lo están adoptando. Si dentro de unos años ves que asyncio cambia por dentro, va a ser por esto.

---

## Por qué asyncio no es solo esto

Después de ver `selectors`, es tentador pensar que asyncio es un envoltorio lindo del mismo bucle. Hay algo más.

Con callbacks, el flujo se parte en pedazos. Esto:

```python
def paso1(conn):
    datos = conn.recv(4096)
    sel.modify(conn, EVENT_WRITE, paso2)      # continuá en paso2

def paso2(conn):
    conn.send(respuesta)
    sel.modify(conn, EVENT_READ, paso3)       # y después en paso3
```

es lo que en JavaScript se llamó *callback hell*: una operación de tres pasos son tres funciones, el estado hay que pasarlo a mano, y el manejo de errores se vuelve un problema porque no hay un `try` que abarque la secuencia.

Asyncio agrega **corrutinas** encima del multiplexor, y eso permite escribir la misma secuencia como código lineal:

```python
async def manejar(conn):
    datos = await conn.recv(4096)
    await conn.send(respuesta)
    ...
```

Cada `await` es un punto donde la función se suspende y el bucle atiende a otro, pero el código se lee de arriba abajo, con `try/except` normales y variables locales que sobreviven entre pasos.

El mecanismo que hace posible esa suspensión son los generadores y `.send()` —lo que vimos en el bloque 0 y lo que vamos a construir en la clase 19. El multiplexor de esta clase queda abajo, intacto, haciendo el trabajo.

---

## Medir el event loop en producción

Un servidor de event loop tiene una métrica crítica que un servidor de threads no: **cuánto tarda una vuelta del bucle**.

Si una vuelta tarda 200 ms, ningún cliente puede tener menos de 200 ms de latencia, por rápido que sea su pedido. Y el síntoma es engañoso: el CPU puede estar al 30% mientras las respuestas tardan una eternidad, porque el problema no es falta de capacidad sino un handler que se queda con el hilo.

Instrumentarlo es simple:

```python
import time

umbral = 0.05                      # 50 ms
while True:
    t0 = time.perf_counter()
    eventos = sel.select(timeout=1)
    t_espera = time.perf_counter() - t0

    t1 = time.perf_counter()
    for clave, mascara in eventos:
        clave.data(clave.fileobj, mascara)
    t_trabajo = time.perf_counter() - t1

    if t_trabajo > umbral:
        print(f'ALERTA: una vuelta tardó {t_trabajo*1000:.0f} ms '
              f'procesando {len(eventos)} eventos')
```

Separar el tiempo de espera del de trabajo es lo importante: esperar mucho está bien (significa que no hay carga), trabajar mucho en una vuelta no.

Asyncio trae esto incorporado con `loop.set_debug(True)`, que avisa de las corrutinas que tardan más de 100 ms.

---

## Lecturas

- [The C10K problem](http://www.kegel.com/c10k.html) - Dan Kegel, 1999. Histórico y todavía legible
- [epoll(7)](https://man7.org/linux/man-pages/man7/epoll.7.html) - la man page, con la explicación de LT contra ET
- [Efficient IO with io_uring](https://kernel.dk/io_uring.pdf) - el paper de Jens Axboe
- [Why does one NGINX worker take all the load?](https://blog.cloudflare.com/the-sad-state-of-linux-socket-balancing/) - Cloudflare sobre thundering herd y `SO_REUSEPORT`
- [`selectors`](https://docs.python.org/3/library/selectors.html) - documentación de Python
- Stevens, *UNIX Network Programming, Vol. 1* - capítulo 6

---

*Computación II - 2026 - Clase 16*
