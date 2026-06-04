# Clase 5: Pipes y Redirección - Ejercicios Prácticos

## Ejercicio 1: Explorando file descriptors

### 1.1 File descriptors en la terminal

Abrí una terminal y explorá los file descriptors de tu shell:

```bash
# Ver file descriptors del shell actual
ls -la /proc/$$/fd

# Deberías ver al menos:
# 0 -> /dev/pts/X (stdin)
# 1 -> /dev/pts/X (stdout)
# 2 -> /dev/pts/X (stderr)
```

Ahora probá esto:

```bash
# Abrir un archivo y ver que aparece un nuevo fd
exec 3< /etc/passwd
ls -la /proc/$$/fd

# Ver que fd 3 está abierto
# Leer una línea del fd 3
read linea <&3
echo "Leí: $linea"

# Cerrar el fd 3
exec 3<&-
ls -la /proc/$$/fd
```

### 1.2 File descriptors en Python

Creá `explorar_fds.py`:

```python
#!/usr/bin/env python3
"""Explorar file descriptors del proceso actual."""
import os

def listar_fds():
    """Lista los file descriptors abiertos."""
    fd_dir = f"/proc/{os.getpid()}/fd"
    print(f"File descriptors de PID {os.getpid()}:")

    for fd in sorted(os.listdir(fd_dir), key=int):
        try:
            target = os.readlink(f"{fd_dir}/{fd}")
            print(f"  fd {fd} -> {target}")
        except OSError as e:
            print(f"  fd {fd} -> (error: {e})")

print("=== Estado inicial ===")
listar_fds()

print("\n=== Después de abrir un archivo ===")
f = open("/tmp/test_fd.txt", "w")
print(f"Archivo abierto con fd {f.fileno()}")
listar_fds()

print("\n=== Después de abrir otro ===")
f2 = open("/etc/passwd", "r")
print(f"Segundo archivo con fd {f2.fileno()}")
listar_fds()

print("\n=== Después de cerrar el primero ===")
f.close()
listar_fds()

print("\n=== Después de cerrar todo ===")
f2.close()
listar_fds()
```

---

## Ejercicio 2: Redirección básica

### 2.1 Redirección manual con dup2

Implementá redirección de stdout a archivo sin usar la sintaxis del shell:

```python
#!/usr/bin/env python3
"""Redirección manual de stdout."""
import os
import sys

print("Este mensaje va a la terminal")

# Guardar stdout original
stdout_original = os.dup(1)

# Abrir archivo destino
archivo = os.open("/tmp/salida.txt", os.O_CREAT | os.O_WRONLY | os.O_TRUNC, 0o644)

# Redirigir stdout
os.dup2(archivo, 1)
os.close(archivo)

# Ahora stdout va al archivo
print("Este mensaje va al archivo")
print("Y este también")
sys.stdout.flush()

# Restaurar stdout original
os.dup2(stdout_original, 1)
os.close(stdout_original)

print("Volvimos a la terminal")
print(f"Revisá el contenido de /tmp/salida.txt")
```

### 2.2 Separando stdout y stderr

Creá un programa que demuestre la diferencia entre stdout y stderr:

```python
#!/usr/bin/env python3
"""Demostración de stdout vs stderr."""
import sys
import os

# Escribir a stdout
print("Mensaje normal a stdout")
sys.stdout.write("Otro mensaje a stdout\n")
os.write(1, b"Y otro mas directo al fd 1\n")

# Escribir a stderr
print("Mensaje de error a stderr", file=sys.stderr)
sys.stderr.write("Otro error a stderr\n")
os.write(2, b"Error directo al fd 2\n")
```

Probalo con diferentes redirecciones:

```bash
python3 separar_salidas.py > solo_stdout.txt
python3 separar_salidas.py 2> solo_stderr.txt
python3 separar_salidas.py > stdout.txt 2> stderr.txt
python3 separar_salidas.py > todo.txt 2>&1
```

---

## Ejercicio 3: Pipes básicos

### 3.1 Pipe entre padre e hijo

