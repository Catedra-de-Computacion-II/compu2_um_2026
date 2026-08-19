# Clase 11: Sincronización - Autoevaluación

Responde estas preguntas para verificar tu comprensión. Las respuestas están al final.

---

## Parte 1: Problemas de concurrencia (5 preguntas)

### Pregunta 1
¿Qué es una race condition?

a) Un tipo de deadlock
b) Cuando el resultado depende del orden de ejecución no determinístico de threads
c) Una competencia de velocidad entre threads
d) Un error de sintaxis

### Pregunta 2
¿Qué es un deadlock?

a) Un thread que no responde
b) Cuando dos o más threads esperan mutuamente recursos que el otro tiene
c) Un thread que usa demasiado CPU
d) Un error de memoria

### Pregunta 3
¿Cuál es la forma más común de prevenir deadlocks?

a) Usar solo un thread
b) Usar más threads
c) No usar locks
d) Adquirir locks siempre en el mismo orden

### Pregunta 4
¿Qué es starvation?

a) Un thread que nunca obtiene acceso al recurso que necesita
b) Un thread sin memoria
c) Un thread que termina inesperadamente
d) Un thread sin trabajo

### Pregunta 5
¿Qué es una sección crítica?

a) Código que puede fallar
b) Código que tarda mucho
c) Código que accede a recursos compartidos y debe ser protegido
d) Código que es muy importante

---

## Parte 2: Lock y RLock (4 preguntas)

### Pregunta 6
¿Qué diferencia hay entre Lock y RLock?

a) RLock es más rápido
b) RLock permite que el mismo thread adquiera el lock múltiples veces
c) No hay diferencia
d) Lock es para lectura, RLock para escritura

### Pregunta 7
¿Cuál es la forma recomendada de usar un Lock?

a) `lock.acquire()` y `lock.release()` separados
b) `with lock:`
c) Cualquiera de las anteriores
d) `lock.lock()` y `lock.unlock()`

### Pregunta 8
¿Qué pasa si un thread intenta adquirir un Lock que ya tiene (sin RLock)?

a) Deadlock
b) Lo adquiere normalmente
c) Lo ignora
d) Lanza excepción

### Pregunta 9
¿Qué hace `lock.acquire(timeout=5)`?

a) Adquiere el lock por 5 segundos
b) Espera indefinidamente
c) Lanza excepción después de 5 segundos
d) Intenta adquirir máximo 5 segundos, retorna False si no puede

---

## Parte 3: Condition (4 preguntas)

### Pregunta 10
¿Para qué se usa Condition?

a) Para que threads esperen hasta que se cumpla cierta condición
b) Para terminar threads
c) Para verificar condiciones booleanas
d) Para contar threads

### Pregunta 11
¿Qué hace `condition.wait()`?

a) Notifica a otros threads
b) Libera el lock, espera notificación, readquiere el lock
c) Termina el thread
d) Solo espera

### Pregunta 12
¿Por qué se debe usar `while` en vez de `if` antes de `condition.wait()`?

a) La condición puede cambiar entre la notificación y el despertar
b) Es más rápido
c) `if` no funciona con Condition
d) No es necesario, es solo estilo

### Pregunta 13
¿Cuál es la diferencia entre `notify()` y `notify_all()`?

a) `notify()` es obsoleto
b) No hay diferencia
c) `notify_all()` es más lento
d) `notify()` despierta un thread, `notify_all()` despierta todos

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

a) Permite 3 operaciones totales
b) Crea un semáforo que permite máximo 3 threads simultáneos
c) Crea 3 semáforos
d) Espera 3 segundos

### Pregunta 16
¿Qué diferencia hay entre Semaphore y BoundedSemaphore?

a) BoundedSemaphore no permite más releases que acquires
b) Semaphore tiene límite, BoundedSemaphore no
c) No hay diferencia
d) BoundedSemaphore es más rápido

### Pregunta 17
¿Qué pasa si hacés `release()` en un Semaphore más veces que `acquire()`?

a) Se ignora
b) Deadlock
c) El contador aumenta más allá del valor inicial
d) Error

