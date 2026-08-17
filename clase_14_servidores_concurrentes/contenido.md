# Clase 14: Servidores Concurrentes

## Introducción: la deuda de la clase anterior

Terminamos la clase 13 con un servidor que funciona y no sirve.

```python
while True:
    conn, direccion = servidor.accept()
    with conn:
        atender(conn)              # <-- mientras esto corre, nadie más entra
```

Mientras `atender()` conversa con un cliente, el bucle no vuelve a `accept()`. Los demás se acumulan en la cola de `listen()`, y cuando se llena, empiezan a rebotar. Con un eco instantáneo casi no se nota; con un cliente que tarda diez segundos, el servidor está muerto diez segundos.

Esta clase resuelve eso, y para hacerlo vuelve sobre casi todo el bloque de concurrencia local: procesos (clase 4), pools (clase 9) y threads (clase 10). Buena parte del sentido de aquellas clases se termina de ver acá, aplicada a un problema concreto.

Vamos a implementar cuatro estrategias, medirlas, y ver dónde se rompe cada una. Porque todas se rompen: la pregunta no es cuál es la buena, sino cuál sirve para qué carga.

> **Nota:** los archivos `server_secuencial.py`, `server_threads.py`, `server_fork.py`, `server_pool.py` y `benchmark.py` acompañan la clase. El benchmark es el corazón de todo esto: los números que vas a ver en tu máquina son el argumento.

---

## Por qué la concurrencia sirve acá

Antes de elegir herramienta conviene entender qué tipo de trabajo estamos repartiendo.

Un servidor de red pasa la enorme mayoría del tiempo **esperando**: que llegue un `recv()`, que el cliente piense, que se vacíe un buffer. No calculando. Es trabajo **I/O-bound**, y en la clase 10 vimos que ahí los threads de Python funcionan bien, porque **el GIL se libera durante las operaciones de I/O**.

Esa es la diferencia clave con lo que vimos en threading. Diez threads sumando números compiten por el GIL y no ganan nada. Diez threads bloqueados en `recv()` no compiten por nada: el GIL está libre mientras esperan.

| Tipo de trabajo | Threads con GIL | Threads free-threaded | Procesos |
|---|---|---|---|
| CPU-bound (calcular) | No sirven | Sí | Sí |
| I/O-bound (red, disco) | **Sí sirven** | Sí | Sí, pero más caros |

Un servidor típico es I/O-bound. Por eso los threads son la primera opción razonable, y no lo eran en la clase 10.

Ojo con el matiz: si tu servidor además **procesa** lo que recibe (comprime, cifra, calcula), esa parte sí es CPU-bound. En un build con GIL eso vuelve a ser un cuello de botella; en uno free-threaded, no. Los servidores reales suelen ser una mezcla de ambos tipos de trabajo.

### El GIL ya no es la única historia

Acá conviene actualizar algo respecto de lo que dice la clase 10.

El free-threading (Python sin GIL) **dejó de ser experimental**. La secuencia:

| Versión | Estado del free-threading |
|---|---|
| 3.13 (2024) | Fase I: build experimental (`--disable-gil`) |
| **3.14 (2025)** | **Fase II: oficialmente soportado**, build separado y opcional |
| Futuro | Fase III: sería el build por defecto. Sin fecha ni PEP todavía |

