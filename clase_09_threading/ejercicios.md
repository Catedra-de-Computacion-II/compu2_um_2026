# Clase 9: Threads - Ejercicios Prácticos

> Los ejercicios cubren el material visto en clase: creación de threads, GIL,
> race conditions, `Lock`, `Queue`, `threading.local()` y daemons.
> Los ejercicios sobre `Condition`, `Event`, `Semaphore` y `Barrier` están
> en las clases 10 y 11.

---

## Ejercicio 1: Primer hilo

**Objetivo:** Crear y lanzar tu primer hilo en Python.

**Consigna:**
Escribí un programa que lance 3 hilos en paralelo. Cada hilo debe imprimir su nombre y un número del 1 al 5, con una pausa de 0.2 segundos entre cada número. El programa principal debe esperar a que todos los hilos terminen antes de imprimir "Listo".

**Pista:** Usá `threading.Thread(target=..., args=...)` y `h.join()`.

<details>
<summary>Ver solución</summary>

```python
import threading
import time

def imprimir_numeros(nombre):
    for i in range(1, 6):
        print(f"[{nombre}] número: {i}")
        time.sleep(0.2)

hilos = [
    threading.Thread(target=imprimir_numeros, args=(f"Hilo-{i}",))
    for i in range(1, 4)
]

for h in hilos:
    h.start()

for h in hilos:
    h.join()

print("Listo")
```
</details>

---

## Ejercicio 2: Comparar tiempos (I/O-bound)

**Objetivo:** Entender el beneficio de threading en tareas I/O-bound.

**Consigna:**
Implementá una función `simular_descarga(url, demora)` que simule descargar un archivo esperando `demora` segundos. Luego:

1. Ejecutá las descargas de forma **secuencial** para 5 URLs con demoras de 1 segundo cada una. Medí el tiempo total.
2. Ejecutá las mismas descargas en **paralelo con threading**. Medí el tiempo total.
3. Imprimí ambos tiempos y el factor de mejora.

**Resultado esperado:** La versión con threading debería ser ~5x más rápida.

<details>
<summary>Ver solución</summary>

```python
import threading
import time

URLS = [f"http://servidor.com/archivo_{i}.zip" for i in range(5)]
DEMORA = 1  # segundos por descarga

def simular_descarga(url, demora):
    time.sleep(demora)
    print(f"Descargado: {url}")

# Secuencial
inicio = time.perf_counter()
for url in URLS:
    simular_descarga(url, DEMORA)
tiempo_secuencial = time.perf_counter() - inicio
print(f"\nSecuencial: {tiempo_secuencial:.2f}s")

# Paralelo con threading
inicio = time.perf_counter()
hilos = [
    threading.Thread(target=simular_descarga, args=(url, DEMORA))
    for url in URLS
]
for h in hilos: h.start()
for h in hilos: h.join()
tiempo_paralelo = time.perf_counter() - inicio
print(f"Threading:  {tiempo_paralelo:.2f}s")
print(f"Mejora:     {tiempo_secuencial / tiempo_paralelo:.1f}x")
```
</details>

---

## Ejercicio 3: GIL en acción (CPU-bound)

**Objetivo:** Demostrar empíricamente que los threads no escalan para CPU-bound (con GIL activo).

**Consigna:** ejecutá una tarea CPU-intensive (ej: sumar raíces cuadradas de 1 a N) de forma secuencial, con 2 threads y con 4 threads. Compará los tiempos. Deberías observar que threads **no mejora** (o incluso empeora) frente a secuencial.

<details>
<summary>Ver solución</summary>

```python
import threading
import time
import math

def cpu_task(n):
    return sum(math.sqrt(i) for i in range(n))

N = 5_000_000

# Secuencial
inicio = time.perf_counter()
for _ in range(4):
    cpu_task(N)
print(f"Secuencial:  {time.perf_counter() - inicio:.2f}s")

# Con 4 threads
inicio = time.perf_counter()
hilos = [threading.Thread(target=cpu_task, args=(N,)) for _ in range(4)]
for h in hilos: h.start()
for h in hilos: h.join()
print(f"4 threads:   {time.perf_counter() - inicio:.2f}s")
```

Probá lo mismo reemplazando `threading` por `multiprocessing.Process` y vas a ver el speedup real.
</details>

---

## Ejercicio 4: Clase Thread personalizada

**Objetivo:** Crear hilos usando herencia de `threading.Thread`.

**Consigna:**
Creá una clase `ContadorHilo` que herede de `threading.Thread`. El hilo debe:
- Recibir un `nombre` y un `limite` en el constructor
- Contar de 1 hasta `limite` con una pausa de 0.1s entre cada número
- Al terminar, guardar el resultado en un atributo `resultado` como string con todos los números separados por coma

Lanzá 3 instancias con diferentes límites y al final imprimí el resultado de cada una.

<details>
<summary>Ver solución</summary>