```python
#!/usr/bin/env python3
"""Comunicación básica por pipe."""
import os

# Crear pipe ANTES del fork
read_fd, write_fd = os.pipe()

pid = os.fork()

if pid == 0:
    # === HIJO: escribe al pipe ===
    os.close(read_fd)  # No necesita leer

    mensajes = [
        "Mensaje 1 del hijo",
        "Mensaje 2 del hijo",
        "Mensaje 3 del hijo",
        "FIN"
    ]

    for msg in mensajes:
        os.write(write_fd, (msg + "\n").encode())
        print(f"[HIJO] Envié: {msg}")

    os.close(write_fd)
    os._exit(0)

else:
    # === PADRE: lee del pipe ===
    os.close(write_fd)  # No necesita escribir

    print("[PADRE] Esperando mensajes del hijo...\n")

    # Leer todo lo que venga por el pipe
    buffer = b""
    while True:
        datos = os.read(read_fd, 1024)
        if not datos:  # EOF - el hijo cerró su extremo
            break
        buffer += datos

    # Procesar los mensajes
    mensajes = buffer.decode().strip().split("\n")
    for msg in mensajes:
        print(f"[PADRE] Recibí: {msg}")

    os.close(read_fd)
    os.wait()
    print("\n[PADRE] Hijo terminó")
```

### 3.2 Comunicación bidireccional

Para comunicación en ambas direcciones, necesitás dos pipes:

```python
#!/usr/bin/env python3
"""Comunicación bidireccional con dos pipes."""
import os

# Pipe 1: padre -> hijo
p2h_read, p2h_write = os.pipe()

# Pipe 2: hijo -> padre
h2p_read, h2p_write = os.pipe()

pid = os.fork()

if pid == 0:
    # === HIJO ===
    os.close(p2h_write)  # No escribe al pipe padre->hijo
    os.close(h2p_read)   # No lee del pipe hijo->padre

    # Leer pregunta del padre
    pregunta = os.read(p2h_read, 1024).decode().strip()
    print(f"[HIJO] Recibí pregunta: {pregunta}")

    # Calcular respuesta
    if pregunta.isdigit():
        respuesta = str(int(pregunta) ** 2)
    else:
        respuesta = "No es un número"

    # Enviar respuesta
    os.write(h2p_write, respuesta.encode())
    print(f"[HIJO] Envié respuesta: {respuesta}")

    os.close(p2h_read)
    os.close(h2p_write)
    os._exit(0)

else:
    # === PADRE ===
    os.close(p2h_read)   # No lee del pipe padre->hijo
    os.close(h2p_write)  # No escribe al pipe hijo->padre

    # Enviar pregunta
    numero = "42"
    print(f"[PADRE] Enviando número: {numero}")
    os.write(p2h_write, numero.encode())
    os.close(p2h_write)  # Señalar que terminamos de escribir

    # Leer respuesta
    respuesta = os.read(h2p_read, 1024).decode()
    print(f"[PADRE] Respuesta: {numero}² = {respuesta}")

    os.close(h2p_read)
    os.wait()
```

---

## Ejercicio 4: Pipeline de comandos

### 4.1 Conectando dos comandos

Implementá el equivalente a `ls -la | grep txt`:

```python
#!/usr/bin/env python3
"""Pipeline de dos comandos."""
import os

def pipeline_dos_comandos(cmd1, args1, cmd2, args2):
    """Ejecuta cmd1 | cmd2"""

    # Crear pipe
    read_fd, write_fd = os.pipe()

    # Primer proceso
    pid1 = os.fork()
    if pid1 == 0:
        os.close(read_fd)      # No lee
        os.dup2(write_fd, 1)   # stdout -> pipe
        os.close(write_fd)
        os.execvp(cmd1, [cmd1] + args1)
        os._exit(1)

    # Segundo proceso
    pid2 = os.fork()
    if pid2 == 0:
        os.close(write_fd)     # No escribe
        os.dup2(read_fd, 0)    # stdin <- pipe
        os.close(read_fd)
        os.execvp(cmd2, [cmd2] + args2)
        os._exit(1)

    # Padre
    os.close(read_fd)
    os.close(write_fd)
    os.waitpid(pid1, 0)
    os.waitpid(pid2, 0)

if __name__ == "__main__":
    print("=== ls -la | grep '.py' ===")
    pipeline_dos_comandos("ls", ["-la"], "grep", [".py"])
```

### 4.2 Pipeline de tres comandos

Extendé para manejar tres comandos:

