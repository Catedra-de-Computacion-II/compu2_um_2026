# Clase 5: Señales - Ejercicios Prácticos

## Ejercicio 1: Explorando señales desde la terminal

### 1.1 Listando señales del sistema

```bash
# Ver todas las señales disponibles
kill -l

# Ver descripción de señales (si está disponible)
man 7 signal
```

### 1.2 Enviando señales a procesos

Abrí dos terminales. En la primera:

```bash
# Crear un proceso que duerme mucho
sleep 1000
```

En la segunda terminal:

```bash
# Encontrar el PID
pgrep sleep
# o
ps aux | grep sleep

# Enviar SIGSTOP (pausar)
kill -STOP <pid>

# El proceso en la primera terminal se pausa

# Enviar SIGCONT (continuar)
kill -CONT <pid>

# El proceso continúa

# Finalmente, terminar con SIGTERM
kill <pid>

# Si no termina, usar SIGKILL
kill -9 <pid>
```

### 1.3 Observando señales con strace

```bash
# Ver las señales que recibe un proceso
strace -e trace=signal python3 -c "import time; time.sleep(10)" &
kill -USR1 $!
```

---

## Ejercicio 2: Manejadores básicos

### 2.1 Capturar Ctrl+C

```python
#!/usr/bin/env python3
"""Capturar SIGINT (Ctrl+C)."""
import signal
import time

contador_ctrl_c = 0

def manejador_sigint(sig, frame):
    global contador_ctrl_c
    contador_ctrl_c += 1
    print(f"\n¡Ctrl+C detectado! (vez #{contador_ctrl_c})")

    if contador_ctrl_c >= 3:
        print("OK, OK, me voy...")
        raise SystemExit(0)
    else:
        print(f"Presioná {3 - contador_ctrl_c} veces más para salir")

signal.signal(signal.SIGINT, manejador_sigint)

print("Presioná Ctrl+C (3 veces para salir)")
print("Observá cómo el programa no termina la primera vez")

while True:
    print(".", end="", flush=True)
    time.sleep(0.5)
```

### 2.2 SIGTERM para shutdown limpio

```python
#!/usr/bin/env python3
"""Shutdown limpio con SIGTERM."""
import signal
import sys
import time
import os

class Aplicacion:
    def __init__(self):
        self.ejecutando = True
        self.recursos = []

        # Registrar manejadores
        signal.signal(signal.SIGTERM, self.shutdown)
        signal.signal(signal.SIGINT, self.shutdown)

    def shutdown(self, sig, frame):
        nombre_señal = signal.Signals(sig).name
        print(f"\nRecibí {nombre_señal}, cerrando...")
        self.ejecutando = False

    def adquirir_recurso(self, nombre):
        print(f"Adquiriendo recurso: {nombre}")
        self.recursos.append(nombre)

    def liberar_recursos(self):
        for recurso in reversed(self.recursos):
            print(f"Liberando recurso: {recurso}")
            time.sleep(0.3)
        self.recursos.clear()

    def run(self):
        print(f"PID: {os.getpid()}")
        print("Enviá 'kill <pid>' para terminar limpiamente")

        # Simular adquisición de recursos
        self.adquirir_recurso("base_de_datos")
        self.adquirir_recurso("archivo_log")
        self.adquirir_recurso("conexion_red")

        # Loop principal
        while self.ejecutando:
            print("Trabajando...")
            time.sleep(1)

        # Cleanup
        self.liberar_recursos()
        print("Aplicación terminada correctamente")

if __name__ == "__main__":
    app = Aplicacion()
    app.run()
```

---

## Ejercicio 3: Comunicación padre-hijo con señales

### 3.1 Padre envía señal al hijo

