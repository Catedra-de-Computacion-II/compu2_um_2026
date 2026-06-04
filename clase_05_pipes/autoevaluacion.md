# Clase 5: Pipes y Redirección - Autoevaluación

Responde estas preguntas para verificar tu comprensión. Las respuestas están al final.

---

## Parte 1: File Descriptors (6 preguntas)

### Pregunta 1
¿Cuáles son los tres file descriptors estándar y sus números?

a) input (0), output (1), error (2)
b) stdin (0), stdout (1), stderr (2)
c) read (0), write (1), log (2)
d) in (1), out (2), err (3)

### Pregunta 2
¿Qué representa un file descriptor?

a) El contenido de un archivo
b) Un índice en la tabla de archivos abiertos del proceso
c) La ubicación del archivo en disco
d) El nombre del archivo

### Pregunta 3
¿Qué hace la syscall dup2(old_fd, new_fd)?

a) Copia el contenido del archivo
b) Hace que new_fd apunte al mismo lugar que old_fd
c) Intercambia los dos file descriptors
d) Cierra ambos file descriptors

### Pregunta 4
Después de `dup2(5, 1)`, ¿a dónde va lo que se escribe a stdout?

a) Al file descriptor 5
b) A donde apuntaba el fd 5
c) A la terminal
d) A ningún lado, se pierde

### Pregunta 5
¿Qué función de Python retorna el file descriptor de un archivo abierto?

a) `f.fd()`
b) `f.fileno()`
c) `f.descriptor()`
d) `f.number()`

### Pregunta 6
Si abrís un archivo cuando los fds 0, 1, 2 ya están ocupados, ¿qué fd obtendrás probablemente?

a) 0
b) 1
c) 3
d) Un número aleatorio

---

## Parte 2: Redirección (5 preguntas)

### Pregunta 7
¿Qué hace `ls > archivo.txt` en bash?

a) Agrega la salida de ls al archivo
b) Crea o sobrescribe el archivo con la salida de ls
c) Lee el archivo y lo pasa a ls
d) Mueve ls al archivo

### Pregunta 8
¿Qué diferencia hay entre `>` y `>>`?

a) `>` es más rápido
b) `>` sobrescribe, `>>` agrega al final
c) `>>` es para stderr
d) No hay diferencia

### Pregunta 9
¿Qué significa `2>&1`?

a) Redirigir fd 2 a un archivo llamado "1"
b) Redirigir stderr a donde apunte stdout
c) Combinar dos archivos
d) Duplicar stdout

### Pregunta 10
En `comando > archivo 2>&1`, ¿a dónde van stdout y stderr?

a) stdout a archivo, stderr a terminal
b) Ambos a archivo
c) Ambos a terminal
d) stdout a terminal, stderr a archivo

### Pregunta 11
¿Qué hace `<` en bash?

a) Redirección de salida
b) Redirección de entrada (stdin)
c) Comparación
d) Pipe

---

## Parte 3: Pipes (8 preguntas)

### Pregunta 12
¿Qué es un pipe en Unix?

a) Un archivo especial en disco
b) Un canal de comunicación unidireccional entre procesos
c) Un programa para conectar comandos
d) Una variable de entorno

### Pregunta 13
¿Qué retorna os.pipe()?

a) Un file descriptor
b) Una tupla (read_fd, write_fd)
c) Un objeto pipe
d) El PID del proceso

### Pregunta 14
¿Por qué es importante cerrar el extremo del pipe que no usás?

a) Ahorra memoria
b) Permite detectar EOF y evita bloqueos indefinidos
c) Es más rápido
d) No es importante, es opcional

### Pregunta 15
¿Qué pasa si leés de un pipe vacío cuando todavía hay escritores?

a) Retorna string vacío
b) Bloquea hasta que lleguen datos
c) Lanza una excepción
d) Retorna None

### Pregunta 16
¿Qué pasa si leés de un pipe vacío sin escritores (todos cerraron)?

