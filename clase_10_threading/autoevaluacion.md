# Clase 10: Threads - Autoevaluación

> Completá esta autoevaluación **después** de leer el contenido y hacer los ejercicios.
> No mires las respuestas antes de intentarlo.

---

## Parte 1: Conceptos básicos

**Pregunta 1.** ¿Qué comparten los threads de un mismo proceso?

a) Nada, están completamente aislados
b) Solo el código
c) Memoria, file descriptors, espacio de direcciones
d) Solo las variables globales

**Pregunta 2.** ¿Qué tiene cada thread de forma independiente?

a) Solo variables locales
b) Stack, program counter, registros
c) Todo - no comparten nada
d) Solo el PID

**Pregunta 3.** ¿Qué módulo de Python se usa para crear threads?

a) `multiprocessing`
b) `concurrent`
c) `threading`
d) `thread`

**Pregunta 4.** ¿Qué método inicia la ejecución de un thread?

a) `run()`
b) `start()`
c) `begin()`
d) `execute()`

**Pregunta 5.** ¿Qué método espera a que un thread termine?

a) `sync()`
b) `finish()`
c) `wait()`
d) `join()`

**Pregunta 6.** ¿Qué es un daemon thread?

a) Un thread que no puede ser detenido
b) Un thread que corre en segundo plano en otra máquina
c) Un thread que corre con privilegios elevados
d) Un thread que se termina automáticamente cuando el programa principal termina

---

## Parte 2: El GIL

**Pregunta 7.** ¿Qué es el GIL en Python?

a) Un mutex que impide que múltiples threads ejecuten bytecode Python simultáneamente
b) Un garbage collector
c) Un tipo especial de lock
d) Una biblioteca de gráficos

**Pregunta 8.** ¿Para qué tipo de tareas los threads sí mejoran el rendimiento en Python (con GIL)?

a) Tareas CPU-bound (cálculos intensivos)
b) Tareas I/O-bound (red, disco)
c) Ninguna tarea
d) Todas las tareas

**Pregunta 9.** ¿Cuándo se libera el GIL?

a) Cada segundo
b) Nunca
c) Solo manualmente
d) Durante operaciones de I/O

**Pregunta 10.** ¿Qué alternativa usarías para tareas CPU-bound en Python con GIL?

a) No hay alternativa
b) Más threads
c) `async/await`
d) `multiprocessing`

**Pregunta 11.** ¿Por qué existe el GIL?

a) Por compatibilidad con Windows
b) Para hacer Python más lento
c) Para proteger el reference counting del garbage collector
d) No hay razón, es un bug

**Pregunta 12.** ¿Qué cambia con el "free-threaded Python" (PEP 703)?

a) Solo funciona en Linux
b) El GIL se puede deshabilitar al compilar, permitiendo verdadero paralelismo con threads (con un costo en single-threaded)
c) Python es más rápido en todo
d) Se elimina el módulo threading

**Pregunta 13.** A partir de qué versión el free-threaded Python dejó de ser experimental:

a) Python 4.0
b) Python 3.12
c) Python 3.14
d) Python 3.13

---

## Parte 3: Sincronización básica (Lock)

**Pregunta 14.** ¿Qué es una race condition?

a) Un error de sintaxis
b) Cuando un thread es más rápido que otro
c) Un tipo de competencia entre programas
d) Cuando múltiples threads acceden a datos compartidos sin sincronización

**Pregunta 15.** ¿Qué primitivo básico protege una sección crítica?

a) Semaphore
b) Queue
c) Lock
d) Event

**Pregunta 16.** ¿Cuál es la forma recomendada de usar un Lock en Python?

a) `lock.acquire()` y `lock.release()`
b) `lock.lock()` y `lock.unlock()`
c) `with lock:`
d) `lock.enter()` y `lock.exit()`

**Pregunta 17.** Si `contador += 1` no es atómico, ¿cuántas operaciones lo componen internamente?

a) 1 (es atómico)
b) Depende del CPU
c) 2 (sumar y escribir)
d) 3 (leer, sumar, escribir)

---

## Parte 4: Comunicación entre threads

**Pregunta 18.** ¿Qué ventaja tiene `queue.Queue` para comunicación entre threads?

a) Es thread-safe por defecto
b) No tiene ventajas especiales
c) Usa menos memoria
d) Es más rápida

**Pregunta 19.** ¿En qué situación usarías `threading.local()`?

a) Para variables locales a una función
b) Para que cada thread tenga su propia copia independiente de una variable
c) Para variables que todos los threads comparten
d) Para constantes

**Pregunta 20.** ¿Qué tipo de queue saca primero el ítem con menor valor numérico?

a) `Queue` (FIFO)
b) `OrderedQueue`
c) `LifoQueue`
d) `PriorityQueue`

---

## Parte 5: Razonamiento

**Pregunta 21.** ¿Qué imprime este programa? ¿Es el resultado determinista?

