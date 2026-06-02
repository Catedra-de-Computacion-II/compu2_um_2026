# Clase 9: Threads - Autoevaluación

> Completá esta autoevaluación **después** de leer el contenido y hacer los ejercicios.
> No mires las respuestas antes de intentarlo.

---

## Parte 1: Conceptos básicos

**Pregunta 1.** ¿Qué comparten los threads de un mismo proceso?

a) Solo el código
b) Memoria, file descriptors, espacio de direcciones
c) Nada, están completamente aislados
d) Solo las variables globales

**Pregunta 2.** ¿Qué tiene cada thread de forma independiente?

a) Todo - no comparten nada
b) Solo el PID
c) Stack, program counter, registros
d) Solo variables locales

**Pregunta 3.** ¿Qué módulo de Python se usa para crear threads?

a) `multiprocessing`
b) `thread`
c) `threading`
d) `concurrent`

**Pregunta 4.** ¿Qué método inicia la ejecución de un thread?

a) `run()`
b) `start()`
c) `begin()`
d) `execute()`

**Pregunta 5.** ¿Qué método espera a que un thread termine?

a) `wait()`
b) `join()`
c) `finish()`
d) `sync()`

**Pregunta 6.** ¿Qué es un daemon thread?

a) Un thread que corre con privilegios elevados
b) Un thread que se termina automáticamente cuando el programa principal termina
c) Un thread que no puede ser detenido
d) Un thread que corre en segundo plano en otra máquina

---

## Parte 2: El GIL

**Pregunta 7.** ¿Qué es el GIL en Python?

a) Un tipo especial de lock
b) Un mutex que impide que múltiples threads ejecuten bytecode Python simultáneamente
c) Una biblioteca de gráficos
d) Un garbage collector

**Pregunta 8.** ¿Para qué tipo de tareas los threads sí mejoran el rendimiento en Python (con GIL)?

a) Tareas CPU-bound (cálculos intensivos)
b) Tareas I/O-bound (red, disco)
c) Todas las tareas
d) Ninguna tarea

**Pregunta 9.** ¿Cuándo se libera el GIL?

a) Nunca
b) Durante operaciones de I/O
c) Solo manualmente
d) Cada segundo

**Pregunta 10.** ¿Qué alternativa usarías para tareas CPU-bound en Python con GIL?

a) Más threads
b) `multiprocessing`
c) No hay alternativa
d) `async/await`

**Pregunta 11.** ¿Por qué existe el GIL?

a) Para hacer Python más lento
b) Para proteger el reference counting del garbage collector
c) Por compatibilidad con Windows
d) No hay razón, es un bug

**Pregunta 12.** ¿Qué cambia con el "free-threaded Python" (PEP 703)?

a) Python es más rápido en todo
b) El GIL se puede deshabilitar al compilar, permitiendo verdadero paralelismo con threads (con un costo en single-threaded)
c) Se elimina el módulo threading
d) Solo funciona en Linux

**Pregunta 13.** A partir de qué versión el free-threaded Python dejó de ser experimental:

a) Python 3.12
b) Python 3.13
c) Python 3.14
d) Python 4.0

---

## Parte 3: Sincronización básica (Lock)

**Pregunta 14.** ¿Qué es una race condition?

a) Un tipo de competencia entre programas
b) Cuando múltiples threads acceden a datos compartidos sin sincronización
c) Cuando un thread es más rápido que otro
d) Un error de sintaxis

**Pregunta 15.** ¿Qué primitivo básico protege una sección crítica?

a) Queue
b) Event
c) Lock
d) Semaphore

**Pregunta 16.** ¿Cuál es la forma recomendada de usar un Lock en Python?

a) `lock.acquire()` y `lock.release()`
b) `with lock:`
c) `lock.enter()` y `lock.exit()`
d) `lock.lock()` y `lock.unlock()`

**Pregunta 17.** Si `contador += 1` no es atómico, ¿cuántas operaciones lo componen internamente?

a) 1 (es atómico)
b) 2 (sumar y escribir)
c) 3 (leer, sumar, escribir)
d) Depende del CPU

---

## Parte 4: Comunicación entre threads

**Pregunta 18.** ¿Qué ventaja tiene `queue.Queue` para comunicación entre threads?

a) Es más rápida
b) Es thread-safe por defecto
c) Usa menos memoria
d) No tiene ventajas especiales

**Pregunta 19.** ¿En qué situación usarías `threading.local()`?

a) Para variables que todos los threads comparten
b) Para que cada thread tenga su propia copia independiente de una variable
c) Para variables locales a una función
d) Para constantes

**Pregunta 20.** ¿Qué tipo de queue saca primero el ítem con menor valor numérico?

a) `Queue` (FIFO)
b) `LifoQueue`
c) `PriorityQueue`
d) `OrderedQueue`

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
| 1 | b | Memoria, file descriptors, espacio de direcciones |
| 2 | c | Stack, program counter, registros |
| 3 | c | `threading` |
| 4 | b | `start()` (run lo invoca start internamente) |
| 5 | b | `join()` |
| 6 | b | Thread que muere automáticamente con el programa principal |
| 7 | b | Mutex que impide ejecución paralela de bytecode Python |
| 8 | b | I/O-bound (red, disco) |
| 9 | b | Durante operaciones de I/O |
| 10 | b | `multiprocessing` |
| 11 | b | Para proteger el reference counting del GC |
| 12 | b | Free-threaded build: GIL opcional al compilar |
| 13 | c | Python 3.14 (PEP 779) |
| 14 | b | Acceso concurrente sin sincronización |
| 15 | c | Lock |
| 16 | b | `with lock:` |
| 17 | c | Leer, sumar, escribir |
| 18 | b | Thread-safe por diseño |
| 19 | b | Variable privada por hilo |
| 20 | c | `PriorityQueue` (menor valor primero) |

</details>

---

## Resultado de la autoevaluación

| Puntaje | Diagnóstico |
|---------|-------------|
| 27-30 correctas | Excelente dominio del tema. Avanzá a la clase 10 (Sincronización I) |
| 21-26 | Buen nivel. Repasá los temas donde fallaste |
| 14-20 | Nivel intermedio. Releé el contenido y hacé los ejercicios básicos primero |
| < 14 | Repasá el contenido completo. Consultá con el docente antes de la próxima clase |

---

*Computación II - 2026 - Clase 9*
