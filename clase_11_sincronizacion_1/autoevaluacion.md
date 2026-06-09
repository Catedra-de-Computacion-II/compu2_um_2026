# Clase 11: Sincronización Avanzada - Autoevaluación

Responde estas preguntas para verificar tu comprensión. Las respuestas están al final.

---

## Parte 1: Problemas de concurrencia (5 preguntas)

### Pregunta 1
¿Qué es una race condition?

a) Una competencia de velocidad entre threads
b) Cuando el resultado depende del orden de ejecución no determinístico de threads
c) Un tipo de deadlock
d) Un error de sintaxis

### Pregunta 2
¿Qué es un deadlock?

a) Un thread que no responde
b) Cuando dos o más threads esperan mutuamente recursos que el otro tiene
c) Un thread que usa demasiado CPU
d) Un error de memoria

### Pregunta 3
¿Cuál es la forma más común de prevenir deadlocks?

a) Usar más threads
b) Adquirir locks siempre en el mismo orden
c) No usar locks
d) Usar solo un thread

### Pregunta 4
¿Qué es starvation?

a) Un thread sin memoria
b) Un thread que nunca obtiene acceso al recurso que necesita
c) Un thread que termina inesperadamente
d) Un thread sin trabajo

### Pregunta 5
¿Qué es una sección crítica?

a) Código que puede fallar
b) Código que accede a recursos compartidos y debe ser protegido
c) Código que es muy importante
d) Código que tarda mucho

---

## Parte 2: Lock y RLock (4 preguntas)

### Pregunta 6
¿Qué diferencia hay entre Lock y RLock?

a) RLock es más rápido
b) RLock permite que el mismo thread adquiera el lock múltiples veces
c) Lock es para lectura, RLock para escritura
d) No hay diferencia

### Pregunta 7
¿Cuál es la forma recomendada de usar un Lock?

a) `lock.acquire()` y `lock.release()` separados
b) `with lock:`
c) `lock.lock()` y `lock.unlock()`
d) Cualquiera de las anteriores

### Pregunta 8
¿Qué pasa si un thread intenta adquirir un Lock que ya tiene (sin RLock)?

a) Lo adquiere normalmente
b) Deadlock
c) Lanza excepción
d) Lo ignora

### Pregunta 9
¿Qué hace `lock.acquire(timeout=5)`?

a) Espera indefinidamente
b) Intenta adquirir máximo 5 segundos, retorna False si no puede
c) Adquiere el lock por 5 segundos
d) Lanza excepción después de 5 segundos

---

## Parte 3: Condition (4 preguntas)

### Pregunta 10
¿Para qué se usa Condition?

a) Para verificar condiciones booleanas
b) Para que threads esperen hasta que se cumpla cierta condición
c) Para contar threads
d) Para terminar threads

### Pregunta 11
¿Qué hace `condition.wait()`?

a) Solo espera
b) Libera el lock, espera notificación, readquiere el lock
c) Notifica a otros threads
d) Termina el thread

### Pregunta 12
¿Por qué se debe usar `while` en vez de `if` antes de `condition.wait()`?

a) Es más rápido
b) La condición puede cambiar entre la notificación y el despertar
c) `if` no funciona con Condition
d) No es necesario, es solo estilo

### Pregunta 13
¿Cuál es la diferencia entre `notify()` y `notify_all()`?

a) No hay diferencia
b) `notify()` despierta un thread, `notify_all()` despierta todos
c) `notify_all()` es más lento
d) `notify()` es obsoleto

---

## Parte 4: Semaphore (4 preguntas)

### Pregunta 14
¿Qué representa el contador interno de un Semaphore?

a) El número de threads esperando
b) El número de recursos disponibles
c) El número de operaciones realizadas
d) El tiempo de espera

### Pregunta 15
¿Qué hace `Semaphore(3)`?

a) Crea un semáforo que permite máximo 3 threads simultáneos
b) Crea 3 semáforos
c) Espera 3 segundos
d) Permite 3 operaciones totales

### Pregunta 16
¿Qué diferencia hay entre Semaphore y BoundedSemaphore?

a) BoundedSemaphore es más rápido
b) BoundedSemaphore no permite más releases que acquires
c) Semaphore tiene límite, BoundedSemaphore no
d) No hay diferencia

