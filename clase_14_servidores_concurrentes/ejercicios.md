# Clase 14: Servidores Concurrentes - Ejercicios Prácticos

Todos los ejercicios necesitan **dos o tres terminales**. Los archivos `server_secuencial.py`, `server_threads.py`, `server_fork.py`, `server_pool.py` y `benchmark.py` acompañan la clase.

Todos los servidores aceptan las mismas opciones:

```bash
python3 server_X.py [puerto] [--lento SEGUNDOS] [--workers N]
```

`--lento` simula trabajo por cliente. Es lo que hace visibles las diferencias: sin él, casi cualquier arquitectura parece buena.

---

## Ejercicio 1: Medir las cuatro estrategias

### 1.1 La línea de base

```bash
# Terminal 1
python3 server_secuencial.py --lento 1

# Terminal 2
python3 benchmark.py --clientes 20
```

1. ¿Cuánto tardó el total? ¿Coincide con lo que esperabas?
2. Mirá la latencia mínima y la máxima. ¿Por qué son tan distintas?
3. El benchmark imprime una nota cuando detecta atención en serie. ¿Qué patrón está detectando?

### 1.2 Las tres concurrentes

Repetí exactamente lo mismo contra `server_threads.py`, `server_fork.py` y `server_pool.py`, siempre con `--lento 1` y 20 clientes.

4. Completá la tabla con tus números:

| Servidor | Tiempo total | Latencia máx | Throughput |
|---|---|---|---|
| Secuencial | | | |
| Threads | | | |
| Fork | | | |
| Pool (20) | | | |

5. ¿Por qué las tres concurrentes dan prácticamente lo mismo con 20 clientes?
6. Ahora corré todo de nuevo **sin** `--lento`. ¿Se distinguen las estrategias? ¿Por qué el parámetro cambia tanto las conclusiones?

### 1.3 Escala

7. Con `server_threads.py --lento 1`, subí los clientes: 50, 100, 200, 500, 1000. ¿Dónde empieza a degradarse?
8. Hacé lo mismo con `server_fork.py`. ¿Aguanta lo mismo? ¿Por qué la diferencia?
9. Mirá `ulimit -n` en tu máquina. ¿El techo que encontraste tiene que ver con ese número, o llegaste antes por otra razón?

---

## Ejercicio 2: El pool que satura

```bash
python3 server_pool.py --workers 5 --lento 1
python3 benchmark.py --clientes 20
```

1. ¿Cuánto tardó? Relacioná el número con la cantidad de workers y de clientes.
2. Mirá la latencia mínima y la máxima. ¿Cuántos "escalones" hay?
3. ¿Algún cliente fue **rechazado**? Distinguí entre rechazado y demorado.
4. Probá `--workers 1`. ¿A qué otra estrategia se parece el resultado?
5. Un pool acota el consumo de recursos, que es deseable. Pero con conexiones persistentes tiene el problema que acabás de medir. ¿Para qué tipo de carga sí es la herramienta correcta?

---

## Ejercicio 3: Los tres descuidos del fork (obligatorio)

### Objetivo

Comprobar empíricamente por qué las tres líneas "de más" de `server_fork.py` no son opcionales.

### Parte A: el padre que no cierra

Copiá `server_fork.py` y **comentá** la línea `conn.close()` de la rama del padre (solo esa; el hijo conserva la suya).

```python
else:
    # ---- PADRE ----
    # conn.close()      # <-- comentada a propósito
```

Levantá el servidor y, desde otra terminal, contá los descriptores del **padre** mientras corre el benchmark:

```bash
ls /proc/<PID_DEL_PADRE>/fd | wc -l
python3 benchmark.py --clientes 30      # repetir varias veces
```

1. ¿Crece el número de descriptores? Anotá lo que observás antes de seguir.

**Lo que vas a ver es que no crece** — y la razón es más interesante que el bug:

```python
import socket, gc, os
def make():
    x = socket.socket()
    return x.fileno()
fd = make()
gc.collect()
os.fstat(fd)      # OSError: el fd ya está cerrado
```

