# Clase 20: Asyncio en red - Ejercicios Prácticos

Los archivos `eco_async.py`, `descargas.py` y `escala.py` acompañan la clase.

Para la parte de HTTP real hace falta `httpx`:

```bash
pip install httpx
```

---

## Ejercicio 1: El servidor eco

```bash
python3 eco_async.py
```

Conectate con varios `nc localhost 8080` en terminales distintas.

### 1.1 Un hilo, muchos clientes

1. Mirá la salida del servidor. ¿Cuántos threads reporta con tres clientes conectados?
2. Compará con `server_threads.py` de la clase 14: contá los threads ahí con `ls /proc/$(pgrep -f server_threads)/task | wc -l`.
3. ¿Qué es una conexión en cada caso: un thread o un objeto?

### 1.2 El servidor no se bloquea

```bash
python3 eco_async.py --lento 3
```

4. Conectá dos clientes y escribí en ambos. ¿El segundo espera a que el primero reciba su respuesta?
5. ¿Por qué el `await asyncio.sleep(3)` no congela a los demás?
6. Cambiá ese `await asyncio.sleep(demora)` por `time.sleep(demora)` y repetí. ¿Qué cambia? Explicá.

### 1.3 Cierre ordenado

7. Con clientes conectados, mandale `SIGTERM` al servidor: `kill -TERM $(pgrep -f eco_async)`. ¿Qué imprime?
8. Mirá `loop.add_signal_handler()` en el código. ¿En qué se diferencia de `signal.signal()` de la clase 6?
9. ¿Por qué esa diferencia importa? Relacionalo con async-signal-safety.

---

## Ejercicio 2: write, drain y el framing

### 2.1 La asimetría

1. ¿Por qué `writer.write()` no lleva `await` y `writer.drain()` sí?
2. Sacá el `await writer.drain()` del servidor. ¿Sigue funcionando con `nc`?
3. Entonces, ¿para qué sirve? Escribí un cliente que mande 100 MB sin leer nunca la respuesta, y observá la memoria del servidor con y sin `drain()`.

### 2.2 Las formas de leer

Probá las cuatro con un cliente que mande `'hola\nmundo\n'`:

```python
await reader.read(100)
await reader.readline()
await reader.readexactly(4)
await reader.readuntil(b'\n')
```

4. ¿Cuál devuelve qué? Anotá los cuatro resultados.
5. ¿Cuáles corresponden a los dos framings de la clase 13?
6. ¿Qué pasa con `readexactly(100)` si el cliente manda menos y cierra? ¿Qué excepción?
7. ¿Qué devuelve `read()` cuando el cliente cerró? ¿Te suena de la clase 13?

---

## Ejercicio 3: Concurrencia de clientes (obligatorio)

### Objetivo

Descargar muchas cosas a la vez, acotando la concurrencia y manejando fallos.

### Parte A: medir la diferencia

```bash
python3 descargas.py
```

1. Copiá los cuatro tiempos. ¿Por qué `gather` tarda lo que la más lenta y no la suma?
2. ¿Por qué el semáforo da un tiempo intermedio?
3. Con el timeout de 0.8s, ¿cuántas se cancelaron? ¿Qué les pasó a esas tareas?

### Parte B: con HTTP real

Reemplazá la simulación por descargas de verdad:

```python
import httpx, asyncio

async def bajar(cliente, url):
    r = await cliente.get(url)
    return url, r.status_code, len(r.content)

async def main():
    urls = ['https://example.com'] * 10
    async with httpx.AsyncClient(timeout=10) as cliente:
        resultados = await asyncio.gather(*(bajar(cliente, u) for u in urls))
```

4. Medí 10 descargas secuenciales contra 10 concurrentes. ¿Cuánto mejora?
5. ¿Por qué el `AsyncClient` se crea **una vez** y no uno por descarga? (Pista: keep-alive, clase 19.)
6. Cambiá `httpx` por `requests` dentro de la corrutina. ¿Qué pasa con los tiempos? Explicá con lo de la clase 19.

### Parte C: acotar

7. Agregá un `Semaphore(3)` y volvé a medir. ¿Cuál es el nuevo tiempo?
8. ¿Qué problema evita acotar la concurrencia? Nombrá dos.
9. Probá con 200 URLs sin semáforo. ¿Qué error aparece? (Pista: `ulimit -n`.)

### Parte D: fallos