El paso de experimental a soportado lo formalizó el [PEP 779](https://peps.python.org/pep-0779/), aprobado por el Steering Council en junio de 2025. "Soportado pero opcional" significa que hay que instalar el build free-threaded explícitamente; el binario que baja la mayoría de la gente **sigue teniendo GIL**.

Verificá qué tenés:

```bash
python3 -c "import sys; print('con GIL' if sys._is_gil_enabled() else 'SIN GIL')"
```

```python
import sysconfig
print(sysconfig.get_config_var('Py_GIL_DISABLED'))   # 1 = build free-threaded
```

Qué implica para esta clase:

- **Para I/O-bound, no cambia nada.** Los threads ya funcionaban bien con GIL, porque se libera esperando. Todo lo que sigue vale igual en los dos builds.
- **Para CPU-bound, cambia todo.** En un build free-threaded, los threads sí aprovechan varios núcleos, y el argumento "usá procesos para esquivar el GIL" pierde fuerza.
- **El costo:** una penalización de entre 5 y 10 por ciento en código de un solo hilo, y extensiones en C que pueden necesitar adaptación.

**En esta materia asumimos el build con GIL**, que es el que van a tener instalado y el que usa el Docker de la cátedra. Pero cuando comparemos threads contra procesos más abajo, tengan presente que la respuesta a "¿por qué procesos para CPU-bound?" tiene fecha de vencimiento.

---

## Estrategia 1: un thread por cliente

La traducción más directa de la idea "que cada cliente tenga su propio flujo de ejecución".

```python
#!/usr/bin/env python3
"""Servidor eco: un thread por cliente."""
import socket
import threading

def atender(conn, direccion):
    """Corre en su propio thread, uno por cliente."""
    with conn:
        while True:
            datos = conn.recv(4096)
            if not datos:
                break
            conn.sendall(datos)
    print(f'[{direccion}] desconectado')

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as servidor:
    servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    servidor.bind(('0.0.0.0', 8080))
    servidor.listen(128)

    while True:
        conn, direccion = servidor.accept()
        hilo = threading.Thread(target=atender, args=(conn, direccion),
                                daemon=True)
        hilo.start()
        # El bucle vuelve INMEDIATAMENTE a accept()
```

El cambio respecto del secuencial son tres líneas. El bucle principal ahora solo acepta y delega; la conversación ocurre en otro lado.

### Qué tener en cuenta

**`daemon=True`** hace que los threads no impidan que el programa termine. Sin eso, un Ctrl+C deja el proceso colgado esperando a que todos los clientes se vayan. La contrapartida es que al salir se los corta de golpe; si necesitás un cierre ordenado, hay que coordinarlo explícitamente.

**Cada thread consume memoria.** El stack por defecto en Linux es de 8 MB de espacio virtual (bastante menos de memoria real efectiva). Con cientos de clientes se nota; con decenas de miles, no hay máquina que aguante.

**El estado compartido vuelve a ser peligroso.** Si los threads tocan una estructura común —un contador de conexiones, una lista de clientes, un log— estamos exactamente en el escenario de la clase 11:

```python
clientes_activos = 0
lock = threading.Lock()

def atender(conn, direccion):
    global clientes_activos
    with lock:                      # sin esto, race condition
        clientes_activos += 1
    try:
        ...
    finally:
        with lock:
            clientes_activos -= 1
```

Este es el punto donde sincronización deja de ser un ejercicio de clase y pasa a ser una necesidad.

---

## Estrategia 2: un proceso por cliente (fork)

El patrón clásico de Unix, anterior a que los threads existieran. Es como funcionaban históricamente Apache, sendmail y el `inetd`.

```python
#!/usr/bin/env python3
"""Servidor eco: un proceso por cliente, con fork()."""
import os
import signal
import socket

def atender(conn):
    while True:
        datos = conn.recv(4096)
        if not datos:
            break
        conn.sendall(datos)

# Evitar procesos zombie: el kernel se encarga de los hijos terminados.
signal.signal(signal.SIGCHLD, signal.SIG_IGN)

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as servidor:
    servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    servidor.bind(('0.0.0.0', 8080))
    servidor.listen(128)
    print(f'PADRE pid={os.getpid()}')

    while True:
        conn, direccion = servidor.accept()
        pid = os.fork()

        if pid == 0:
            # ---- HIJO ----
            servidor.close()        # el hijo NO necesita el socket que escucha
            atender(conn)
            conn.close()
            os._exit(0)             # salir sin ejecutar cleanup del padre
        else:
            # ---- PADRE ----
            conn.close()            # el padre NO necesita el socket del cliente
            print(f'Cliente {direccion} atendido por hijo pid={pid}')
```

### Los tres detalles que casi todos olvidan

Este código tiene tres líneas que parecen redundantes y no lo son. Las tres producen bugs difíciles si faltan.

**1. El padre tiene que cerrar `conn`.**

Después de `fork()`, el descriptor está abierto **en los dos procesos**. La conexión TCP no se cierra hasta que se cierran todas las copias. Si el padre no cierra la suya, el cliente nunca ve el fin de la conexión y el descriptor queda filtrado en el padre. Con suficientes clientes, el padre se queda sin descriptores y el servidor deja de aceptar.

**2. El hijo tiene que cerrar `servidor`.**

Menos grave, pero igual de real: el hijo hereda el socket que escucha y no lo necesita. Mantenerlo abierto complica el cierre ordenado del servidor.

**3. Los zombies.**

Cuando un hijo termina, queda como **zombie** hasta que el padre llame a `wait()` — exactamente lo que vimos en la clase 4. Un servidor que forkea sin recoger a sus hijos acumula entradas en la tabla de procesos hasta agotarla.

`signal.signal(signal.SIGCHLD, signal.SIG_IGN)` le dice al kernel que se ocupe él. La alternativa explícita es un handler:

```python
def cosechar(signum, frame):
    """Recoge todos los hijos terminados sin bloquear."""
    while True:
        try:
            pid, status = os.waitpid(-1, os.WNOHANG)
            if pid == 0:
                break
        except ChildProcessError:
            break

signal.signal(signal.SIGCHLD, cosechar)
```

El `WNOHANG` es lo que hace que no bloquee, y el bucle es necesario porque **las señales no se encolan**: si dos hijos mueren antes de que el handler corra, el proceso recibe un solo `SIGCHLD`. Un handler que recoge un único hijo por señal deja los demás como zombies.

Medido con 60 hijos muriendo simultáneamente: sin el bucle quedan zombies en la mayoría de las corridas (2, 4, a veces 0); con el bucle, siempre 0. Es un bug intermitente y dependiente de la carga — de los peores de diagnosticar.

### Ventajas y desventajas frente a threads

**A favor:** aislamiento real. Si un cliente provoca un crash, se lleva puesto solo a su proceso; el servidor sigue. No hay estado compartido, así que no hay race conditions. Y no hay GIL: si el trabajo por cliente es CPU-bound, esto escala en varios núcleos donde los threads con GIL no pueden.

> Ese último argumento es el que está cambiando: en un build free-threaded los threads también escalan en varios núcleos. El aislamiento ante crashes, en cambio, sigue siendo exclusivo de los procesos — y esa ventaja no caduca.

**En contra:** un proceso es mucho más caro que un thread —memoria, tiempo de creación, cambios de contexto—. Y compartir estado entre clientes requiere IPC explícito (clases 7 a 9), no una variable global.

---

## Estrategia 3: pool de threads

Las dos estrategias anteriores tienen el mismo defecto de fondo: **crean un recurso por cliente, sin techo**. Diez mil clientes, diez mil threads. Es una invitación a que un pico de tráfico voltee la máquina.

Un pool fija la cantidad de workers de antemano.

### Interludio: `concurrent.futures`

En el ejercicio obligatorio de la clase 10 construyeron un pool de threads a mano: unos cuantos `threading.Thread` consumiendo URLs de una `queue.Queue`, con su lógica de arranque, de parada y de recolección de resultados. Funcionaba, y valía la pena escribirlo para entender qué hay adentro.

La biblioteca estándar ya trae eso resuelto en `concurrent.futures`, y acá lo necesitamos. La clase 23 lo retoma en profundidad —`ProcessPoolExecutor`, `map`, `as_completed`, manejo de excepciones—; por ahora alcanza con tres ideas.

**Un `Executor` es un pool de workers con una cola adentro.** Se crea diciendo cuántos workers querés:

```python
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=4) as pool:
    ...
# al salir del with, espera a que terminen todas las tareas pendientes
```

**`submit()` encola una tarea y devuelve enseguida.** No espera a que se ejecute:

```python
futuro = pool.submit(mi_funcion, arg1, arg2)   # vuelve inmediatamente
```

**Un `Future` es el resultado que todavía no está.** Es un recibo: podés preguntarle si terminó, o pedirle el valor (y ahí sí se bloquea hasta que esté):

```python
futuro.done()      # ¿ya terminó? True/False, no bloquea
futuro.result()    # el valor devuelto; BLOQUEA hasta que esté listo
```

Comparado con lo que escribieron en la clase 10: `ThreadPoolExecutor` es la `queue.Queue` más los threads más el arranque y la parada, en una línea. Los workers se reutilizan entre tareas, así que no se paga la creación de un thread por cada una.

Un detalle que va a importar enseguida: **si la tarea lanza una excepción, no explota nada visible.** La excepción queda guardada dentro del `Future` y solo aparece cuando alguien llama a `result()`. En un servidor que nunca mira los `Future`, un error desaparece sin dejar rastro.

### El servidor con pool

```python
#!/usr/bin/env python3
"""Servidor eco con pool de threads acotado."""
import socket
from concurrent.futures import ThreadPoolExecutor

MAX_WORKERS = 20

def atender(conn, direccion):
    with conn:
        while True:
            datos = conn.recv(4096)
            if not datos:
                break
            conn.sendall(datos)

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as servidor:
    servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    servidor.bind(('0.0.0.0', 8080))
    servidor.listen(128)

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        while True:
            conn, direccion = servidor.accept()
            pool.submit(atender, conn, direccion)
```

El consumo de recursos ahora tiene un techo conocido, y no hay que pagar la creación de un thread por conexión: los workers se reutilizan.

### El problema del pool con conexiones persistentes

Acá hay una trampa que conviene ver antes de chocarse con ella.

Si cada cliente mantiene la conexión abierta —como hace nuestro eco, que conversa hasta que el cliente se va— entonces **cada cliente ocupa un worker durante toda su sesión**. Con `max_workers=20`, el cliente 21 no es atendido hasta que alguno de los 20 se desconecte. No fue rechazado: quedó esperando en la cola del pool, invisible.

Es el mismo problema del servidor secuencial, solo que corrido veinte lugares.

Los pools funcionan bien cuando las tareas son **cortas y acotadas**: una petición, una respuesta, se libera el worker. Es el modelo de HTTP sin keep-alive. Para conexiones largas hacen falta otras herramientas.

Y acá se ve el problema de los `Future` que mencionamos arriba: este servidor **nunca llama a `result()`**, así que si `atender()` explota, el error queda guardado en un `Future` que nadie mira. El servidor sigue como si nada y el cliente ve una conexión cortada sin explicación. Conviene envolver:

```python
def atender_seguro(conn, direccion):
    try:
        atender(conn, direccion)
    except Exception as e:
        print(f'[{direccion}] error: {e}')
```

---

## Estrategia 4: socketserver

La biblioteca estándar ya trae todo esto resuelto:

```python
#!/usr/bin/env python3
"""Servidor eco con socketserver."""
import socketserver

class EchoHandler(socketserver.StreamRequestHandler):
    def handle(self):
        """Se llama una vez por conexión, en su propio thread."""
        for linea in self.rfile:            # framing por líneas, gratis
            self.wfile.write(linea)

class Servidor(socketserver.ThreadingTCPServer):
    allow_reuse_address = True              # equivale a SO_REUSEADDR
    daemon_threads = True

with Servidor(('0.0.0.0', 8080), EchoHandler) as srv:
    srv.serve_forever()
```

Diez líneas para lo que veníamos escribiendo a mano. `ThreadingTCPServer` usa un thread por cliente; `ForkingTCPServer` usa un proceso.

`self.rfile` y `self.wfile` son objetos tipo archivo sobre el socket —el `makefile()` que vimos en la clase 13—, así que el framing por líneas viene incluido.

### Entonces, ¿para qué escribimos lo anterior?

Porque `socketserver` es una caja negra hasta que algo falla. Cuando tu servidor pierde conexiones bajo carga, cuando los threads se acumulan, cuando aparece un descriptor filtrado, el diagnóstico requiere saber qué está haciendo por dentro. Y lo que hace por dentro es, casi literalmente, el código de las estrategias 1 y 2.

Además `socketserver` está algo anticuado y tiene limitaciones (no maneja bien miles de conexiones, la configuración es por herencia de clases). En producción moderna se usa asyncio o un framework. Pero para un servidor chico es perfectamente razonable, y evita reescribir código ya resuelto.

---

## Medir: el benchmark

Todo lo anterior son afirmaciones. Veámoslas.

`benchmark.py` lanza N clientes simultáneos contra un servidor, cada uno manda un mensaje, espera el eco y mide cuánto tardó. Reporta cuántos completaron, el tiempo total y las latencias.

```bash
# Terminal 1
python3 server_secuencial.py

# Terminal 2
python3 benchmark.py --clientes 50
```

Repetilo contra cada servidor levantado con `--lento 1`. Estos son números reales de una corrida con **20 clientes**:

| Servidor | Tiempo total | Latencia máxima | Throughput |
|---|---|---|---|
| Secuencial | **20,02 s** | 20,00 s | 1,0 clientes/s |
| Threads | 1,02 s | 1,01 s | 19,7 clientes/s |
| Fork | 1,04 s | 1,02 s | 19,3 clientes/s |
| Pool (20 workers) | 1,02 s | 1,01 s | 19,6 clientes/s |

Veinte veces más lento, exactamente. No es casualidad: 20 clientes × 1 segundo cada uno, en serie.

Fijate también en la **latencia máxima** del secuencial. No es que todos hayan tardado 20 segundos: el primer cliente tardó 1 y el último 20. Esa escalera es la firma de un servidor que atiende de a uno, y el benchmark la detecta y la reporta.

Y el pool saturado, con `--workers 5` contra 20 clientes:

| | Medido |
|---|---|
| Tiempo total | 4,01 s |
| Latencia mínima | 1,00 s |
| Latencia máxima | 4,00 s |

Cuatro tandas de cinco. Nadie fue rechazado; los últimos quince simplemente esperaron su turno.

Vale la pena que corras el benchmark subiendo la cantidad de clientes hasta que algo se rompa. En la máquina donde se probó esto, 200 clientes concurrentes contra el servidor de threads completaron en 1,13 s sin un solo fallo — el techo está bastante más arriba de lo que uno esperaría, y encontrarlo es el argumento para la clase 17.

---

## Dónde se rompe cada una

Ninguna de las cuatro estrategias escala indefinidamente. Los límites:

**Threads**: cada uno reserva stack y compite por el planificador. En el orden de los miles, el costo de los cambios de contexto empieza a dominar y el rendimiento cae. Es el fenómeno del *thrashing*.

**Procesos**: lo mismo pero antes, porque un proceso es más caro que un thread.

**Pool**: no se rompe, se satura. Es lo que uno quiere de un sistema bajo carga —degradar de forma predecible en vez de colapsar— pero significa que hay clientes esperando.

**Todas**: hay un límite duro de descriptores de archivo por proceso.

```bash
ulimit -n
```

Cada conexión consume uno. El valor varía muchísimo entre sistemas: el clásico es 1024, pero muchas distribuciones modernas y entornos con systemd traen cientos de miles. Mirá el tuyo antes de suponer dónde está el techo.

Ese límite se puede subir, pero no es infinito — y aunque lo fuera, el costo de los threads o procesos llega primero.

### El problema C10K

En 1999, Dan Kegel escribió un texto famoso preguntando cómo hacer para atender **diez mil conexiones simultáneas** en una sola máquina. Con un thread o un proceso por conexión, la respuesta era: no se puede.

La solución no fue hacer los threads más baratos, sino cambiar el modelo: **un solo hilo que atiende muchas conexiones**, preguntándole al sistema operativo cuáles tienen datos listos en vez de bloquearse en cada una.

Eso es I/O multiplexing, y es la clase 17. Es también la idea sobre la que está construido asyncio, y la razón por la que nginx maneja con un puñado de procesos lo que Apache necesitaba miles de threads para hacer.

---

## Cuál usar

| Situación | Estrategia |
|---|---|
| Pocos clientes, código simple | Threads, o `socketserver` |
| Trabajo CPU-bound por cliente | Procesos (o threads, si corrés free-threaded) |
| Necesitás aislamiento ante crashes | Procesos |
| Carga alta pero acotada, tareas cortas | Pool |
| Miles de conexiones simultáneas | Multiplexing / asyncio (clases 17+) |
| Estado compartido complejo | Threads (con locks) antes que procesos con IPC |

Para lo que van a escribir en esta materia, threads o `socketserver` alcanzan casi siempre. Lo importante es poder justificar la elección.

---

## Conceptos clave

1. **Un servidor de red es I/O-bound**: por eso los threads sirven acá, aunque no sirvieran en la clase 10. El GIL se libera esperando — y esto valía incluso antes del free-threading.
2. **El bucle de `accept()` tiene que delegar rápido**: cualquier trabajo dentro del bucle bloquea a los demás clientes.
3. **Con `fork()`, ambos procesos heredan el descriptor**: el padre cierra `conn`, el hijo cierra `servidor`. Si no, se filtran descriptores.
4. **Los hijos terminados son zombies hasta que alguien los recoja**: `SIGCHLD` ignorado o un handler con `WNOHANG`.
5. **Un pool acota los recursos, pero satura**: con conexiones persistentes, cada cliente ocupa un worker toda su sesión.
6. **Estado compartido entre threads necesita locks**: es la clase 11 aplicada.
7. **Ninguna estrategia llega a diez mil conexiones**: ese es el problema C10K, y se resuelve cambiando de modelo.
8. **El free-threading ya no es experimental**: desde Python 3.14 está oficialmente soportado, aunque el build por defecto sigue teniendo GIL. Para I/O-bound no cambia nada; para CPU-bound cambia el argumento a favor de los procesos.

---

## Preparación para la próxima clase

En la **clase 15 (UDP)** cambiamos de protocolo. Todo lo de sockets sigue valiendo, pero sin conexión: no hay `listen()`, no hay `accept()`, y un `sendto()` es un `recvfrom()`. Vamos a ver por qué eso simplifica algunas cosas y complica otras, y qué pasa cuando la red pierde paquetes de verdad.

Para llegar preparado:

- Corré el benchmark contra las cuatro estrategias y guardá los números.
- Asegurate de entender por qué el padre tiene que cerrar `conn` en la versión con `fork()`.

---

## Referencias

- [The C10K problem](http://www.kegel.com/c10k.html) - el texto de 1999 que definió el problema
- [PEP 779](https://peps.python.org/pep-0779/) - los criterios que llevaron al free-threading de experimental a soportado en 3.14
- [Python support for free threading](https://docs.python.org/3/howto/free-threading-python.html) - la guía oficial
- [`socketserver`](https://docs.python.org/3/library/socketserver.html) - documentación oficial
- [`concurrent.futures`](https://docs.python.org/3/library/concurrent.futures.html)
- Stevens, *UNIX Network Programming, Vol. 1* - capítulo 30, "Client/Server Design Alternatives": compara nueve estrategias con mediciones
- [Beej's Guide](https://beej.us/guide/bgnet/) - sección sobre servidores concurrentes

---

*Computación II - 2026 - Clase 14*