```python
#!/usr/bin/env python3
"""Pipeline de tres comandos: cmd1 | cmd2 | cmd3"""
import os

def pipeline_tres_comandos(cmd1, args1, cmd2, args2, cmd3, args3):
    """Ejecuta cmd1 | cmd2 | cmd3"""

    # Dos pipes
    pipe1_read, pipe1_write = os.pipe()
    pipe2_read, pipe2_write = os.pipe()

    # cmd1: stdout -> pipe1
    pid1 = os.fork()
    if pid1 == 0:
        os.close(pipe1_read)
        os.close(pipe2_read)
        os.close(pipe2_write)
        os.dup2(pipe1_write, 1)
        os.close(pipe1_write)
        os.execvp(cmd1, [cmd1] + args1)
        os._exit(1)

    # cmd2: stdin <- pipe1, stdout -> pipe2
    pid2 = os.fork()
    if pid2 == 0:
        os.close(pipe1_write)
        os.close(pipe2_read)
        os.dup2(pipe1_read, 0)
        os.dup2(pipe2_write, 1)
        os.close(pipe1_read)
        os.close(pipe2_write)
        os.execvp(cmd2, [cmd2] + args2)
        os._exit(1)

    # cmd3: stdin <- pipe2
    pid3 = os.fork()
    if pid3 == 0:
        os.close(pipe1_read)
        os.close(pipe1_write)
        os.close(pipe2_write)
        os.dup2(pipe2_read, 0)
        os.close(pipe2_read)
        os.execvp(cmd3, [cmd3] + args3)
        os._exit(1)

    # Padre: cerrar todos los pipes y esperar
    os.close(pipe1_read)
    os.close(pipe1_write)
    os.close(pipe2_read)
    os.close(pipe2_write)

    os.waitpid(pid1, 0)
    os.waitpid(pid2, 0)
    os.waitpid(pid3, 0)

if __name__ == "__main__":
    # cat /etc/passwd | grep "root" | wc -l
    print("=== cat /etc/passwd | grep root | wc -l ===")
    pipeline_tres_comandos(
        "cat", ["/etc/passwd"],
        "grep", ["root"],
        "wc", ["-l"]
    )
```

---

## Ejercicio 5: Mini-shell con redirección (Obligatorio)

### Objetivo

Extender el mini-shell de la clase anterior para soportar redirección de salida (`>`).

### Especificación

El shell debe soportar:

```bash
minish$ ls -la              # Comando normal
minish$ ls -la > archivo.txt # Redirección de salida
minish$ echo hola > saludo.txt
minish$ cat < entrada.txt    # (BONUS: redirección de entrada)
```

### Esqueleto

```python
#!/usr/bin/env python3
"""Mini-shell con redirección."""
import os
import sys

def parsear_linea(linea):
    """
    Parsea una línea de comando.
    Retorna (comando, args, archivo_salida, archivo_entrada)

    Ejemplos:
      "ls -la" -> ("ls", ["-la"], None, None)
      "ls > out.txt" -> ("ls", [], "out.txt", None)
      "cat < in.txt" -> ("cat", [], None, "in.txt")
    """
    # TODO: implementar
    partes = linea.split()
    comando = partes[0] if partes else None
    args = []
    archivo_salida = None
    archivo_entrada = None

    # Buscar > y <
    i = 1
    while i < len(partes):
        if partes[i] == ">":
            archivo_salida = partes[i + 1]
            i += 2
        elif partes[i] == "<":
            archivo_entrada = partes[i + 1]
            i += 2
        else:
            args.append(partes[i])
            i += 1

    return comando, args, archivo_salida, archivo_entrada

def ejecutar(comando, args, archivo_salida=None, archivo_entrada=None):
    """Ejecuta un comando con redirección opcional."""
    pid = os.fork()

    if pid == 0:
        # Configurar redirecciones ANTES del exec

        if archivo_salida:
            fd = os.open(archivo_salida, os.O_CREAT | os.O_WRONLY | os.O_TRUNC, 0o644)
            os.dup2(fd, 1)  # stdout -> archivo
            os.close(fd)

        if archivo_entrada:
            fd = os.open(archivo_entrada, os.O_RDONLY)
            os.dup2(fd, 0)  # stdin <- archivo
            os.close(fd)

        # Ejecutar
        try:
            os.execvp(comando, [comando] + args)
        except OSError as e:
            print(f"Error: {e}", file=sys.stderr)
            os._exit(127)

    else:
        _, status = os.wait()
        return os.WEXITSTATUS(status)

def main():
    while True:
        try:
            linea = input("minish$ ")
        except EOFError:
            print("\nChau!")
            break

        linea = linea.strip()
        if not linea:
            continue

        if linea == "exit":
            break

        comando, args, salida, entrada = parsear_linea(linea)
        if comando:
            ejecutar(comando, args, salida, entrada)

if __name__ == "__main__":
    main()
```