```python
#!/usr/bin/env python3
"""Padre envía comandos al hijo vía señales."""
import os
import signal
import time

pid = os.fork()

if pid == 0:
    # === HIJO ===
    contador = 0

    def incrementar(sig, frame):
        global contador
        contador += 1
        print(f"[HIJO] Contador incrementado: {contador}")

    def mostrar(sig, frame):
        print(f"[HIJO] Valor actual: {contador}")

    signal.signal(signal.SIGUSR1, incrementar)
    signal.signal(signal.SIGUSR2, mostrar)

    print(f"[HIJO] PID={os.getpid()}, esperando señales...")

    while True:
        signal.pause()  # Esperar señales

else:
    # === PADRE ===
    time.sleep(0.5)  # Dar tiempo al hijo

    print("[PADRE] Enviando SIGUSR1 (incrementar) x3")
    for _ in range(3):
        os.kill(pid, signal.SIGUSR1)
        time.sleep(0.3)

    print("[PADRE] Enviando SIGUSR2 (mostrar)")
    os.kill(pid, signal.SIGUSR2)
    time.sleep(0.3)

    print("[PADRE] Enviando SIGUSR1 x2")
    for _ in range(2):
        os.kill(pid, signal.SIGUSR1)
        time.sleep(0.3)

    print("[PADRE] Enviando SIGUSR2 (mostrar)")
    os.kill(pid, signal.SIGUSR2)
    time.sleep(0.3)

    print("[PADRE] Terminando hijo")
    os.kill(pid, signal.SIGTERM)
    os.wait()
```

### 3.2 SIGCHLD para detectar hijos terminados

```python
#!/usr/bin/env python3
"""Usar SIGCHLD para detectar cuando terminan los hijos."""
import os
import signal
import time

hijos_activos = set()
resultados = {}

def sigchld_handler(sig, frame):
    """Recoger hijos terminados sin bloquear."""
    while True:
        try:
            pid, status = os.waitpid(-1, os.WNOHANG)
            if pid == 0:
                break
            hijos_activos.discard(pid)
            codigo = os.WEXITSTATUS(status) if os.WIFEXITED(status) else -1
            resultados[pid] = codigo
            # Nota: print no es async-signal-safe, pero funciona en Python
            print(f"[SIGCHLD] Hijo {pid} terminó con código {codigo}")
        except ChildProcessError:
            break

signal.signal(signal.SIGCHLD, sigchld_handler)

# Crear 5 hijos con diferentes duraciones
print("Creando 5 hijos...")
for i in range(5):
    pid = os.fork()
    if pid == 0:
        # Hijo
        duracion = (i + 1) * 0.5
        time.sleep(duracion)
        os._exit(i)
    else:
        hijos_activos.add(pid)
        print(f"Creado hijo {pid}, durará {(i+1)*0.5}s")

# El padre hace otras cosas mientras los hijos trabajan
print("\n[PADRE] Trabajando mientras los hijos se ejecutan...")
for tick in range(10):
    print(f"[PADRE] Tick {tick}, hijos activos: {len(hijos_activos)}")
    time.sleep(0.5)
    if not hijos_activos:
        break

print(f"\n[PADRE] Todos terminaron. Resultados: {resultados}")
```

---

## Ejercicio 4: Alarmas y timeouts

### 4.1 Timeout simple

```python
#!/usr/bin/env python3
"""Timeout usando SIGALRM."""
import signal

class Timeout(Exception):
    pass

def timeout_handler(sig, frame):
    raise Timeout("Operación excedió el tiempo límite")

def con_timeout(segundos):
    """Decorador para agregar timeout a una función."""
    def decorador(func):
        def wrapper(*args, **kwargs):
            old_handler = signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(segundos)
            try:
                return func(*args, **kwargs)
            finally:
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)
        return wrapper
    return decorador

# Uso
@con_timeout(3)
def operacion_lenta():
    import time
    print("Iniciando operación...")
    time.sleep(5)
    return "Completado"

@con_timeout(3)
def operacion_rapida():
    import time
    print("Iniciando operación...")
    time.sleep(1)
    return "Completado"

print("=== Operación rápida ===")
try:
    resultado = operacion_rapida()
    print(f"Resultado: {resultado}")
except Timeout as e:
    print(f"Timeout: {e}")

print("\n=== Operación lenta ===")
try:
    resultado = operacion_lenta()
    print(f"Resultado: {resultado}")
except Timeout as e:
    print(f"Timeout: {e}")
```

### 4.2 Timer periódico

```python
#!/usr/bin/env python3
"""Timer periódico con setitimer."""
import signal
import time
import os

class TimerPeriodico:
    def __init__(self, intervalo, callback):
        self.intervalo = intervalo
        self.callback = callback
        self.activo = False

    def _handler(self, sig, frame):
        if self.activo:
            self.callback()

    def iniciar(self):
        self.activo = True
        signal.signal(signal.SIGALRM, self._handler)
        signal.setitimer(signal.ITIMER_REAL, self.intervalo, self.intervalo)
        print(f"Timer iniciado (cada {self.intervalo}s)")

    def detener(self):
        self.activo = False
        signal.setitimer(signal.ITIMER_REAL, 0)
        print("Timer detenido")

# Uso
stats = {"operaciones": 0}

def mostrar_stats():
    print(f"[STATS] Operaciones hasta ahora: {stats['operaciones']}")

timer = TimerPeriodico(2.0, mostrar_stats)
timer.iniciar()

print("Simulando trabajo...")
print("Ctrl+C para terminar")

try:
    for i in range(20):
        stats["operaciones"] += 1
        time.sleep(0.5)
except KeyboardInterrupt:
    pass
finally:
    timer.detener()
    print(f"\nTotal de operaciones: {stats['operaciones']}")
```