10. Agregá una URL inválida a la lista. Con `gather` normal, ¿qué pasa con las demás?
11. Probá `asyncio.gather(..., return_exceptions=True)`. ¿Qué cambia?
12. ¿Cuál de los dos comportamientos querés para el TP2? Justificá.

---

## Ejercicio 4: Locks, o su ausencia

### 4.1 Cuándo no hacen falta

```python
contador = 0

async def sumar():
    global contador
    contador += 1
```

1. Lanzá 1000 tareas de `sumar()` con `gather`. ¿El contador queda en 1000?
2. Hacé lo mismo con 1000 threads (clase 11). ¿Da lo mismo?
3. ¿Por qué con corrutinas no hace falta `Lock`?

### 4.2 Cuándo sí

```python
async def transferir(origen, destino, monto):
    saldo = cuentas[origen]
    await asyncio.sleep(0)            # un punto de suspensión en el medio
    cuentas[origen] = saldo - monto
```

4. Lanzá 100 transferencias concurrentes sobre la misma cuenta. ¿El saldo final es correcto?
5. ¿Por qué ahora sí hay race condition, si sigue siendo un solo hilo?
6. Arreglalo con `asyncio.Lock`. ¿Por qué `async with` y no `with`?
7. Escribí la regla en una frase: ¿cuándo hace falta un lock en asyncio?

---

## Ejercicio 5: Timeouts y cancelación

### 5.1 Timeout

```python
async with asyncio.timeout(2):
    await operacion_lenta()
```

1. ¿Qué excepción lanza si vence?
2. ¿Qué le pasa a `operacion_lenta()` cuando vence el timeout: sigue corriendo o se cancela?
3. Compará con `asyncio.wait_for()`. ¿Hacen lo mismo?

### 5.2 Cancelación

4. Corré la última parte de `descargas.py`. Anotá el orden de los tres mensajes.
5. ¿En qué momento exacto recibe la tarea el `CancelledError`?
6. Escribí una corrutina que calcule sin ningún `await` durante 5 segundos e intentá cancelarla. ¿Funciona? ¿Por qué?
7. ¿Qué pasa si capturás `CancelledError` y **no** la relanzás? Probalo y describí el síntoma.
8. ¿Por qué `CancelledError` hereda de `BaseException` y no de `Exception`?

---

## Ejercicio 6: La escala

```bash
python3 escala.py
python3 escala.py 2000 5000
```

1. Copiá la tabla. ¿Cuántos threads usa el proceso?
2. ¿Hasta cuántos clientes aguanta tu máquina? ¿Qué falla primero?
3. Mirá tu `ulimit -n`. ¿Se relaciona con el techo que encontraste?
4. Estimá cuánta memoria habrían usado esos clientes como threads (4 MB de stack cada uno).
5. Escribí un párrafo, con tus números, explicando por qué asyncio resuelve el problema C10K de la clase 14.

---

## Verificación del ejercicio obligatorio

### Ejercicio 3: Concurrencia de clientes

- [ ] Medición de secuencial contra `gather`, con números propios
- [ ] Explicaste por qué `gather` tarda lo que la más lenta
- [ ] Descargas reales con `httpx` y `AsyncClient` reutilizado
- [ ] Probaste qué pasa con `requests` adentro de una corrutina
- [ ] Implementaste el semáforo y mediste el efecto
- [ ] Nombraste dos problemas que evita acotar la concurrencia
- [ ] Probaste `return_exceptions=True` y elegiste cuál conviene para el TP2

---

## Ejercicios adicionales

### El chat, otra vez

Reescribí `chat.py` de la clase 17 con asyncio. Vas a necesitar mantener el conjunto de `writer` conectados y escribir a todos cuando llega un mensaje. ¿Cuál de las dos versiones es más legible?

### El servidor de comandos

Tomá `comandos.py` de la clase 16 (`socketserver`) y pasalo a asyncio. Compará el manejo de estado compartido: ¿sigue haciendo falta el `Lock`?

### Proxy asíncrono

Un servidor que acepte conexiones y reenvíe todo a otro host, en ambos sentidos a la vez. Vas a necesitar dos tareas por conexión y cancelar una cuando la otra termine.

### El esqueleto del TP2

Con lo de hoy y la clase 19 ya podés armar la estructura: una API FastAPI que encola tareas, y workers asyncio que las consumen. La cola y el pool los vemos la clase que viene, pero la parte de red ya la tenés.

---

*Computación II - 2026 - Clase 20*