```python
import threading
import time

class ContadorHilo(threading.Thread):
    def __init__(self, nombre, limite):
        super().__init__(name=nombre)
        self.limite = limite
        self.resultado = ""

    def run(self):
        numeros = []
        for i in range(1, self.limite + 1):
            numeros.append(str(i))
            time.sleep(0.1)
        self.resultado = ", ".join(numeros)

hilos = [
    ContadorHilo(f"Contador-{i}", limite)
    for i, limite in enumerate([5, 8, 3], 1)
]

for h in hilos: h.start()
for h in hilos: h.join()

for h in hilos:
    print(f"[{h.name}] resultado: {h.resultado}")
```
</details>

---

## Ejercicio 5: Race condition y Lock

**Objetivo:** Observar una race condition y corregirla con Lock.

**Consigna:**
Tenés el siguiente código con race condition:

```python
import threading

saldo = 1000

def retirar(monto):
    global saldo
    if saldo >= monto:
        import time; time.sleep(0.001)  # simular procesamiento
        saldo -= monto
        print(f"Retiro de ${monto} exitoso. Saldo: ${saldo}")
    else:
        print(f"Saldo insuficiente para retirar ${monto}")
```

1. Ejecutá 10 hilos intentando retirar $200 cada uno simultáneamente. Observá que el saldo puede volverse negativo.
2. Corregí el código usando `threading.Lock()` para que el saldo nunca sea negativo.

<details>
<summary>Ver solución</summary>

```python
import threading
import time

# Versión CON race condition
saldo_inseguro = 1000

def retirar_inseguro(monto):
    global saldo_inseguro
    if saldo_inseguro >= monto:
        time.sleep(0.001)
        saldo_inseguro -= monto

hilos = [threading.Thread(target=retirar_inseguro, args=(200,)) for _ in range(10)]
for h in hilos: h.start()
for h in hilos: h.join()
print(f"Saldo inseguro final: ${saldo_inseguro} (puede ser negativo)")

# Versión CORREGIDA con Lock
saldo_seguro = 1000
lock = threading.Lock()

def retirar_seguro(monto):
    global saldo_seguro
    with lock:
        if saldo_seguro >= monto:
            time.sleep(0.001)
            saldo_seguro -= monto
            print(f"Retiro de ${monto} OK. Saldo: ${saldo_seguro}")
        else:
            print(f"Saldo insuficiente para ${monto}. Saldo: ${saldo_seguro}")

hilos = [threading.Thread(target=retirar_seguro, args=(200,)) for _ in range(10)]
for h in hilos: h.start()
for h in hilos: h.join()
print(f"Saldo seguro final: ${saldo_seguro}")
```
</details>

---

## Ejercicio 6: Hilos daemon

**Objetivo:** Comprender el comportamiento de los hilos daemon.

**Consigna:**
Creá dos programas:

1. **Sin daemon**: lanzá un hilo que hace un loop infinito imprimiendo "trabajando..." cada segundo. Observá que el programa no termina (terminalo con Ctrl+C).
2. **Con daemon**: hacé lo mismo pero con `daemon=True`. Observá que el programa termina después de 3 segundos del programa principal.

<details>
<summary>Ver solución</summary>

```python
import threading
import time

def loop_infinito(label):
    while True:
        print(f"[{label}] trabajando...")
        time.sleep(1)

# Versión sin daemon (descomentar para probar, terminar con Ctrl+C)
# h = threading.Thread(target=loop_infinito, args=("no-daemon",))
# h.start()
# time.sleep(3)
# print("Main terminó pero el programa sigue vivo")

# Versión con daemon
h = threading.Thread(target=loop_infinito, args=("daemon",), daemon=True)
h.start()

time.sleep(3)
print("Main terminó: el daemon muere automáticamente")
```
</details>

---

## Ejercicio 7: Productor-Consumidor con Queue

**Objetivo:** Practicar comunicación entre threads con `queue.Queue`.

**Consigna:** implementá un sistema de procesamiento de imágenes (simulado) con:
- Una función `procesar_imagen(nombre)` que tarda 0.5 segundos
- Un pool de **4 workers** que procesan imágenes de una cola
- 20 imágenes para procesar (`imagen_001.jpg` a `imagen_020.jpg`)
- Al final, imprimí cuántas procesó cada worker y el tiempo total

<details>
<summary>Ver solución</summary>

```python
import threading
import queue
import time

resultados = {}
resultados_lock = threading.Lock()

def procesar_imagen(nombre):
    time.sleep(0.5)
    return f"{nombre} -> procesada"

def worker(q, worker_id):
    contador = 0
    while True:
        imagen = q.get()
        if imagen is None:
            break
        resultado = procesar_imagen(imagen)
        print(f"Worker-{worker_id}: {resultado}")
        contador += 1
        q.task_done()

    with resultados_lock:
        resultados[f"Worker-{worker_id}"] = contador

cola = queue.Queue()

workers = [
    threading.Thread(target=worker, args=(cola, i))
    for i in range(4)
]
for w in workers: w.start()

inicio = time.perf_counter()
for i in range(1, 21):
    cola.put(f"imagen_{i:03d}.jpg")

cola.join()

for _ in workers:
    cola.put(None)
for w in workers:
    w.join()

tiempo = time.perf_counter() - inicio
print(f"\nTiempo total: {tiempo:.2f}s")
print("\nImagenes por worker:")
for nombre, cant in resultados.items():
    print(f"  {nombre}: {cant} imágenes")
```
</details>