---

## Ejercicio 5: Servidor con señales (Obligatorio)

### Objetivo

Crear un "servidor" simple que responda a diferentes señales:

- **SIGTERM/SIGINT:** Shutdown limpio
- **SIGHUP:** Recargar configuración
- **SIGUSR1:** Mostrar estadísticas
- **SIGUSR2:** Rotar logs (simular)

### Especificación

```python
#!/usr/bin/env python3
"""
Servidor que responde a señales.
Uso:
    python3 servidor_signals.py

Señales:
    kill -HUP <pid>   -> Recargar config
    kill -USR1 <pid>  -> Mostrar stats
    kill -USR2 <pid>  -> Rotar logs
    kill <pid>        -> Shutdown limpio
"""
import signal
import sys
import time
import os

class Servidor:
    def __init__(self):
        self.ejecutando = True
        self.config = {"max_conexiones": 100, "timeout": 30}
        self.stats = {"requests": 0, "errores": 0, "inicio": time.time()}

        self._registrar_manejadores()

    def _registrar_manejadores(self):
        signal.signal(signal.SIGTERM, self._shutdown)
        signal.signal(signal.SIGINT, self._shutdown)
        signal.signal(signal.SIGHUP, self._reload_config)
        signal.signal(signal.SIGUSR1, self._mostrar_stats)
        signal.signal(signal.SIGUSR2, self._rotar_logs)

    def _shutdown(self, sig, frame):
        nombre = signal.Signals(sig).name
        print(f"\n[{nombre}] Iniciando shutdown...")
        self.ejecutando = False

    def _reload_config(self, sig, frame):
        print("\n[SIGHUP] Recargando configuración...")
        # Simular lectura de archivo de config
        self.config["max_conexiones"] += 10
        self.config["recargado"] = time.ctime()
        print(f"[SIGHUP] Nueva config: {self.config}")

    def _mostrar_stats(self, sig, frame):
        uptime = time.time() - self.stats["inicio"]
        print(f"\n[SIGUSR1] === Estadísticas ===")
        print(f"  Uptime: {uptime:.1f}s")
        print(f"  Requests: {self.stats['requests']}")
        print(f"  Errores: {self.stats['errores']}")
        print(f"  Config: {self.config}")

    def _rotar_logs(self, sig, frame):
        print(f"\n[SIGUSR2] Rotando logs...")
        # Simular rotación de logs
        print(f"[SIGUSR2] Logs rotados a server.log.{int(time.time())}")

    def procesar_request(self):
        """Simula procesamiento de una request."""
        self.stats["requests"] += 1
        # Simular trabajo
        time.sleep(0.1)
        # Simular errores ocasionales
        if self.stats["requests"] % 10 == 0:
            self.stats["errores"] += 1

    def run(self):
        print(f"Servidor iniciado (PID {os.getpid()})")
        print("Comandos disponibles:")
        print(f"  kill -HUP {os.getpid()}   -> Recargar config")
        print(f"  kill -USR1 {os.getpid()}  -> Ver stats")
        print(f"  kill -USR2 {os.getpid()}  -> Rotar logs")
        print(f"  kill {os.getpid()}        -> Shutdown")
        print()

        while self.ejecutando:
            self.procesar_request()

        # Cleanup
        print("Realizando cleanup...")
        time.sleep(0.5)
        print(f"Servidor terminado. Requests procesadas: {self.stats['requests']}")

if __name__ == "__main__":
    servidor = Servidor()
    servidor.run()
```

### Pruebas

En una terminal ejecutá el servidor, en otra enviá señales:

```bash
# Mostrar stats
kill -USR1 <pid>

# Recargar config
kill -HUP <pid>

# Rotar logs
kill -USR2 <pid>

# Shutdown
kill <pid>
```

---