a) Bloquea indefinidamente
b) Lanza excepción
c) Retorna 0 bytes (EOF)
d) El proceso termina

### Pregunta 17
¿Qué señal recibe un proceso que escribe a un pipe sin lectores?

a) SIGINT
b) SIGTERM
c) SIGPIPE
d) SIGIO

### Pregunta 18
Para conectar `ls | grep txt`, ¿cuántos pipes necesitás?

a) Ninguno
b) 1
c) 2
d) 3

### Pregunta 19
En un pipeline `cmd1 | cmd2`, ¿qué fd de cmd1 se conecta a qué fd de cmd2?

a) stdin de cmd1 a stdout de cmd2
b) stdout de cmd1 a stdin de cmd2
c) stderr de cmd1 a stdin de cmd2
d) stdout de cmd1 a stderr de cmd2

---

## Parte 4: Named Pipes - FIFOs (3 preguntas)

### Pregunta 20
¿Cuál es la diferencia principal entre un pipe anónimo y un named pipe (FIFO)?

a) El FIFO es más rápido
b) El FIFO tiene nombre en el filesystem y puede conectar procesos no relacionados
c) El pipe anónimo es bidireccional
d) El FIFO solo funciona entre padre e hijo

### Pregunta 21
¿Qué función crea un named pipe en Python?

a) `os.pipe()`
b) `os.mkfifo()`
c) `os.mknod()`
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
b) `capture_output=True`
c) `get_stdout=True`
d) `stdout=True`

### Pregunta 24
¿Por qué es peligroso usar `shell=True` con input de usuario?

a) Es más lento
b) Permite inyección de comandos maliciosos
c) No funciona en Linux
d) Consume más memoria

### Pregunta 25
¿Cómo pasás input a un proceso con subprocess.run()?

a) `subprocess.run(cmd, stdin="datos")`
b) `subprocess.run(cmd, input="datos", text=True)`
c) `subprocess.run(cmd, data="datos")`
d) `subprocess.run(cmd, send="datos")`

---

## Respuestas

<details>
<summary>Click para ver respuestas</summary>

### Parte 1: File Descriptors
1. **b** - stdin (0), stdout (1), stderr (2)
2. **b** - Un índice en la tabla de archivos abiertos del proceso
3. **b** - Hace que new_fd apunte al mismo lugar que old_fd
4. **b** - A donde apuntaba el fd 5
5. **b** - `f.fileno()`
6. **c** - 3 (el menor fd disponible)

### Parte 2: Redirección
7. **b** - Crea o sobrescribe el archivo con la salida de ls
8. **b** - `>` sobrescribe, `>>` agrega al final
9. **b** - Redirigir stderr a donde apunte stdout
10. **b** - Ambos a archivo
11. **b** - Redirección de entrada (stdin)

### Parte 3: Pipes
12. **b** - Un canal de comunicación unidireccional entre procesos
13. **b** - Una tupla (read_fd, write_fd)
14. **b** - Permite detectar EOF y evita bloqueos indefinidos
15. **b** - Bloquea hasta que lleguen datos
16. **c** - Retorna 0 bytes (EOF)
17. **c** - SIGPIPE
18. **b** - 1
19. **b** - stdout de cmd1 a stdin de cmd2

### Parte 4: Named Pipes
20. **b** - El FIFO tiene nombre en el filesystem y puede conectar procesos no relacionados
21. **b** - `os.mkfifo()`
22. **b** - Bloquea hasta que un lector abra el otro extremo

### Parte 5: Subprocess
23. **b** - `capture_output=True`
24. **b** - Permite inyección de comandos maliciosos
25. **b** - `subprocess.run(cmd, input="datos", text=True)`

### Puntuación
- 23-25: Excelente dominio de pipes y redirección
- 18-22: Buen nivel
- 13-17: Necesitas repasar algunos conceptos
- <13: Revisa el material nuevamente

</details>

---

*Computación II - 2026 - Clase 5*
