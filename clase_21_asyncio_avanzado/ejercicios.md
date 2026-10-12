# Clase 21: Asyncio avanzado - Ejercicios Prácticos

Los archivos `cola.py`, `grupos.py` y `executor.py` acompañan la clase.

Estos ejercicios son, en buena medida, el TP2 hecho de a pedazos. Lo que armes acá te sirve directo.

---

## Ejercicio 1: La cola

```bash
python3 cola.py
python3 cola.py --centinela
python3 cola.py --presion
```

### 1.1 El reparto

1. Con 12 tareas de 0.05 s y 3 workers, ¿cuánto tarda? ¿Cuánto habría tardado secuencial?
2. ¿Cómo quedó repartido el trabajo entre los workers? ¿Es siempre parejo?
3. Subí a 6 workers. ¿Se reduce a la mitad? ¿Por qué no exactamente?

### 1.2 task_done

4. Sacá el `cola.task_done()` del worker y corré de nuevo. ¿Qué pasa?
5. Explicá el mecanismo: ¿qué cuenta la cola internamente y qué espera `join()`?
6. ¿Por qué `task_done()` va en un `finally` y no después de `procesar()`?

### 1.3 Backpressure

7. Corré `cola.py --presion`. ¿Cuánto tarda el productor con `maxsize=2` y con `maxsize=100`?
8. ¿Dónde está esperando el productor en el primer caso?
9. Tu API recibe 10.000 pedidos de golpe y la cola es infinita. ¿Qué pasa con la memoria?
10. ¿Qué código de estado HTTP conviene devolver cuando la cola está llena? (Clase 19.)

### 1.4 Apagado

11. Compará el modo normal con `--centinela`. ¿Qué diferencia hay en cómo terminan los workers?
12. Si cancelás un worker justo cuando está procesando, ¿qué pasa con esa tarea?
13. ¿Por qué hay que poner **un centinela por worker** y no uno solo?

### 1.5 Prioridades

14. Cambiá `asyncio.Queue` por `asyncio.PriorityQueue` y encolá tuplas `(prioridad, tarea)`.
15. Probá encolar dos tareas con la misma prioridad. ¿Qué error da? ¿Cómo se arregla?
16. ¿Qué problema de la clase 11 puede aparecer con una cola de prioridad?

---

## Ejercicio 2: Grupos de tareas

```bash
python3 grupos.py
```

1. En la parte de `gather`, ¿qué pasa con la tarea A cuando falla la otra?
2. En la de `TaskGroup`, ¿qué pasa con B? ¿Quién la canceló?
3. ¿Por qué eso importa en un servidor que corre semanas?

### 2.1 ExceptionGroup

4. En la última parte entran **las dos** ramas del `except*`. ¿Por qué no es como un `except` común?
5. Escribí un `TaskGroup` donde fallen tres tareas con el mismo tipo de excepción. ¿Cuántas llegan al `eg.exceptions`?
6. ¿Se puede usar `except` común para capturar un `ExceptionGroup`? Probalo.

### 2.2 Cuál usar

7. Para cada caso, decidí entre `gather` y `TaskGroup`, y justificá:
   - Descargar 10 URLs; si una falla querés las otras 9 igual
   - Abrir una conexión a la base y arrancar el worker que la usa
   - Lanzar 4 workers que viven mientras el servidor esté arriba
   - Procesar un lote donde si uno falla el lote entero es inválido

8. `TaskGroup` no devuelve resultados. ¿Cómo se obtienen?

---

## Ejercicio 3: Sacar el trabajo del loop (obligatorio)

### Objetivo

Reproducir la medición 2 del TP2 y entender por qué threads y procesos no son intercambiables.

### Parte A: el loop bloqueado

```bash
python3 executor.py
```

1. Copiá los tres tiempos y los tres "peor atraso".
2. ¿Cuánto se atrasa el loop sin executor? ¿Qué significa ese número para un servidor?
3. Con executor, el trabajo tarda **lo mismo**. Entonces, ¿qué mejoró exactamente?
4. Mirá cómo está hecho el medidor en el código. ¿Por qué mide el atraso de un `sleep` y no otra cosa?

### Parte B: threads contra procesos

```bash
python3 executor.py --paralelo
```

5. Con 4 tareas CPU-bound, ¿cuánto tarda con threads y cuánto con procesos?
6. ¿Por qué la diferencia? Relacionalo con la clase 10.
7. Con **una sola** tarea los dos empatan. ¿Por qué el GIL no se nota ahí?
8. Cambiá el trabajo por algo I/O-bound (`time.sleep`) y repetí. ¿Siguen diferenciándose?