---

## Ejercicio 8: `threading.local()` para contexto por hilo

**Objetivo:** Usar `threading.local()` para aislar estado entre hilos.

**Consigna:**
Simulá un servidor web simple donde cada hilo atiende un "request" diferente. Cada request tiene su propio `usuario`, `ip` y `timestamp`. Usá `threading.local()` para que cada hilo tenga su propio contexto sin interferir con los demás. Implementá una función `get_contexto()` que retorne el contexto del hilo actual.

<details>
<summary>Ver solución</summary>

```python
import threading
import time
import random

contexto = threading.local()

def get_contexto():
    return {
        "usuario": getattr(contexto, "usuario", None),
        "ip": getattr(contexto, "ip", None),
        "timestamp": getattr(contexto, "timestamp", None),
    }

def atender_request(request_id):
    contexto.usuario = f"user_{random.randint(1000, 9999)}"
    contexto.ip = f"192.168.{random.randint(0,255)}.{random.randint(0,255)}"
    contexto.timestamp = time.time()

    print(f"Request {request_id} iniciando | contexto: {get_contexto()}")
    time.sleep(random.uniform(0.1, 0.5))

    print(f"Request {request_id} finalizando | usuario: {contexto.usuario}")

hilos = [
    threading.Thread(target=atender_request, args=(i,), name=f"Request-{i}")
    for i in range(6)
]

for h in hilos: h.start()
for h in hilos: h.join()

print("\nTodos los requests atendidos")
```
</details>

---

## Ejercicio 9: Descargador paralelo (Obligatorio)

**Objetivo:** Construir un descargador real de URLs usando threads.

**Consigna:** dado un conjunto de URLs, descargarlas en paralelo usando un pool fijo de threads (sin `ThreadPoolExecutor`, que se ve en clase 23). Usá `threading.Thread` y `queue.Queue`. Manejar errores de red. Mostrar estadísticas al final.

```python
import threading
import queue
import urllib.request
import urllib.error
import time

def worker(in_q, out_list, lock):
    while True:
        url = in_q.get()
        if url is None:
            in_q.task_done()
            break
        inicio = time.time()
        try:
            response = urllib.request.urlopen(url, timeout=10)
            datos = response.read()
            with lock:
                out_list.append({
                    "url": url,
                    "ok": True,
                    "bytes": len(datos),
                    "tiempo": time.time() - inicio,
                })
        except Exception as e:
            with lock:
                out_list.append({
                    "url": url,
                    "ok": False,
                    "error": str(e),
                    "tiempo": time.time() - inicio,
                })
        in_q.task_done()

if __name__ == "__main__":
    urls = [
        "https://www.python.org",
        "https://docs.python.org",
        "https://pypi.org",
        "https://www.google.com",
        "https://www.github.com",
    ]
    NUM_WORKERS = 4

    in_q = queue.Queue()
    resultados = []
    lock = threading.Lock()

    workers = [
        threading.Thread(target=worker, args=(in_q, resultados, lock))
        for _ in range(NUM_WORKERS)
    ]
    for w in workers: w.start()

    inicio = time.time()
    for url in urls:
        in_q.put(url)

    # Señales de fin
    for _ in workers:
        in_q.put(None)

    for w in workers:
        w.join()

    tiempo_total = time.time() - inicio

    ok = sum(1 for r in resultados if r["ok"])
    bytes_total = sum(r.get("bytes", 0) for r in resultados)
    print(f"\nDescargas exitosas: {ok}/{len(urls)}")
    print(f"Bytes totales: {bytes_total:,}")
    print(f"Tiempo total: {tiempo_total:.2f}s")
```

### Verificación

Tu implementación debe:
- Usar un pool fijo de workers (no crear un thread por URL)
- Descargar URLs en paralelo
- Manejar errores de red sin crashear
- Mostrar estadísticas finales

---

## Ejercicios adicionales

### Chat multi-hilo (sin sincronización avanzada)

Implementá un programa donde múltiples "usuarios" (threads) envían mensajes a una `queue.Queue` central, y un thread "display" los muestra a medida que llegan.

### Monitor de sistema simple

Lanzá 3 threads daemon que cada N segundos imprimen métricas simuladas (CPU, memoria, disco). El programa principal duerme 10 segundos y termina, llevándose los daemons.

### Crawler básico

Dada una URL inicial, descargá la página, extraé los enlaces y descargá cada enlace en threads separados con un pool de tamaño limitado.

---

*Computación II - 2026 - Clase 9*
