# Clase 7: Multiprocessing - Fundamentos — Autoevaluación

> *Sección en construcción.*

---

## Preguntas conceptuales

1. ¿Qué ventajas tiene `multiprocessing.Process` sobre `os.fork()` directo?

2. ¿Para qué sirve el guard `if __name__ == "__main__":` y cuándo es obligatorio?

3. Explicá las diferencias entre `fork`, `spawn` y `forkserver`. ¿Cuál usarías en Windows? ¿Cuál en Linux para arranques rápidos?

4. Si un proceso hijo modifica una variable global heredada del padre (con `fork`), ¿el padre ve el cambio? ¿Por qué?

5. ¿Cómo se serializan los datos al pasarlos por una `multiprocessing.Queue`? ¿Qué limitación tiene?

6. ¿Cuál es la diferencia entre `terminate()` y `kill()`?

7. ¿En qué se parece `multiprocessing.Pipe()` al pipe de bajo nivel (clase 4)? ¿En qué se diferencia?

---

*Computación II - 2026 - Clase 7*