### Verificación

Tu shell debe pasar estas pruebas:

```bash
minish$ echo "hola mundo" > test.txt
minish$ cat test.txt
hola mundo
minish$ ls -la > listado.txt
minish$ wc -l < listado.txt
10  # (o el número que sea)
minish$ exit
```

---

## Ejercicio 6: Procesador de texto con pipes

### 6.1 Filtro de texto en Python

Creá un programa que funcione como filtro Unix (lee stdin, escribe stdout):

```python
#!/usr/bin/env python3
"""Filtro que convierte a mayúsculas."""
import sys

for linea in sys.stdin:
    sys.stdout.write(linea.upper())
```

Probalo:

```bash
echo "hola mundo" | python3 mayusculas.py
cat archivo.txt | python3 mayusculas.py | head -5
```

### 6.2 Procesamiento con subprocess

```python
#!/usr/bin/env python3
"""Procesar texto usando pipeline de subprocess."""
import subprocess

texto = """
primera linea
segunda linea con error
tercera linea
otra linea con error
ultima linea
"""

# Pipeline: echo texto | grep error | wc -l
# Usando subprocess para construir el pipeline

echo = subprocess.Popen(
    ["echo", texto],
    stdout=subprocess.PIPE
)

grep = subprocess.Popen(
    ["grep", "error"],
    stdin=echo.stdout,
    stdout=subprocess.PIPE
)

wc = subprocess.Popen(
    ["wc", "-l"],
    stdin=grep.stdout,
    stdout=subprocess.PIPE,
    text=True
)

# Importante: cerrar pipes del padre
echo.stdout.close()
grep.stdout.close()

resultado, _ = wc.communicate()
print(f"Líneas con 'error': {resultado.strip()}")
```

---

## Ejercicio 7: Named pipe para comunicación entre programas

### 7.1 Escritor y lector independientes

Creá dos programas que se comuniquen via named pipe.

**escritor_fifo.py:**
```python
#!/usr/bin/env python3
"""Escribe a un named pipe."""
import os
import time

FIFO = "/tmp/mi_canal"

# Crear FIFO si no existe
if not os.path.exists(FIFO):
    os.mkfifo(FIFO)

print(f"Escribiendo a {FIFO}...")
print("(Ejecutá lector_fifo.py en otra terminal)")

with open(FIFO, 'w') as f:
    for i in range(10):
        mensaje = f"Mensaje {i}: {time.ctime()}"
        print(f"Enviando: {mensaje}")
        f.write(mensaje + "\n")
        f.flush()
        time.sleep(1)

print("Escritura completada")
```

**lector_fifo.py:**
```python
#!/usr/bin/env python3
"""Lee de un named pipe."""

FIFO = "/tmp/mi_canal"

print(f"Leyendo de {FIFO}...")

with open(FIFO, 'r') as f:
    for linea in f:
        print(f"Recibido: {linea.strip()}")

print("Lectura completada (el escritor cerró el pipe)")
```

Ejecutá el escritor en una terminal y el lector en otra.

---

## Verificación del ejercicio obligatorio

### Ejercicio 5: Mini-shell con redirección

Tu implementación debe:

- [ ] Parsear correctamente `>` para redirección de salida
- [ ] Crear/truncar el archivo de salida
- [ ] Redirigir stdout del comando al archivo
- [ ] Funcionar con cualquier comando
- [ ] (BONUS) Soportar `<` para redirección de entrada
- [ ] (BONUS) Soportar `>>` para append

---

## Ejercicios adicionales

### Tee casero

Implementá el comando `tee` que duplica la entrada a stdout Y a un archivo:

```bash
ls -la | python3 mi_tee.py salida.txt
# La salida aparece en pantalla Y se guarda en salida.txt
```

### Monitor de pipe

Creá un programa que se interponga en un pipeline y muestre estadísticas de los datos que pasan:

```bash
cat archivo_grande | python3 monitor.py | wc -l
# Monitor muestra: "Procesados 1000 bytes, 50 líneas..."
```

---

*Computación II - 2026 - Clase 5*
