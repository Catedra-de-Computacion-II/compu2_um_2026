# Clase 9: Multiprocessing Avanzado - Autoevaluación

Respondé estas preguntas para verificar tu comprensión. Las respuestas están al final.

---

## Preguntas (20)

### 1. ¿Por qué `Pool` es preferible a crear procesos manualmente cuando se ejecutan muchas tareas?

a) Reutiliza los procesos workers en lugar de crear y destruir uno por tarea
b) Funciona mejor en Windows
c) Es más fácil de programar
d) Permite usar lambdas

### 2. ¿Qué hace `Pool.map(func, iterable)`?

a) No espera ningún resultado
b) Ejecuta `func` una sola vez
c) Devuelve un iterador lazy con los resultados
d) Aplica `func` a cada elemento del iterable y devuelve los resultados como lista cuando todos terminan

### 3. ¿Cuál es la diferencia entre `map` e `imap`?

a) No hay diferencia
b) `imap` es para procesos remotos
c) `map` es para múltiples argumentos
d) `imap` es un iterador lazy; `map` devuelve la lista completa

### 4. ¿Qué hace `imap_unordered` distinto a `imap`?

a) Es síncrono
b) No funciona con Pool
c) Devuelve los resultados en el orden en que terminan, no en el orden de entrada
d) Es para argumentos sin nombre

### 5. ¿Para qué sirve `Pool.starmap`?

a) Para funciones que reciben múltiples argumentos (desempaqueta cada tupla del iterable)
b) Para tareas prioritarias
c) Para ejecutar tareas en estrella
d) Es un sinónimo de `map`

### 6. ¿Qué devuelve `Pool.apply_async`?

a) Un objeto `AsyncResult` que representa el valor futuro
b) Nada
c) El resultado directamente
d) Una excepción

### 7. ¿Qué método de `AsyncResult` verifica si la tarea terminó sin bloquear?

a) `finished()`
b) `done()`
c) `ready()`
d) `complete()`

### 8. ¿Cuántos workers usa `Pool()` sin argumentos?

a) Siempre 4
b) Siempre 1
c) Es obligatorio especificar
d) `os.cpu_count()` (cantidad de cores disponibles)

### 9. ¿Para qué sirve `Value('i', 0)` de multiprocessing?

a) Convierte int a string
b) Crea una variable local
c) Es para queues
d) Crea un entero compartido entre procesos en memoria compartida

### 10. ¿Qué tipo de datos comparte `Array`?

a) Objetos Python arbitrarios
b) Solo booleanos
c) Tipos primitivos de C (int, double, char...) en memoria contigua compartida
d) Solo strings

### 11. ¿En qué se diferencia `Manager` de `Value` y `Array`?

a) `Manager` corre un proceso separado y permite compartir objetos Python complejos (dict, list); es más lento pero más flexible
b) `Manager` es más rápido
c) Son idénticos
d) `Manager` solo funciona en Windows

### 12. ¿Por qué el siguiente código falla?

```python
with Pool(4) as pool:
    pool.map(lambda x: x * 2, range(10))
```

a) Falta `if __name__ == "__main__":`
b) `map` no existe en Pool
c) `Pool` no acepta lambdas en macOS
d) `lambda` no se puede serializar con pickle

### 13. ¿Qué protocolo usa multiprocessing para pasar objetos entre procesos?

a) pickle
b) JSON
c) Protocol Buffers
d) XML

### 14. ¿Para qué tipo de tareas conviene multiprocessing?

a) Tareas instantáneas (< 1ms)
b) Esperar respuestas de red (I/O-bound)
c) Servir muchas conexiones cortas
d) Cálculos pesados (CPU-bound)

### 15. ¿Qué hace `from functools import reduce`?

a) Reduce el tamaño de un archivo
b) Optimiza el código
c) Comprime datos
d) Importa una función que aplica acumulativamente una función de dos argumentos a una secuencia, reduciéndola a un valor

### 16. En Map-Reduce, ¿qué etapa se paraleliza típicamente?

a) Map se paraleliza, reduce se hace secuencial combinando los resultados
b) Solo reduce
c) Solo map
d) Ninguna

### 17. ¿Qué es un Pipeline de procesos?

a) Una sola tarea ejecutada N veces
b) Una cadena de etapas conectadas por colas, donde cada etapa transforma los datos
c) Una variante de Queue
d) Un atajo de Pool

### 18. ¿Cuándo conviene `imap_unordered` sobre `imap`?

a) Cuando no te importa el orden y querés máxima velocidad
b) Siempre que uses Pool
c) Cuando necesitás el orden estricto
d) Cuando hay un solo elemento

### 19. ¿Por qué `Value` provee `get_lock()` automáticamente?

a) Para serializar mejor
b) Para que puedas evitar race conditions al modificar el valor desde varios procesos
c) Para hacer el código más lento
d) Es obligatorio usarlo siempre

### 20. ¿Cuándo NO conviene usar multiprocessing?

a) Cuando las tareas son muy chicas (< 10ms) y el overhead de serialización supera la ganancia
b) Solo en Windows
c) Solo en Linux
d) Nunca, siempre conviene

---

## Respuestas

<details>
<summary>Click para ver respuestas</summary>

1. **a** - Reutiliza los workers en lugar de crear/destruir
2. **d** - Aplica func y devuelve lista al final, bloqueando hasta terminar
3. **d** - `imap` es lazy, `map` devuelve lista completa
4. **c** - Devuelve en orden de finalización, no de entrada
5. **a** - Desempaqueta tuplas como argumentos posicionales
6. **a** - Un `AsyncResult` (future)
7. **c** - `ready()`
8. **d** - `os.cpu_count()`
9. **d** - Entero compartido en memoria compartida
10. **c** - Tipos primitivos de C en memoria contigua
11. **a** - Manager usa proceso separado, más lento pero soporta objetos complejos
12. **d** - Lambdas no son picklables
13. **a** - pickle
14. **d** - CPU-bound
15. **d** - Aplica función acumulativa para reducir secuencia a un valor
16. **a** - Map se paraleliza, reduce combina secuencialmente
17. **b** - Cadena de etapas conectadas por colas
18. **a** - Cuando no importa el orden y querés máxima velocidad
19. **b** - Para evitar race conditions
20. **a** - Cuando las tareas son chicas y el overhead supera la ganancia

### Puntuación

- 18-20: Excelente dominio del tema. Avanzá a los ejercicios adicionales
- 14-17: Buen nivel. Repasá los temas donde fallaste
- 10-13: Releé el contenido, los conceptos clave todavía no están firmes
- < 10: Repasá la clase completa y consultá dudas con el docente

</details>

---

*Computación II - 2026 - Clase 9*