2. Ejecutá ese fragmento. ¿Quién cerró el descriptor, si nadie llamó a `close()`?
3. En el bucle `while True` del servidor, la variable `conn` se reasigna en cada vuelta. ¿Qué le pasa al objeto socket de la vuelta anterior?
4. Entonces: ¿el `conn.close()` del padre es innecesario en Python? Antes de responder, pensá en estos tres casos:
   - El mismo servidor escrito en C, donde `accept()` devuelve un `int` y no hay recolector.
   - Un padre que guarda las conexiones en una lista (`activas.append(conn)`) para llevar estadísticas.
   - Una implementación de Python sin conteo de referencias, como PyPy, donde la recolección es diferida.
5. Reescribí la conclusión con tus palabras: ¿por qué sigue siendo correcto escribir el `close()` explícito aunque CPython te cubra?

### Parte A2: el cierre que sí se nota

El efecto que el descriptor filtrado esconde sí se puede observar. Modificá el padre para que **guarde** las conexiones en vez de cerrarlas:

```python
conexiones_abiertas = []      # a nivel de módulo
...
else:
    # ---- PADRE ----
    conexiones_abiertas.append(conn)    # ahora la referencia sobrevive
```

6. Corré el benchmark y volvé a contar descriptores. ¿Ahora sí crecen?
7. Conectate con `nc localhost 8080` y matá el proceso **hijo** que te atiende (buscalo con `ps --ppid <PID_PADRE>`). ¿El cliente ve que la conexión se cerró? ¿Por qué no?
8. Explicá el mecanismo: ¿cuántas copias del descriptor existen tras el `fork()`, y cuándo se cierra realmente la conexión TCP?

### Parte B: los zombies

Reemplazá el handler de `SIGCHLD` por nada:

```python
# signal.signal(signal.SIGCHLD, cosechar)
```

4. Corré el benchmark con 50 clientes y después:

```bash
ps --ppid <PID_DEL_PADRE> -o pid,stat,comm
```

¿Qué estado tienen los hijos? (Pista: la columna `STAT`, y lo que vimos en la clase 4.)

5. Contá cuántos hay. Corré el benchmark otra vez. ¿Se acumulan?
6. ¿Qué pasaría con un servidor así corriendo durante semanas?

### Parte C: el bucle del cosechador

Volvé a poner el handler, pero sacale el `while`:

```python
def cosechar(signum, frame):
    try:
        os.waitpid(-1, os.WNOHANG)    # sin bucle: recoge UN hijo por señal
    except ChildProcessError:
        pass
```

7. Corré el benchmark con 50 clientes y contá zombies. Probablemente veas **cero**: los clientes terminan escalonados, así que las señales llegan de a una y un handler sin bucle da abasto.

Para provocar el fallo hay que hacer que muchos hijos mueran **exactamente a la vez**. Usá este script en vez del servidor:

```python
#!/usr/bin/env python3
import os, signal, subprocess, time

recogidos = [0]

def cosechar(signum, frame):
    try:
        pid, _ = os.waitpid(-1, os.WNOHANG)   # SIN bucle
        if pid > 0:
            recogidos[0] += 1
    except ChildProcessError:
        pass

signal.signal(signal.SIGCHLD, cosechar)

N = 60
for _ in range(N):
    if os.fork() == 0:
        time.sleep(0.5)     # todos duermen lo mismo: mueren juntos
        os._exit(0)

time.sleep(2.0)
salida = subprocess.run(['ps', '--ppid', str(os.getpid()), '-o', 'stat='],
                        capture_output=True, text=True).stdout
zombies = sum(1 for l in salida.splitlines() if l.strip().startswith('Z'))
print(f'hijos={N}  recogidos={recogidos[0]}  zombies={zombies}')
```

8. Corrélo **varias veces**. ¿Siempre da el mismo resultado?
9. Agregale el bucle `while True` al handler y volvé a correrlo varias veces. ¿Qué cambia?
10. ¿Por qué el fallo es intermitente? Relacionalo con el hecho de que las señales **no se encolan**: si llegan dos `SIGCHLD` antes de que el handler corra, el proceso ve una sola.
11. ¿Qué hace exactamente `WNOHANG`, y qué pasaría sin él dentro de un handler de señal?
12. Un bug que aparece en 2 de cada 3 corridas y solo bajo carga: ¿cómo lo encontrarías en un servidor en producción?

### Parte D: la alternativa