---

## Parte 5: Event y Barrier (4 preguntas)

### Pregunta 18
¿Qué es un Event?

a) Un contador
b) Un tipo de excepción
c) Un log de eventos
d) Un flag thread-safe que threads pueden esperar

### Pregunta 19
¿Qué hace `event.wait()`?

a) Verifica si hay evento
b) Bloquea hasta que el evento sea seteado
c) Setea el evento
d) Limpia el evento

### Pregunta 20
¿Para qué sirve Barrier?

a) Para limitar acceso concurrente
b) Para evitar deadlocks
c) Para proteger datos
d) Para que N threads esperen hasta que todos lleguen a un punto

### Pregunta 21
¿Qué pasa si un thread llega a una Barrier(4) y solo hay 3 threads en total?

a) Lanza excepción inmediatamente
b) Se crea un thread adicional
c) El thread espera indefinidamente
d) Funciona normalmente

---

## Parte 6: Patrones (4 preguntas)

### Pregunta 22
En el patrón productor-consumidor, ¿qué primitivo se usa típicamente?

a) Condition o Queue
b) Solo Lock
c) Solo Semaphore
d) Solo Event

### Pregunta 23
¿Qué permite un Readers-Writers Lock?

a) Solo escritura
b) Solo lectura
c) Múltiples lectores O un escritor, pero no ambos
d) Cualquier acceso simultáneo

### Pregunta 24
¿Cuál es el propósito del double-checked locking?

a) Evitar adquirir lock innecesariamente en casos comunes
b) Prevenir deadlocks
c) Mejorar la lectura
d) Doble seguridad

### Pregunta 25
¿Qué ventaja tiene `queue.Queue` sobre una lista con Lock?

a) Es thread-safe por diseño con operaciones bloqueantes
b) Usa menos memoria
c) Es más rápida
d) No tiene ventajas

---

## Respuestas

<details>
<summary>Click para ver respuestas</summary>

### Parte 1: Problemas de concurrencia
1. **b** - Cuando el resultado depende del orden de ejecución no determinístico
2. **b** - Cuando dos o más threads esperan mutuamente recursos que el otro tiene
3. **d** - Adquirir locks siempre en el mismo orden
4. **a** - Un thread que nunca obtiene acceso al recurso que necesita
5. **c** - Código que accede a recursos compartidos y debe ser protegido

### Parte 2: Lock y RLock
6. **b** - RLock permite que el mismo thread adquiera el lock múltiples veces
7. **b** - `with lock:`
8. **a** - Deadlock
9. **d** - Intenta adquirir máximo 5 segundos, retorna False si no puede

### Parte 3: Condition
10. **a** - Para que threads esperen hasta que se cumpla cierta condición
11. **b** - Libera el lock, espera notificación, readquiere el lock
12. **a** - La condición puede cambiar entre la notificación y el despertar
13. **d** - `notify()` despierta un thread, `notify_all()` despierta todos

### Parte 4: Semaphore
14. **b** - El número de recursos disponibles
15. **b** - Crea un semáforo que permite máximo 3 threads simultáneos
16. **a** - BoundedSemaphore no permite más releases que acquires
17. **c** - El contador aumenta más allá del valor inicial

### Parte 5: Event y Barrier
18. **d** - Un flag thread-safe que threads pueden esperar
19. **b** - Bloquea hasta que el evento sea seteado
20. **d** - Para que N threads esperen hasta que todos lleguen a un punto
21. **c** - El thread espera indefinidamente

### Parte 6: Patrones
22. **a** - Condition o Queue
23. **c** - Múltiples lectores O un escritor, pero no ambos
24. **a** - Evitar adquirir lock innecesariamente en casos comunes
25. **a** - Es thread-safe por diseño con operaciones bloqueantes

### Puntuación
- 23-25: Excelente dominio de sincronización
- 18-22: Buen nivel
- 13-17: Necesitas repasar algunos conceptos
- <13: Revisa el material nuevamente

</details>

---

*Computación II - 2026 - Clase 11*
