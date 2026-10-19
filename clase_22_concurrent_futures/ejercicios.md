# Clase 22: concurrent.futures - Ejercicios Prácticos

Los archivos `futuros.py`, `patrones.py` y `errores.py` acompañan la clase.

---

## Ejercicio 1: El Future por dentro

```bash
python3 futuros.py
```

### 1.1 Los estados

1. ¿Cuánto tardó `submit()` en volver? ¿Qué significa ese número?
2. El ejemplo usa `max_workers=1` a propósito. ¿Por qué hace falta para ver el estado `PENDING`?
3. Anotá los estados de las dos tareas en los tres momentos que imprime. ¿Cuándo pasó la segunda de `PENDING` a `RUNNING`?

### 1.2 Qué bloquea

4. ¿Cuánto tardaron `done()` y `result()`? Explicá la diferencia.
5. Escribí un bucle que haga `done()` cada 50 ms e imprima el estado hasta que termine. ¿Para qué serviría eso en un programa real?
6. ¿Qué devuelve `exception()` si la tarea terminó bien?

### 1.3 Cancelar

7. ¿Cuál de las dos tareas se pudo cancelar? ¿Por qué la otra no?
8. ¿Se puede interrumpir un thread que ya está ejecutando código? Buscá por qué Python no lo permite.
9. Compará con `cancel()` de asyncio (clase 21). ¿Por qué ahí sí funciona sobre una tarea en curso?

### 1.4 El timeout engañoso

10. Corré la cuarta sección. Después del `TimeoutError`, ¿la tarea se canceló?
11. Entonces, ¿de qué es el timeout de `result(timeout=...)`?
12. Si querés que la tarea efectivamente se detenga, ¿qué habría que hacer?

---

## Ejercicio 2: map contra as_completed (obligatorio)

### Objetivo

Entender que las dos corren igual de concurrente, pero entregan distinto.

### Parte A: medir

```bash
python3 patrones.py
```

1. Copiá los tiempos de las dos primeras secciones.
2. Con `map`, ¿a qué hora estuvo disponible el resultado de `rapida`? ¿Y cuándo estuvo realmente calculado?
3. ¿Por qué el **total** es el mismo en los dos casos, si la entrega es tan distinta?
4. Explicá en una frase qué garantiza `map` que `as_completed` no.

### Parte B: cuándo cada uno

Para cada caso, elegí y justificá:

5. Convertir una lista de 1000 URLs en una lista de códigos de estado, en el mismo orden.
6. Mostrar una barra de progreso mientras se procesan 1000 archivos.
7. Descargar 50 imágenes y guardarlas apenas lleguen.
8. Calcular el promedio de un cálculo aplicado a 100 números.

### Parte C: la correspondencia

9. Con `as_completed`, ¿cómo sabés de qué entrada era cada resultado?
10. Implementá el patrón del diccionario para procesar 5 URLs y reportar cuál falló.
11. ¿Por qué un `Future` se puede usar como clave de un diccionario? (Pista: ¿qué necesita un objeto para ser hashable?)

### Parte D: wait

12. Corré la cuarta sección. ¿Qué devuelve `wait()`?
13. Probá con `return_when=FIRST_EXCEPTION`. ¿Cuándo vuelve?
14. Implementá "consultar tres servidores y quedarse con la primera respuesta". ¿Qué hacés con los otros dos futures?

---

## Ejercicio 3: Las excepciones

```bash
python3 errores.py
```

### 3.1 El bug silencioso

1. La primera sección no imprime ningún error. ¿Qué pasó con la excepción?
2. ¿Por qué no sube por la pila como una excepción normal?
3. Compará con asyncio: si una Task falla y nadie la espera, ¿avisa algo? Probalo.
4. Imaginá un servidor que procesa pagos en segundo plano con este bug. Describí el síntoma que vería el equipo.

### 3.2 Dónde queda

5. ¿Qué diferencia hay entre `f.exception()` y `f.result()` cuando la tarea falló?
6. ¿`exception()` bloquea? Probalo pidiéndolo antes de que termine.
7. ¿Qué devuelve `exception()` si la tarea salió bien?

### 3.3 Las defensas

