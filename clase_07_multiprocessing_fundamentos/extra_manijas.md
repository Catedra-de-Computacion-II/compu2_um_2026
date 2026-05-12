# Clase 7: Multiprocessing - Fundamentos — Extra Manijas

> *Material opcional. Sección en construcción.*

---

## Temas para profundizar

### 1. Internals: cómo implementa Python `Process` por debajo

Mirar el código fuente de `multiprocessing/process.py`. Ver cómo se traduce a `os.fork()` en Linux y a `CreateProcess()` en Windows.

### 2. Pickle: qué se puede y qué no

- Funciones top-level: sí
- Lambdas: no
- Closures: no
- Métodos de clase: depende
- Objetos con sockets/conexiones: generalmente no

Probar `dill` como alternativa (`pip install dill`).

### 3. Costo de creación

Medir el costo de:
- `fork()` puro
- `multiprocessing.Process` con `fork`
- `multiprocessing.Process` con `spawn`
- Crear un thread

Comparar latencia y throughput.

### 4. `multiprocessing.set_start_method` y la herencia de archivos

Cuando hacés `fork`, el hijo hereda todos los file descriptors abiertos del padre. Esto puede dar bugs sutiles si el padre tenía archivos/sockets/conexiones a base de datos abiertos. Con `spawn` esto no pasa.

### 5. Reactor pattern

Implementar un servidor que use un proceso por conexión usando solo `multiprocessing.Process`. Después comparalo con `socketserver` (clase 14) y con el manejo manual de la clase 3.

---

*Computación II - 2026 - Clase 7*
