# Clase 7: Multiprocessing - Fundamentos — Ejercicios

> *Ejercicios a desarrollar en clase. Esta sección está en construcción.*

---

## Ejercicio 1: Tu primer Process

Adaptá el ejemplo de `os.fork()` de la clase 3 a `multiprocessing.Process`. Compará las dos APIs: ¿qué pasos te ahorrás?

## Ejercicio 2: 5 workers en paralelo

Lanzá 5 procesos que esperen un tiempo random entre 0.5 y 2 segundos cada uno. El programa principal debe esperar a todos y reportar el tiempo total.

## Ejercicio 3: Productor-Consumidor con Queue

Implementá productor + consumidor usando `multiprocessing.Queue`. El productor genera 10 items, el consumidor los procesa.

## Ejercicio 4: Pipe bidireccional

Padre e hijo se mandan 5 mensajes alternados (ping-pong) usando `multiprocessing.Pipe()`.

## Ejercicio 5: fork vs spawn

Corré el mismo programa con `set_start_method('fork')` y `set_start_method('spawn')`. Medí el tiempo de creación de 100 procesos en cada caso.

---

*Computación II - 2026 - Clase 7*