```python
import threading

resultado = []

def agregar(valor):
    resultado.append(valor)

hilos = [threading.Thread(target=agregar, args=(i,)) for i in range(5)]
for h in hilos: h.start()
for h in hilos: h.join()

print(sorted(resultado))
```

<details>
<summary>Ver respuesta</summary>

`sorted(resultado)` imprime `[0, 1, 2, 3, 4]` de forma determinista en cuanto a contenido, pero el orden de inserción en `resultado` no es determinista (depende del scheduling del SO).

Nota: `list.append()` en CPython es thread-safe en la práctica porque es atómico a nivel de bytecode, pero esto es un detalle de implementación y no debe asumirse en código portable.

</details>

**Pregunta 22.** Tenés que descargar 100 imágenes de internet. ¿Usarías `threading` o `multiprocessing`? ¿Por qué?

<details>
<summary>Ver respuesta</summary>

`threading` es la mejor opción. Descargar imágenes es **I/O-bound**: el programa pasa la mayor parte del tiempo esperando la respuesta de la red. Durante esa espera el GIL se libera y otros hilos pueden avanzar.

`multiprocessing` crearía procesos con overhead innecesario. Una alternativa aún mejor para este caso es `asyncio` (clases 19-21), pero `threading` con un pool de workers es simple y efectivo.

</details>

**Pregunta 23.** ¿Por qué este código puede ser peligroso?

```python
contador = 0
def incrementar():
    global contador
    for _ in range(1_000_000):
        contador += 1
```

<details>
<summary>Ver respuesta</summary>

`contador += 1` no es atómico. Internamente involucra leer el valor, sumarle 1 y escribirlo. Si dos threads ejecutan estos pasos intercalados, pueden leer el mismo valor inicial y "perder" un incremento. El contador final puede ser menor al esperado.

La solución es proteger la operación con un `Lock`.

</details>

---

## Parte 6: Verdadero o Falso

| # | Afirmación | V/F |
|---|------------|-----|
| 24 | El GIL impide completamente la concurrencia en Python | |
| 25 | `join()` hace que el hilo actual espere a que el hilo objetivo termine | |
| 26 | Los hilos dentro del mismo proceso no comparten memoria | |
| 27 | `queue.Queue` es thread-safe por diseño | |
| 28 | Un hilo daemon puede impedir que el programa termine | |
| 29 | El free-threaded Python (3.13+) ya es el default | |
| 30 | Con el GIL, los threads aprovechan múltiples cores para cálculos | |

<details>
<summary>Ver respuestas</summary>

| # | V/F | Justificación |
|---|-----|---------------|
| 24 | F | El GIL impide *paralelismo* (ejecución simultánea real), pero la *concurrencia* (intercalado de tareas) sigue siendo posible |
| 25 | V | El hilo que llama `h.join()` se bloquea hasta que `h` termina |
| 26 | F | Los hilos comparten el espacio de memoria del proceso |
| 27 | V | Usa locks internos para acceso thread-safe |
| 28 | F | Los daemon threads se terminan automáticamente con el programa principal |
| 29 | F | Es opcional ("supported" desde 3.14), pero no default. Hay que bajar/compilar el binario aparte |
| 30 | F | Con el GIL solo un thread ejecuta bytecode Python a la vez, independiente de cuántos cores haya |

</details>

---

## Respuestas (Parte 1 a 4)

<details>
<summary>Click para ver respuestas</summary>

| # | Resp | Explicación |
|---|------|-------------|
| 1 | c | Memoria, file descriptors, espacio de direcciones |
| 2 | b | Stack, program counter, registros |
| 3 | c | `threading` |
| 4 | b | `start()` (run lo invoca start internamente) |
| 5 | d | `join()` |
| 6 | d | Thread que muere automáticamente con el programa principal |
| 7 | a | Mutex que impide ejecución paralela de bytecode Python |
| 8 | b | I/O-bound (red, disco) |
| 9 | d | Durante operaciones de I/O |
| 10 | d | `multiprocessing` |
| 11 | c | Para proteger el reference counting del GC |
| 12 | b | Free-threaded build: GIL opcional al compilar |
| 13 | c | Python 3.14 (PEP 779) |
| 14 | d | Acceso concurrente sin sincronización |
| 15 | c | Lock |
| 16 | c | `with lock:` |
| 17 | d | Leer, sumar, escribir |
| 18 | a | Thread-safe por diseño |
| 19 | b | Variable privada por hilo |
| 20 | d | `PriorityQueue` (menor valor primero) |

</details>

---

## Resultado de la autoevaluación

| Puntaje | Diagnóstico |
|---------|-------------|
| 27-30 correctas | Excelente dominio del tema. Avanzá a la clase 11 (Sincronización) |
| 21-26 | Buen nivel. Repasá los temas donde fallaste |
| 14-20 | Nivel intermedio. Releé el contenido y hacé los ejercicios básicos primero |
| < 14 | Repasá el contenido completo. Consultá con el docente antes de la próxima clase |

---

*Computación II - 2026 - Clase 10*