### Pregunta 17
¿Qué pasa si hacés `release()` en un Semaphore más veces que `acquire()`?

a) Error
b) El contador aumenta más allá del valor inicial
c) Se ignora
d) Deadlock

---

## Parte 5: Event y Barrier (4 preguntas)

### Pregunta 18
¿Qué es un Event?

a) Un contador
b) Un flag thread-safe que threads pueden esperar
c) Un tipo de excepción
d) Un log de eventos

### Pregunta 19
¿Qué hace `event.wait()`?

a) Setea el evento
b) Bloquea hasta que el evento sea seteado
c) Limpia el evento
d) Verifica si hay evento

### Pregunta 20
¿Para qué sirve Barrier?

a) Para evitar deadlocks
b) Para que N threads esperen hasta que todos lleguen a un punto
c) Para limitar acceso concurrente
d) Para proteger datos

### Pregunta 21
¿Qué pasa si un thread llega a una Barrier(4) y solo hay 3 threads en total?

a) Funciona normalmente
b) El thread espera indefinidamente
c) Lanza excepción inmediatamente
d) Se crea un thread adicional

---

## Parte 6: Patrones (4 preguntas)

### Pregunta 22
En el patrón productor-consumidor, ¿qué primitivo se usa típicamente?

a) Solo Lock
b) Condition o Queue
c) Solo Event
d) Solo Semaphore

### Pregunta 23
¿Qué permite un Readers-Writers Lock?

a) Cualquier acceso simultáneo
b) Múltiples lectores O un escritor, pero no ambos
c) Solo lectura
d) Solo escritura

### Pregunta 24
¿Cuál es el propósito del double-checked locking?

a) Doble seguridad
b) Evitar adquirir lock innecesariamente en casos comunes
c) Prevenir deadlocks
d) Mejorar la lectura

### Pregunta 25
¿Qué ventaja tiene `queue.Queue` sobre una lista con Lock?

a) Es más rápida
b) Es thread-safe por diseño con operaciones bloqueantes
c) Usa menos memoria
d) No tiene ventajas

---

## Respuestas

<details>
<summary>Click para ver respuestas</summary>

### Parte 1: Problemas de concurrencia
1. **b** - Cuando el resultado depende del orden de ejecución no determinístico
2. **b** - Cuando dos o más threads esperan mutuamente recursos que el otro tiene
3. **b** - Adquirir locks siempre en el mismo orden
4. **b** - Un thread que nunca obtiene acceso al recurso que necesita
5. **b** - Código que accede a recursos compartidos y debe ser protegido

### Parte 2: Lock y RLock
6. **b** - RLock permite que el mismo thread adquiera el lock múltiples veces
7. **b** - `with lock:`
8. **b** - Deadlock
9. **b** - Intenta adquirir máximo 5 segundos, retorna False si no puede

### Parte 3: Condition
10. **b** - Para que threads esperen hasta que se cumpla cierta condición
11. **b** - Libera el lock, espera notificación, readquiere el lock
12. **b** - La condición puede cambiar entre la notificación y el despertar
13. **b** - `notify()` despierta un thread, `notify_all()` despierta todos

### Parte 4: Semaphore
14. **b** - El número de recursos disponibles
15. **a** - Crea un semáforo que permite máximo 3 threads simultáneos
16. **b** - BoundedSemaphore no permite más releases que acquires
17. **b** - El contador aumenta más allá del valor inicial

### Parte 5: Event y Barrier
18. **b** - Un flag thread-safe que threads pueden esperar
19. **b** - Bloquea hasta que el evento sea seteado
20. **b** - Para que N threads esperen hasta que todos lleguen a un punto
21. **b** - El thread espera indefinidamente

### Parte 6: Patrones
22. **b** - Condition o Queue
23. **b** - Múltiples lectores O un escritor, pero no ambos
24. **b** - Evitar adquirir lock innecesariamente en casos comunes
25. **b** - Es thread-safe por diseño con operaciones bloqueantes

### Puntuación
- 23-25: Excelente dominio de sincronización
- 18-22: Buen nivel
- 13-17: Necesitas repasar algunos conceptos
- <13: Revisa el material nuevamente

</details>

---

*Computación II - 2026 - Clase 11*
