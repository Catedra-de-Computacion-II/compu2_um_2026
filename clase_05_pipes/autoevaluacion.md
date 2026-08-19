# Clase 5: Pipes y Redirección - Autoevaluación

Responde estas preguntas para verificar tu comprensión. Las respuestas están al final.

---

## Parte 1: File Descriptors (6 preguntas)

### Pregunta 1
¿Cuáles son los tres file descriptors estándar y sus números?

a) in (1), out (2), err (3)
b) stdin (0), stdout (1), stderr (2)
c) input (0), output (1), error (2)
d) read (0), write (1), log (2)

### Pregunta 2
¿Qué representa un file descriptor?

a) El nombre del archivo
b) Un índice en la tabla de archivos abiertos del proceso
c) El contenido de un archivo
d) La ubicación del archivo en disco

### Pregunta 3
¿Qué hace la syscall dup2(old_fd, new_fd)?

a) Hace que new_fd apunte al mismo lugar que old_fd
b) Intercambia los dos file descriptors
c) Copia el contenido del archivo
d) Cierra ambos file descriptors

### Pregunta 4
Después de `dup2(5, 1)`, ¿a dónde va lo que se escribe a stdout?

a) Al file descriptor 5
b) A ningún lado, se pierde
c) A la terminal
d) A donde apuntaba el fd 5

### Pregunta 5
¿Qué función de Python retorna el file descriptor de un archivo abierto?

a) `f.fileno()`
b) `f.descriptor()`
c) `f.number()`
d) `f.fd()`

### Pregunta 6
Si abrís un archivo cuando los fds 0, 1, 2 ya están ocupados, ¿qué fd obtendrás probablemente?

a) Un número aleatorio
b) 0
c) 3
d) 1

---

## Parte 2: Redirección (5 preguntas)

### Pregunta 7
¿Qué hace `ls > archivo.txt` en bash?

a) Lee el archivo y lo pasa a ls
b) Crea o sobrescribe el archivo con la salida de ls
c) Mueve ls al archivo
d) Agrega la salida de ls al archivo

### Pregunta 8
¿Qué diferencia hay entre `>` y `>>`?

a) No hay diferencia
b) `>>` es para stderr
c) `>` sobrescribe, `>>` agrega al final
d) `>` es más rápido

### Pregunta 9
¿Qué significa `2>&1`?

a) Duplicar stdout
b) Redirigir stderr a donde apunte stdout
c) Combinar dos archivos
d) Redirigir fd 2 a un archivo llamado "1"

### Pregunta 10
En `comando > archivo 2>&1`, ¿a dónde van stdout y stderr?

a) Ambos a terminal
b) stdout a archivo, stderr a terminal
c) stdout a terminal, stderr a archivo
d) Ambos a archivo

### Pregunta 11
¿Qué hace `<` en bash?

a) Comparación
b) Redirección de entrada (stdin)
c) Pipe
d) Redirección de salida

---

## Parte 3: Pipes (8 preguntas)

### Pregunta 12
¿Qué es un pipe en Unix?

a) Un programa para conectar comandos
b) Un canal de comunicación unidireccional entre procesos
c) Una variable de entorno
d) Un archivo especial en disco

### Pregunta 13
¿Qué retorna os.pipe()?

a) El PID del proceso
b) Un file descriptor
c) Un objeto pipe
d) Una tupla (read_fd, write_fd)

### Pregunta 14
¿Por qué es importante cerrar el extremo del pipe que no usás?

a) No es importante, es opcional
b) Ahorra memoria
c) Permite detectar EOF y evita bloqueos indefinidos
d) Es más rápido

### Pregunta 15
¿Qué pasa si leés de un pipe vacío cuando todavía hay escritores?

a) Bloquea hasta que lleguen datos
b) Lanza una excepción
c) Retorna string vacío
d) Retorna None

### Pregunta 16
¿Qué pasa si leés de un pipe vacío sin escritores (todos cerraron)?

a) Lanza excepción
b) El proceso termina
c) Retorna 0 bytes (EOF)
d) Bloquea indefinidamente

### Pregunta 17
¿Qué señal recibe un proceso que escribe a un pipe sin lectores?

