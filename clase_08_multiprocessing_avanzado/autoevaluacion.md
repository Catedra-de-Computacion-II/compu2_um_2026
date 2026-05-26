# Clase 8: Multiprocessing Avanzado - Autoevaluación

Respondé estas preguntas para verificar tu comprensión. Las respuestas están al final.

---

## Preguntas (20)

### 1. ¿Por qué `Pool` es preferible a crear procesos manualmente cuando se ejecutan muchas tareas?

a) Es más fácil de programar
b) Reutiliza los procesos workers en lugar de crear y destruir uno por tarea
c) Funciona mejor en Windows
d) Permite usar lambdas

### 2. ¿Qué hace `Pool.map(func, iterable)`?

a) Aplica `func` a cada elemento del iterable y devuelve los resultados como lista cuando todos terminan
b) Devuelve un iterador lazy con los resultados
c) Ejecuta `func` una sola vez
d) No espera ningún resultado

### 3. ¿Cuál es la diferencia entre `map` e `imap`?

a) No hay diferencia
b) `imap` es un iterador lazy; `map` devuelve la lista completa
c) `map` es para múltiples argumentos
d) `imap` es para procesos remotos

### 4. ¿Qué hace `imap_unordered` distinto a `imap`?

a) Es para argumentos sin nombre
b) Devuelve los resultados en el orden en que terminan, no en el orden de entrada
c) No funciona con Pool
d) Es síncrono

### 5. ¿Para qué sirve `Pool.starmap`?

a) Para ejecutar tareas en estrella
b) Para funciones que reciben múltiples argumentos (desempaqueta cada tupla del iterable)
c) Es un sinónimo de `map`
d) Para tareas prioritarias

### 6. ¿Qué devuelve `Pool.apply_async`?

a) El resultado directamente
b) Un objeto `AsyncResult` que representa el valor futuro
c) Nada
d) Una excepción

### 7. ¿Qué método de `AsyncResult` verifica si la tarea terminó sin bloquear?

a) `done()`
b) `ready()`
c) `finished()`
d) `complete()`

### 8. ¿Cuántos workers usa `Pool()` sin argumentos?

a) Siempre 1
b) `os.cpu_count()` (cantidad de cores disponibles)
c) Siempre 4
d) Es obligatorio especificar

### 9. ¿Para qué sirve `Value('i', 0)` de multiprocessing?

a) Crea un entero compartido entre procesos en memoria compartida
b) Crea una variable local
c) Es para queues
d) Convierte int a string

### 10. ¿Qué tipo de datos comparte `Array`?

a) Solo strings
b) Tipos primitivos de C (int, double, char...) en memoria contigua compartida
c) Objetos Python arbitrarios
d) Solo booleanos

### 11. ¿En qué se diferencia `Manager` de `Value` y `Array`?

a) `Manager` es más rápido
b) `Manager` corre un proceso separado y permite compartir objetos Python complejos (dict, list); es más lento pero más flexible
c) Son idénticos
d) `Manager` solo funciona en Windows

### 12. ¿Por qué el siguiente código falla?

```python
with Pool(4) as pool:
    pool.map(lambda x: x * 2, range(10))
```

a) `lambda` no se puede serializar con pickle
b) `Pool` no acepta lambdas en macOS
c) `map` no existe en Pool
d) Falta `if __name__ == "__main__":`

### 13. ¿Qué protocolo usa multiprocessing para pasar objetos entre procesos?

a) JSON
b) XML
c) pickle
d) Protocol Buffers

### 14. ¿Para qué tipo de tareas conviene multiprocessing?

a) Esperar respuestas de red (I/O-bound)
b) Cálculos pesados (CPU-bound)
c) Tareas instantáneas (< 1ms)
d) Servir muchas conexiones cortas

### 15. ¿Qué hace `from functools import reduce`?

a) Importa una función que aplica acumulativamente una función de dos argumentos a una secuencia, reduciéndola a un valor
b) Reduce el tamaño de un archivo
c) Optimiza el código
d) Comprime datos

### 16. En Map-Reduce, ¿qué etapa se paraleliza típicamente?

a) Solo reduce
b) Solo map
c) Map se paraleliza, reduce se hace secuencial combinando los resultados
d) Ninguna

### 17. ¿Qué es un Pipeline de procesos?

a) Una sola tarea ejecutada N veces
b) Una cadena de etapas conectadas por colas, donde cada etapa transforma los datos
c) Un atajo de Pool
d) Una variante de Queue

### 18. ¿Cuándo conviene `imap_unordered` sobre `imap`?

a) Cuando no te importa el orden y querés máxima velocidad
b) Cuando necesitás el orden estricto
c) Cuando hay un solo elemento
d) Siempre que uses Pool

### 19. ¿Por qué `Value` provee `get_lock()` automáticamente?

a) Para que puedas evitar race conditions al modificar el valor desde varios procesos
b) Para hacer el código más lento
c) Para serializar mejor
d) Es obligatorio usarlo siempre

### 20. ¿Cuándo NO conviene usar multiprocessing?

a) Cuando las tareas son muy chicas (< 10ms) y el overhead de serialización supera la ganancia
b) Nunca, siempre conviene
c) Solo en Windows
d) Solo en Linux

---

## Respuestas

<details>
<summary>Click para ver respuestas</summary>

1. **b** - Reutiliza los workers en lugar de crear/destruir
2. **a** - Aplica func y devuelve lista al final, bloqueando hasta terminar
3. **b** - `imap` es lazy, `map` devuelve lista completa
4. **b** - Devuelve en orden de finalización, no de entrada
5. **b** - Desempaqueta tuplas como argumentos posicionales
6. **b** - Un `AsyncResult` (future)
7. **b** - `ready()`
8. **b** - `os.cpu_count()`
9. **a** - Entero compartido en memoria compartida
10. **b** - Tipos primitivos de C en memoria contigua
11. **b** - Manager usa proceso separado, más lento pero soporta objetos complejos
12. **a** - Lambdas no son picklables
13. **c** - pickle
14. **b** - CPU-bound
15. **a** - Aplica función acumulativa para reducir secuencia a un valor
16. **c** - Map se paraleliza, reduce combina secuencialmente
17. **b** - Cadena de etapas conectadas por colas
18. **a** - Cuando no importa el orden y querés máxima velocidad
19. **a** - Para evitar race conditions
20. **a** - Cuando las tareas son chicas y el overhead supera la ganancia

### Puntuación

- 18-20: Excelente dominio del tema. Avanzá a los ejercicios adicionales
- 14-17: Buen nivel. Repasá los temas donde fallaste
- 10-13: Releé el contenido, los conceptos clave todavía no están firmes
- < 10: Repasá la clase completa y consultá dudas con el docente

</details>

---

*Computación II - 2026 - Clase 8*
