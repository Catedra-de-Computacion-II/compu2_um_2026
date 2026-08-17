# Clase 14: Servidores Concurrentes - Extra Manijas

Material opcional para profundizar.

---

## El thundering herd

Si varios procesos hacen `accept()` sobre el **mismo** socket que escucha, ¿qué pasa cuando llega una conexión?

Históricamente: el kernel despertaba a **todos**, todos competían, uno ganaba y el resto volvía a dormir habiendo hecho un cambio de contexto para nada. Con cientos de workers, cada conexión provocaba cientos de despertares inútiles. Se lo llamó *thundering herd* — la estampida.

Linux lo arregló para `accept()` hace tiempo (despierta a uno solo), pero el problema volvió con `epoll`: si varios procesos esperan sobre el mismo descriptor con `epoll_wait`, la estampida reaparece. De ahí `EPOLLEXCLUSIVE`, agregado en Linux 4.5.

La solución moderna es otra: **`SO_REUSEPORT`**.

```python
import socket

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
s.bind(('0.0.0.0', 8080))
s.listen(128)
```

Con `SO_REUSEPORT`, **varios procesos pueden hacer `bind()` al mismo puerto**, cada uno con su propio socket, y el kernel reparte las conexiones entrantes entre ellos con un hash. No hay estampida porque cada conexión despierta exactamente a un proceso, y no hay un proceso padre que sea cuello de botella.

Es lo que usan nginx y la mayoría de los servidores modernos para aprovechar varios núcleos: N procesos independientes, todos escuchando en el 80.

Un detalle de seguridad: en Linux, todos los sockets que comparten el puerto deben pertenecer al mismo usuario efectivo. Si no, cualquiera podría "robar" tráfico de un servicio ajeno.

---

## El backlog de listen(), en detalle

`listen(n)` no es una sola cola, son dos:

```
SYN recibido          handshake completo
      |                       |
      v                       v
 [ cola SYN ]  --------> [ cola accept ]  --------> tu accept()
   (incompleta)            (completa)
```

- La **cola SYN** guarda conexiones a medio handshake (llegó el SYN, se mandó SYN-ACK, falta el ACK).
- La **cola accept** guarda conexiones ya establecidas esperando que la aplicación las tome.

El argumento de `listen()` limita la segunda. La primera se controla aparte:

```bash
cat /proc/sys/net/ipv4/tcp_max_syn_backlog
cat /proc/sys/net/core/somaxconn        # tope duro del backlog de accept
```

Si pedís `listen(1000)` pero `somaxconn` vale 128, tenés 128. El kernel trunca en silencio.

Cuando la cola accept se llena, el kernel descarta el ACK final. El cliente cree que la conexión está abierta y reintenta; desde afuera se ve como una conexión lenta, no como un rechazo.

Podés ver ambas colas:

```bash
ss -tln          # Recv-Q en una línea LISTEN = conexiones esperando accept()
                 # Send-Q en esa línea = el backlog configurado
```

Esa columna `Recv-Q` en la línea `LISTEN` es exactamente el ejercicio 6 de la clase 13 visto desde el otro lado.

### SYN flood

Llenar la cola SYN a propósito es un ataque clásico: mandar miles de SYN sin completar nunca el handshake. La defensa son las **SYN cookies**, que codifican el estado de la conexión en el propio número de secuencia y permiten no guardar nada hasta que llegue el ACK.

```bash
cat /proc/sys/net/ipv4/tcp_syncookies    # 1 = habilitadas
```

---

## Por qué un thread cuesta menos de lo que parece

Se suele decir que un thread reserva 8 MB de stack. Verificalo:

```bash
ulimit -s          # tamaño de stack por defecto, en KB
```

Pero esos 8 MB son **espacio de direcciones virtuales**, no memoria física. Linux asigna páginas reales solo cuando se tocan, así que un thread que usa 16 KB de stack consume 16 KB de RAM, no 8 MB.

Compruébalo comparando `VmSize` (virtual) contra `VmRSS` (residente) mientras subís la cantidad de threads:

```bash
grep -E "VmSize|VmRSS|Threads" /proc/<PID>/status
```

Lo que sí escala mal no es la memoria sino el **planificador**: más threads listos para correr significa más cambios de contexto, más presión de caché, y más contención sobre las estructuras del kernel. Por eso el techo práctico está en los miles y no en los cientos de miles, aun con RAM de sobra.

Se puede bajar el stack por thread:

```python
import threading
threading.stack_size(512 * 1024)     # 512 KB, antes de crear los threads
```

Útil si sabés que tus threads no recursan hondo.

---

## fork() y el copy-on-write

`fork()` no copia la memoria del padre: crea una tabla de páginas que apunta a las mismas páginas físicas, marcadas como solo lectura. Recién cuando alguno de los dos escribe, el kernel copia esa página. Es **copy-on-write**, y lo vimos en la clase 4.

