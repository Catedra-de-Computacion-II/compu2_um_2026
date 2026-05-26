# Clase 8: Multiprocessing - Autoevaluación

Responde estas preguntas para verificar tu comprensión. Las respuestas están al final.

---

## Preguntas (20)

### 1. ¿Cuál es la principal ventaja de multiprocessing sobre threading en Python?
a) Es más fácil de usar
b) Supera el GIL permitiendo verdadero paralelismo
c) Usa menos memoria
d) Es más rápido siempre

### 2. ¿Los procesos creados con multiprocessing comparten memoria por defecto?
a) Sí
b) No
c) Solo variables globales
d) Solo con Manager

### 3. ¿Por qué es necesario `if __name__ == "__main__":` en multiprocessing?
a) Es opcional
b) Para evitar que el código se ejecute al importar (necesario en Windows)
c) Solo por estilo
d) Para mejorar rendimiento

### 4. ¿Qué clase se usa para crear pools de procesos?
a) ProcessPool
b) Pool
c) Workers
d) ProcessExecutor

### 5. ¿Qué método de Pool aplica una función a cada elemento de un iterable?
a) apply()
b) execute()
c) map()
d) run()

### 6. ¿Cuál es la diferencia entre `map` e `imap` en Pool?
a) No hay diferencia
b) imap es un iterador lazy, map retorna lista completa
c) map es más rápido
d) imap es para múltiples argumentos

### 7. ¿Qué clase permite compartir un valor simple entre procesos?
a) SharedValue
b) Value
c) Shared
d) GlobalValue

### 8. ¿Para qué se usa multiprocessing.Queue?
a) Para ordenar procesos
b) Para comunicación entre procesos
c) Para sincronización
d) Para logging

### 9. ¿Qué retorna Pipe()?
a) Un solo extremo
b) Dos conexiones (extremos del pipe)
c) Un Queue
d) Un file descriptor

### 10. ¿Qué es Manager en multiprocessing?
a) Un supervisor de procesos
b) Un servidor que permite compartir objetos complejos entre procesos
c) Un pool manager
d) Un garbage collector

### 11. ¿Qué método espera a que un proceso termine?
a) wait()
b) join()
c) sync()
d) finish()

### 12. ¿Qué protocolo usa multiprocessing para serializar objetos?
a) JSON
b) XML
c) pickle
d) marshal

### 13. ¿Pueden las lambdas pasarse a Pool.map()?
a) Sí
b) No, no son serializables con pickle
c) Solo en Linux
d) Solo con cloudpickle

### 14. ¿Cuál es el overhead principal de multiprocessing vs threading?
a) Más memoria
b) Creación de procesos es más costosa
c) No hay overhead
d) Sincronización

### 15. ¿Para qué tipo de tareas es mejor multiprocessing?
a) I/O-bound
b) CPU-bound
c) Tareas simples
d) Networking

### 16. ¿Qué hace Pool.starmap()?
a) Mapea con múltiples argumentos (desempaqueta tuplas)
b) Ejecuta en estrella
c) Prioriza tareas
d) Map asíncrono

### 17. ¿Cómo se protege un Value compartido de race conditions?
a) Es thread-safe automáticamente
b) Usando get_lock() o Lock explícito
c) No es necesario
d) Con Semaphore

### 18. ¿Qué método de AsyncResult verifica si terminó?
a) done()
b) ready()
c) finished()
d) complete()

### 19. ¿Cuál es equivalente a ThreadPoolExecutor para procesos?
a) ProcessPool
b) ProcessPoolExecutor
c) MultiprocessingExecutor
d) ParallelExecutor

### 20. ¿Qué pasa si un proceso hijo falla?
a) El padre falla también
b) El padre puede detectarlo con exitcode
c) Se reinicia automáticamente
d) Se ignora

---

## Respuestas

<details>
<summary>Click para ver respuestas</summary>

1. **b** - Supera el GIL permitiendo verdadero paralelismo
2. **b** - No (tienen memoria separada)
3. **b** - Para evitar que el código se ejecute al importar
4. **b** - Pool
5. **c** - map()
6. **b** - imap es un iterador lazy, map retorna lista completa
7. **b** - Value
8. **b** - Para comunicación entre procesos
9. **b** - Dos conexiones (extremos del pipe)
10. **b** - Un servidor que permite compartir objetos complejos
11. **b** - join()
12. **c** - pickle
13. **b** - No, no son serializables con pickle
14. **b** - Creación de procesos es más costosa
15. **b** - CPU-bound
16. **a** - Mapea con múltiples argumentos
17. **b** - Usando get_lock() o Lock explícito
18. **b** - ready()
19. **b** - ProcessPoolExecutor
20. **b** - El padre puede detectarlo con exitcode

### Puntuación
- 18-20: Excelente
- 14-17: Buen nivel
- 10-13: Necesita repaso
- <10: Revisar material

</details>

---

*Computación II - 2026 - Clase 8*