10. Reemplazá todo el handler por `signal.signal(signal.SIGCHLD, signal.SIG_IGN)`. ¿Siguen apareciendo zombies? ¿Quién los está recogiendo ahora?

---

## Ejercicio 4: Race conditions reales

`server_threads.py` mantiene un contador de clientes activos protegido con un lock.

1. Sacá el `with lock:` de las dos secciones donde se modifica `clientes_activos`.
2. Corré el benchmark con 200 clientes varias veces. ¿El contador vuelve a cero al final?
3. Si no falla, subí a 500 o 1000 clientes y agregá un `time.sleep(0.0001)` entre la lectura y la escritura. ¿Ahora sí?
4. Explicá por qué `clientes_activos += 1` no es atómico, conectándolo con lo que vimos en la clase 11.
5. ¿Por qué la versión con `fork()` no necesita este lock?

---

## Ejercicio 5: socketserver

Reescribí el servidor eco usando `socketserver.ThreadingTCPServer`.

```python
import socketserver

class EchoHandler(socketserver.StreamRequestHandler):
    def handle(self):
        # TODO
        pass

class Servidor(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True
```

1. Hacelo funcionar y medilo con el benchmark. ¿Cómo se compara con tu `server_threads.py`?
2. `self.rfile` y `self.wfile` son objetos tipo archivo. ¿Qué problema de la clase 13 resuelven gratis?
3. Cambiá `ThreadingTCPServer` por `ForkingTCPServer`. ¿Qué cambia en la medición?
4. Mirá el código fuente de `socketserver` (`python3 -c "import socketserver; print(socketserver.__file__)"`). Buscá el bucle de `accept()`. ¿Se parece a lo que escribimos a mano?
5. ¿Qué justifica haber escrito las estrategias a mano si esto ya existía?

---

## Ejercicio 6: Un servidor que hace trabajo real

Hasta acá el "trabajo" era un `sleep`, que es I/O-bound simulado. Ahora probemos con CPU real.

Modificá `atender()` para que haga algo que consuma CPU:

```python
def trabajo_cpu(n=2_000_000):
    """CPU-bound de verdad: no libera el GIL."""
    total = 0
    for i in range(n):
        total += i * i
    return total
```

1. Medí `server_threads.py` con esa carga y 10 clientes. ¿Escala?
2. Medí `server_fork.py` con la misma carga. ¿Y ahora?
3. Explicá la diferencia. ¿Cuántos núcleos tiene tu máquina (`nproc`)?
4. Verificá si tu Python tiene GIL:

```bash
python3 -c "import sys; print('con GIL' if sys._is_gil_enabled() else 'SIN GIL')"
```

5. Si tuvieras un build free-threaded, ¿qué esperarías que cambiara en el punto 1? ¿Y qué **no** cambiaría respecto del fork?

---

## Verificación del ejercicio obligatorio

### Ejercicio 3: Los tres descuidos del fork

- [ ] Mostrar el crecimiento de descriptores cuando el padre no cierra `conn`
- [ ] Explicar por qué el cliente no ve el cierre de la conexión
- [ ] Mostrar zombies acumulándose sin handler de `SIGCHLD`
- [ ] Mostrar que un cosechador sin bucle deja zombies bajo carga
- [ ] Explicar qué hace `WNOHANG` y por qué es necesario
- [ ] Verificar que `SIG_IGN` también funciona, y decir quién cosecha en ese caso

---

## Ejercicios adicionales

### Límite de conexiones

Agregale al servidor de threads un tope de clientes simultáneos: pasado el límite, responder "servidor ocupado" y cerrar en vez de aceptar. Es lo que hace un servidor real bajo presión.

### Servidor con estadísticas

Extendé el servidor de threads para que responda a un comando `STATS` con: clientes activos, total atendidos, bytes transferidos y uptime. Cuidado con las race conditions.

### Comparar contra nginx

Instalá nginx, servile un archivo estático y medilo con `ab` o `wrk`. Compará el throughput con tu mejor servidor Python. La diferencia es la clase 17 en números.

### Cierre ordenado

Los `daemon_threads` se cortan de golpe al salir. Implementá un shutdown que espere a que los clientes actuales terminen (con timeout) antes de cerrar, usando `threading.Event` de la clase 11.

---

*Computación II - 2026 - Clase 14*