Por eso forkear un proceso de 500 MB es casi instantáneo y no consume 500 MB extra.

El problema es que **CPython lo arruina**. El conteo de referencias escribe en la cabecera de cada objeto que se toca, aunque solo lo estés leyendo:

```python
import sys
x = [1, 2, 3]
sys.getrefcount(x)     # el solo hecho de mirarlo modifica el contador
```

Resultado: un hijo que recorre estructuras heredadas del padre va copiando páginas sin escribir nada semánticamente. Es un problema conocido de los servidores pre-fork en Python (Gunicorn, uWSGI), y parte de por qué existe `gc.freeze()`:

```python
import gc
gc.freeze()      # mueve los objetos actuales a un área que el GC no toca
# ... ahora forkear
```

Se llama antes de forkear, en el padre, y reduce bastante la copia espuria.

---

## Pre-fork: cómo lo hacen los servidores reales

Ni "un proceso por cliente" ni "un thread por cliente" es lo que usa un servidor de producción. El patrón real es **pre-fork**: crear N workers al arrancar y que cada uno atienda conexiones en un bucle.

```python
import os
import socket

NUM_WORKERS = os.cpu_count()

servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
servidor.bind(('0.0.0.0', 8080))
servidor.listen(128)

for _ in range(NUM_WORKERS):
    if os.fork() == 0:
        # Cada worker corre su propio bucle de accept() sobre el MISMO socket
        while True:
            conn, _ = servidor.accept()
            with conn:
                atender(conn)
        os._exit(0)

# El padre solo supervisa: recoge workers muertos y los repone
while True:
    pid, status = os.wait()
    print(f'worker {pid} murió; relanzando')
    if os.fork() == 0:
        ...
```

Ventajas: no se paga el costo de crear un proceso por conexión, y el padre puede reponer workers que mueran. Es el modelo de Gunicorn, del Apache clásico en modo `prefork`, y de PostgreSQL.

Combinado con `SO_REUSEPORT` (arriba) y con threads o asyncio dentro de cada worker, es la arquitectura estándar de un servidor Python moderno.

---

## Medir de verdad: latencia de cola

El benchmark de la clase reporta mínima, mediana y máxima. En producción eso no alcanza: lo que importa son los **percentiles altos**.

```python
import statistics

def percentil(datos, p):
    """Percentil p (0-100) de una lista ya ordenada."""
    k = (len(datos) - 1) * p / 100
    f, c = int(k), min(int(k) + 1, len(datos) - 1)
    return datos[f] + (datos[c] - datos[f]) * (k - f)

latencias = sorted(mediciones)
print(f'p50: {percentil(latencias, 50):.3f}s')
print(f'p95: {percentil(latencias, 95):.3f}s')
print(f'p99: {percentil(latencias, 99):.3f}s')
```

La razón: si tu p50 es 10 ms pero tu p99 es 3 segundos, uno de cada cien usuarios tiene una experiencia pésima. Y en una página que hace 100 peticiones, **casi todos los usuarios** pegan al menos una vez en ese p99.

Es lo que Google llamó *the tail at scale*: a escala, la cola de la distribución deja de ser un caso raro y pasa a ser la experiencia típica.

Herramientas serias para esto: `wrk`, `wrk2` (corrige el *coordinated omission*), `hey`, `ab`.

---

## Coordinated omission

Un sesgo que arruina la mayoría de los benchmarks caseros, incluido el de esta clase.

Si tu cliente hace "mandar petición → esperar respuesta → mandar la siguiente", entonces cuando el servidor se pone lento **el cliente también manda más despacio**. Las peticiones que deberían haberse enviado durante la lentitud simplemente no se envían, y no se registran. El resultado subestima la latencia real, a veces por órdenes de magnitud.

Un cliente correcto manda a **tasa constante**, independientemente de si el servidor responde, y mide desde el momento en que la petición *debería* haber salido.

`wrk2` existe precisamente para esto. Si alguna vez comparás números tuyos contra los publicados por un proyecto, verificá primero si miden lo mismo.

---

## Lecturas

- [The C10K problem](http://www.kegel.com/c10k.html) - Dan Kegel, 1999. El texto que definió el campo
- [The Secret to 10 Million Concurrent Connections](http://highscalability.com/blog/2013/5/13/the-secret-to-10-million-concurrent-connections-the-kernel-i.html) - la secuela: C10M
- [The Tail at Scale](https://research.google/pubs/the-tail-at-scale/) - Dean & Barroso, sobre por qué importan los percentiles altos
- [How is SO_REUSEPORT implemented](https://lwn.net/Articles/542629/) - LWN sobre el reparto de conexiones en el kernel
- Stevens, *UNIX Network Programming, Vol. 1*, capítulo 30 - compara nueve arquitecturas de servidor con mediciones
- [Gunicorn design](https://docs.gunicorn.org/en/stable/design.html) - el modelo pre-fork explicado por sus autores

---

*Computación II - 2026 - Clase 14*