a) SIGTERM
b) SIGINT
c) SIGPIPE
d) SIGIO

### Pregunta 18
Para conectar `ls | grep txt`, ¿cuántos pipes necesitás?

a) 2
b) Ninguno
c) 3
d) 1

### Pregunta 19
En un pipeline `cmd1 | cmd2`, ¿qué fd de cmd1 se conecta a qué fd de cmd2?

a) stdout de cmd1 a stderr de cmd2
b) stderr de cmd1 a stdin de cmd2
c) stdin de cmd1 a stdout de cmd2
d) stdout de cmd1 a stdin de cmd2

---

## Parte 4: Named Pipes - FIFOs (3 preguntas)

### Pregunta 20
¿Cuál es la diferencia principal entre un pipe anónimo y un named pipe (FIFO)?

a) El FIFO solo funciona entre padre e hijo
b) El FIFO es más rápido
c) El FIFO tiene nombre en el filesystem y puede conectar procesos no relacionados
d) El pipe anónimo es bidireccional

### Pregunta 21
¿Qué función crea un named pipe en Python?

a) `os.mkfifo()`
b) `os.mknod()`
c) `os.pipe()`
d) `os.create_fifo()`

### Pregunta 22
¿Qué pasa cuando abrís un FIFO para escritura y no hay lectores?

a) Falla inmediatamente
b) Bloquea hasta que un lector abra el otro extremo
c) Los datos se pierden
d) Se crea un buffer temporal

---

## Parte 5: Subprocess (3 preguntas)

### Pregunta 23
¿Qué parámetro de subprocess.run() captura stdout?

a) `output=True`
b) `stdout=True`
c) `capture_output=True`
d) `get_stdout=True`

### Pregunta 24
¿Por qué es peligroso usar `shell=True` con input de usuario?

a) Consume más memoria
b) Permite inyección de comandos maliciosos
c) No funciona en Linux
d) Es más lento

### Pregunta 25
¿Cómo pasás input a un proceso con subprocess.run()?

a) `subprocess.run(cmd, data="datos")`
b) `subprocess.run(cmd, stdin="datos")`
c) `subprocess.run(cmd, input="datos", text=True)`
d) `subprocess.run(cmd, send="datos")`

---

## Respuestas

<details>
<summary>Click para ver respuestas</summary>

### Parte 1: File Descriptors
1. **b** - stdin (0), stdout (1), stderr (2)
2. **b** - Un índice en la tabla de archivos abiertos del proceso
3. **a** - Hace que new_fd apunte al mismo lugar que old_fd
4. **d** - A donde apuntaba el fd 5
5. **a** - `f.fileno()`
6. **c** - 3 (el menor fd disponible)

### Parte 2: Redirección
7. **b** - Crea o sobrescribe el archivo con la salida de ls
8. **c** - `>` sobrescribe, `>>` agrega al final
9. **b** - Redirigir stderr a donde apunte stdout
10. **d** - Ambos a archivo
11. **b** - Redirección de entrada (stdin)

### Parte 3: Pipes
12. **b** - Un canal de comunicación unidireccional entre procesos
13. **d** - Una tupla (read_fd, write_fd)
14. **c** - Permite detectar EOF y evita bloqueos indefinidos
15. **a** - Bloquea hasta que lleguen datos
16. **c** - Retorna 0 bytes (EOF)
17. **c** - SIGPIPE
18. **d** - 1
19. **d** - stdout de cmd1 a stdin de cmd2

### Parte 4: Named Pipes
20. **c** - El FIFO tiene nombre en el filesystem y puede conectar procesos no relacionados
21. **a** - `os.mkfifo()`
22. **b** - Bloquea hasta que un lector abra el otro extremo

### Parte 5: Subprocess
23. **c** - `capture_output=True`
24. **b** - Permite inyección de comandos maliciosos
25. **c** - `subprocess.run(cmd, input="datos", text=True)`

### Puntuación
- 23-25: Excelente dominio de pipes y redirección
- 18-22: Buen nivel
- 13-17: Necesitas repasar algunos conceptos
- <13: Revisa el material nuevamente

</details>

---

*Computación II - 2026 - Clase 5*