## Ejercicio 6: Pool de workers con señales

### 6.1 Supervisor que maneja workers

```python
#!/usr/bin/env python3
"""
Pool de workers supervisado con señales.
El supervisor reinicia workers que fallan.
"""
import os
import signal
import time
import random

class WorkerPool:
    def __init__(self, num_workers):
        self.num_workers = num_workers
        self.workers = {}  # pid -> info
        self.ejecutando = True

        signal.signal(signal.SIGTERM, self._shutdown)
        signal.signal(signal.SIGINT, self._shutdown)
        signal.signal(signal.SIGCHLD, self._sigchld)

    def _shutdown(self, sig, frame):
        print("\n[SUPERVISOR] Shutdown solicitado")
        self.ejecutando = False
        # Enviar SIGTERM a todos los workers
        for pid in list(self.workers.keys()):
            try:
                os.kill(pid, signal.SIGTERM)
            except ProcessLookupError:
                pass

    def _sigchld(self, sig, frame):
        while True:
            try:
                pid, status = os.waitpid(-1, os.WNOHANG)
                if pid == 0:
                    break
                if pid in self.workers:
                    info = self.workers.pop(pid)
                    codigo = os.WEXITSTATUS(status) if os.WIFEXITED(status) else -1
                    print(f"[SUPERVISOR] Worker {info['id']} (pid {pid}) terminó con código {codigo}")
            except ChildProcessError:
                break

    def _worker_main(self, worker_id):
        """Código que ejecuta cada worker."""
        print(f"[Worker {worker_id}] Iniciado (PID {os.getpid()})")

        # Manejador de señales del worker
        def worker_shutdown(sig, frame):
            print(f"[Worker {worker_id}] Recibí SIGTERM, terminando...")
            os._exit(0)

        signal.signal(signal.SIGTERM, worker_shutdown)

        # Simular trabajo
        for i in range(random.randint(5, 15)):
            print(f"[Worker {worker_id}] Trabajando... ({i})")
            time.sleep(0.5)

        # Simular fallo ocasional
        if random.random() < 0.3:
            print(f"[Worker {worker_id}] ¡Error simulado!")
            os._exit(1)

        print(f"[Worker {worker_id}] Trabajo completado")
        os._exit(0)

    def spawn_worker(self, worker_id):
        pid = os.fork()
        if pid == 0:
            self._worker_main(worker_id)
        else:
            self.workers[pid] = {"id": worker_id, "started": time.time()}
            print(f"[SUPERVISOR] Spawned worker {worker_id} (PID {pid})")

    def run(self):
        print(f"[SUPERVISOR] PID {os.getpid()}, iniciando {self.num_workers} workers")

        # Iniciar workers
        for i in range(self.num_workers):
            self.spawn_worker(i)

        # Loop supervisor: reiniciar workers caídos
        next_worker_id = self.num_workers
        while self.ejecutando:
            time.sleep(1)

            # ¿Necesitamos más workers?
            if len(self.workers) < self.num_workers and self.ejecutando:
                print(f"[SUPERVISOR] Solo {len(self.workers)} workers activos, spawneando más")
                self.spawn_worker(next_worker_id)
                next_worker_id += 1

        # Esperar que terminen todos
        while self.workers:
            time.sleep(0.1)

        print("[SUPERVISOR] Todos los workers terminados")

if __name__ == "__main__":
    pool = WorkerPool(3)
    pool.run()
```

---

## Verificación del ejercicio obligatorio

### Ejercicio 5: Servidor con señales

Tu implementación debe:

- [ ] Responder a SIGTERM/SIGINT con shutdown limpio
- [ ] Responder a SIGHUP recargando configuración
- [ ] Responder a SIGUSR1 mostrando estadísticas
- [ ] Responder a SIGUSR2 rotando logs (puede ser simulado)
- [ ] Mostrar el PID y los comandos disponibles al inicio
- [ ] Hacer cleanup antes de terminar

---

## Ejercicios adicionales

### Watchdog

Implementá un proceso watchdog que monitorea otro proceso y lo reinicia si termina inesperadamente.

### Rate limiter con señales

Usá SIGALRM para implementar un rate limiter que permita máximo N operaciones por segundo.

### Señales como comandos

Extendé el ejercicio 5 para usar múltiples instancias de SIGUSR1 como comandos (1 USR1 = acción A, 2 USR1 seguidos = acción B, etc.)

---

*Computación II - 2026 - Clase 5*