8. Implementá la defensa A (consumir resultados) para procesar 10 divisiones donde algunas tengan divisor cero. Reportá cuáles fallaron.
9. Implementá la defensa B (callback). ¿Cuándo se ejecuta el callback: en el thread del worker o en el principal? Averigualo imprimiendo `threading.current_thread().name`.
10. Escribí la defensa C: una función envoltorio que capture adentro y devuelva `('ok', valor)` o `('error', mensaje)`. ¿Qué ventaja tiene sobre las otras dos?

### 3.4 map corta

11. En la quinta sección, ¿cuántos resultados se vieron de cuántos?
12. Los dos últimos estaban calculados. ¿Por qué se perdieron?
13. Reescribí ese caso con `as_completed` para no perder ninguno.

---

## Ejercicio 4: Threads o procesos

### 4.1 La misma interfaz

1. Tomá cualquier ejemplo de la clase y cambiá `ThreadPoolExecutor` por `ProcessPoolExecutor`. ¿Cuántas líneas tuviste que tocar?
2. ¿Funcionó sin más? Si no, ¿qué falló?

### 4.2 El GIL, otra vez

3. Escribí un benchmark: 4 tareas de cálculo pesado, con los dos executors. Anotá los tiempos.
4. Repetí con 4 tareas de `time.sleep(1)`. ¿Ahora cuál gana?
5. Explicá los dos resultados con lo de la clase 10.

### 4.3 El costo del pickle

6. Medí cuánto tarda `submit(suma, lista_de_2M_enteros)` contra `submit(doble, 5)` en un `ProcessPoolExecutor`.
7. ¿Qué proporción hay entre los dos?
8. Tenés que procesar un archivo de 500 MB en 4 procesos. ¿Qué le mandás a cada worker?
9. Probá pasarle una `lambda` a un `ProcessPoolExecutor`. ¿Qué error da?
10. ¿Por qué con `ThreadPoolExecutor` la lambda sí funciona?

### 4.4 El costo de crear el pool

11. Medí cuánto tarda crear un pool de 4 procesos contra uno de 4 threads.
12. Un servidor que crea un pool por pedido, ¿cuánta latencia agrega?
13. ¿Dónde debería crearse el pool en una aplicación FastAPI? (Clase 19.)

---

## Ejercicio 5: El puente con asyncio

1. Repasá `run_in_executor` de la clase 21. ¿Qué relación tiene con lo de hoy?
2. Escribí una corrutina que delegue un cálculo pesado a un `ProcessPoolExecutor` y mientras tanto siga atendiendo otra tarea.
3. ¿Por qué `await loop.run_in_executor(...)` no bloquea el event loop, si la función que ejecuta sí es bloqueante?
4. ¿Qué devuelve `run_in_executor`: un `Future` de `concurrent.futures` o uno de asyncio? Verificalo con `type()`.

---

## Verificación del ejercicio obligatorio

### Ejercicio 2: map contra as_completed

- [ ] Los tiempos de las dos formas, con números propios
- [ ] Explicaste por qué el total es igual pero la entrega distinta
- [ ] Enunciaste qué garantiza `map` que `as_completed` no
- [ ] Elegiste y justificaste para los cuatro casos de la parte B
- [ ] Implementaste el patrón del diccionario
- [ ] Explicaste por qué un Future puede ser clave de un dict
- [ ] Probaste `wait` con `FIRST_COMPLETED` y `FIRST_EXCEPTION`

---

## Ejercicios adicionales

### Barra de progreso

Procesá 50 tareas de duración aleatoria mostrando el porcentaje completado en vivo. ¿Con cuál de los dos patrones se puede hacer?

### Reintentos

Una función que reintente hasta 3 veces las tareas que fallaron, con backoff. ¿Conviene reintentar dentro del worker o volver a hacer `submit()`?

### Pool con límite de tiempo global

Procesá una lista de tareas con un presupuesto total de 5 segundos: lo que no haya terminado, se descarta. Pista: `wait(futuros, timeout=5)`.

### Comparar con lo escrito a mano

Buscá el pool de threads que escribieron en el ejercicio obligatorio de la clase 10 (con `threading` y `queue.Queue`). Reescribilo con `ThreadPoolExecutor` y compará la cantidad de líneas.

---

*Computación II - 2026 - Clase 22*