### Parte C: el costo de los procesos

9. Pasale al executor una función `lambda`. ¿Qué error da? ¿Por qué?
10. Pasale un argumento grande (una lista de un millón de números) y medí. Compará con pasar solo un número.
11. ¿Por qué conviene crear el `ProcessPoolExecutor` una vez y no por tarea?

### Parte D: en una API

12. Tomá `api.py` de la clase 19 y agregale un endpoint `POST /hashear` que haga el cálculo pesado **sin** executor.
13. Mientras procesa, pedí `GET /tareas` desde otra terminal. ¿Cuánto tarda en responder?
14. Ahora con `run_in_executor`, creando el pool en el `lifespan`. Repetí la medición.
15. Esa diferencia es la medición 2 del TP2: anotá los dos números.

---

## Ejercicio 4: Sincronización async

### 4.1 Cuándo hace falta

1. Repasá la regla de la clase 20. ¿Cuándo necesitás un `asyncio.Lock`?
2. Este código, ¿necesita lock? Justificá.

```python
async def incrementar():
    global contador
    contador += 1
```

3. ¿Y este?

```python
async def transferir(a, b, monto):
    saldo = cuentas[a]
    await log(monto)
    cuentas[a] = saldo - monto
```

4. Implementá el segundo con `asyncio.Lock` y verificá que el saldo final sea correcto con 100 transferencias concurrentes.

### 4.2 Semáforo contra cola

5. ¿Cuál es la diferencia entre limitar con `Semaphore(5)` y usar una `Queue` con 5 workers?
6. ¿En qué caso conviene cada uno?
7. Implementá las dos versiones para descargar 20 URLs con concurrencia máxima 5. ¿Cuál quedó más clara?

### 4.3 Event

8. Usá un `asyncio.Event` para que varios workers esperen a que termine una inicialización antes de empezar.
9. ¿Qué pasa si llamás `set()` antes de que alguien haga `wait()`?
10. ¿Cómo se "desetea"? ¿Cuándo sirve `clear()`?

---

## Ejercicio 5: El esqueleto del TP2

Juntá todo en una API que funcione de verdad.

1. Partí de `api.py` de la clase 19.
2. Agregá en el `lifespan`: una `asyncio.Queue` con `maxsize`, un `ProcessPoolExecutor`, y N workers.
3. `POST /tareas` encola y responde **inmediatamente** con el id y estado `pendiente`.
4. Los workers consumen, cambian el estado a `ejecutando`, procesan y marcan `completada`.
5. `GET /tareas/{id}` devuelve el estado actual.
6. Las tareas de tipo `hashear` van al executor; las de tipo `esperar`, directo al loop.
7. `DELETE /tareas/{id}` cancela una tarea en ejecución.
8. En el apagado, los workers terminan lo que están haciendo (centinela) y el pool se cierra.

Con eso tenés el núcleo del TP2 funcionando. Lo que falta es el manejo de errores, las estadísticas y las mediciones.

---

## Verificación del ejercicio obligatorio

### Ejercicio 3: Sacar el trabajo del loop

- [ ] Los tres tiempos y los tres atrasos, con números propios
- [ ] Explicaste qué significa el atraso para un servidor
- [ ] Explicaste qué mejora el executor si el trabajo tarda lo mismo
- [ ] Mediste threads contra procesos con 4 tareas CPU-bound
- [ ] Explicaste la diferencia con el GIL
- [ ] Probaste qué pasa con una tarea sola y explicaste por qué empatan
- [ ] Probaste el error de pasar una lambda al executor
- [ ] Hiciste la medición en una API real (parte D)

---

## Ejercicios adicionales

### Workers con reintentos

Si una tarea falla, volver a encolarla hasta 3 veces con backoff exponencial. ¿Dónde guardás el contador de intentos?

### Estadísticas en vivo

Un endpoint `GET /estadisticas` que devuelva: tareas por estado, tamaño actual de la cola, cuántos workers están ocupados, y el tiempo promedio de procesamiento.

### Cola con prioridad real

Que `POST /tareas` acepte un campo `prioridad` y las tareas se procesen en ese orden. Resolvé el problema de la inanición: garantizá que una tarea de baja prioridad no espere indefinidamente.

### Medir el loop en vivo

Agregá a tu API una tarea de fondo que mida el atraso del event loop (como el medidor de `executor.py`) y lo exponga en `/estadisticas`. Es la instrumentación que usan los servidores en producción.

---

*Computación II - 2026 - Clase 21*
