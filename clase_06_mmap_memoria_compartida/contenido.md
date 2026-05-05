# Clase 6: mmap y Memoria Compartida

## Introducción: compartir memoria entre procesos

En las clases anteriores vimos cómo comunicar procesos usando pipes y FIFOs. Funcionan bien, pero tienen una limitación importante: los datos se **copian**. El escritor copia datos al kernel, el kernel los copia al lector. Para mensajes pequeños no importa, pero cuando necesitás compartir grandes volúmenes de datos entre procesos, esas copias se vuelven costosas.

¿Y si dos procesos pudieran acceder directamente a la misma región de memoria? Sin copias, sin intermediarios. Eso es exactamente lo que permite la **memoria compartida** y el mecanismo de **mmap**.

Hoy vamos a ver cómo funciona esto en Linux y Python, desde el nivel más bajo (mmap) hasta las abstracciones más cómodas que ofrece `multiprocessing`.

---

## ¿Por qué memoria compartida?

### El problema de copiar datos

Con pipes o colas, la comunicación sigue este camino:

```
Proceso A  ──(copia 1)──>  Kernel  ──(copia 2)──>  Proceso B
```

Cada envío implica al menos dos copias de los datos. Si estás compartiendo un array de 100 MB entre procesos, eso significa mover 200 MB de datos por cada actualización.

### La solución: compartir directamente

Con memoria compartida:

```
Proceso A  ──────┐
                  ├──>  Región de memoria compartida
Proceso B  ──────┘
```

Ambos procesos acceden a la misma región física de memoria. Cero copias. Velocidad máxima.

### Comparación

| Mecanismo | Copias por mensaje | Velocidad | Sincronización | Complejidad |
|-----------|--------|-----------|----------------|-------------|
| Pipe | 2 (escritor → kernel → lector) | Moderada | Implícita (FIFO) | Baja |
| Queue | 2 + serialización | Moderada | Implícita | Baja |
| Memoria compartida | 0 | Máxima | Manual (peligro) | Alta |

La velocidad tiene un costo: cuando dos procesos acceden a la misma memoria, vos sos responsable de que no se pisen entre sí. Pero eso lo veremos en detalle en las próximas clases sobre sincronización.

---

## mmap: el módulo fundamental

`mmap` viene de "memory-mapped file" (archivo mapeado a memoria). La idea es simple: tomar un archivo (o una región anónima de memoria) y hacerlo accesible como si fuera un array de bytes en memoria.

### mmap sobre un archivo

Cuando mapeás un archivo, el kernel conecta una región de memoria de tu proceso directamente con el contenido del archivo en disco. Los cambios en memoria se reflejan en el archivo y viceversa.

```python
import mmap

# Abrir un archivo existente
with open("datos.txt", "r+b") as f:
    # Mapear todo el archivo a memoria
    mm = mmap.mmap(f.fileno(), 0)  # 0 = mapear todo el archivo

    # Leer como si fuera un archivo
    print(mm.readline())

    # Acceder como si fuera un array de bytes
    print(mm[0:10])

    # Modificar directamente
    mm[0:5] = b"HOLA!"

    # Los cambios se escriben al archivo
    mm.flush()
    mm.close()
```

El primer argumento de `mmap.mmap()` es el file descriptor, y el segundo es el tamaño a mapear (0 = todo el archivo).

### Parámetros importantes de mmap

```python
import mmap

with open("datos.bin", "r+b") as f:
    mm = mmap.mmap(
        f.fileno(),        # File descriptor
        0,                 # Tamaño (0 = todo el archivo)
        access=mmap.ACCESS_WRITE,  # Permisos
        offset=0           # Desde dónde empezar a mapear
    )
```

Los modos de acceso son:

| Modo | Descripción |
|------|-------------|
| `ACCESS_READ` | Solo lectura |
| `ACCESS_WRITE` | Lectura y escritura (cambios van al archivo) |
| `ACCESS_COPY` | Copia privada (cambios NO van al archivo) |

### Operaciones sobre un mmap

Un objeto `mmap` se comporta como un mix entre archivo y bytearray:

```python
import mmap

with open("ejemplo.txt", "r+b") as f:
    mm = mmap.mmap(f.fileno(), 0)

    # Como archivo:
    mm.seek(0)
    linea = mm.readline()
    print(f"Primera línea: {linea}")

    # Como bytearray (slicing):
    datos = mm[10:20]
    print(f"Bytes 10-20: {datos}")

    # Buscar patrones:
    pos = mm.find(b"palabra")
    if pos != -1:
        print(f"Encontrado en posición {pos}")

    # Tamaño:
    print(f"Tamaño: {mm.size()} bytes")

    # Redimensionar (si es un archivo real):
    mm.resize(2048)

    mm.close()
```

### Crear y preparar un archivo para mmap

Un detalle importante: no podés mapear un archivo vacío. El archivo tiene que tener el tamaño que necesitás antes de mapearlo.

```python
import mmap
import os

# Crear un archivo con tamaño fijo
ruta = "/tmp/mi_mmap.bin"
tamaño = 1024  # 1 KB

with open(ruta, "wb") as f:
    f.write(b'\x00' * tamaño)  # Llenar con ceros

# Ahora sí, mapearlo
with open(ruta, "r+b") as f:
    mm = mmap.mmap(f.fileno(), tamaño)

    # Escribir datos
    mm[0:12] = b"Hola, mmap!"

    # Leer datos
    mm.seek(0)
    print(mm.read(12))  # b'Hola, mmap!'

    mm.close()

# Limpiar
os.unlink(ruta)
```

---

## mmap anónimo: memoria sin archivo

No siempre necesitás un archivo real. Podés crear una región de memoria compartida "anónima" (sin respaldo en disco). Esto es exactamente lo que necesitás para compartir memoria entre un proceso padre y sus hijos creados con `fork()`.

```python
import mmap
import os

# Crear mmap anónimo de 1024 bytes
# tagname="" y fileno=-1 indican que es anónimo
mm = mmap.mmap(-1, 1024)

pid = os.fork()

if pid == 0:
    # Hijo
    mm.seek(0)
    mm.write(b"Mensaje del hijo!")
    os._exit(0)
else:
    # Padre
    os.wait()
    mm.seek(0)
    datos = mm.read(17)
    print(f"El padre leyó: {datos}")  # b'Mensaje del hijo!'
    mm.close()
```

Cuando usás `mmap(-1, tamaño)`, el `-1` como file descriptor le dice al sistema que no hay archivo asociado. La memoria existe solo en RAM y se comparte entre padre e hijos gracias a que `fork()` hereda los mappings.

---

## mmap para IPC entre procesos

### Padre e hijo compartiendo memoria con fork

```python
import mmap
import os
import struct
import time

# Crear región compartida: un entero de 4 bytes
TAMAÑO = 4
mm = mmap.mmap(-1, TAMAÑO)

pid = os.fork()

if pid == 0:
    # === HIJO ===
    # Incrementar el valor 5 veces
    for i in range(5):
        mm.seek(0)
        valor_actual = struct.unpack('i', mm.read(4))[0]
        nuevo_valor = valor_actual + 1
        mm.seek(0)
        mm.write(struct.pack('i', nuevo_valor))
        print(f"[HIJO] Valor incrementado a: {nuevo_valor}")
        time.sleep(0.5)
    os._exit(0)

else:
    # === PADRE ===
    os.wait()
    mm.seek(0)
    valor_final = struct.unpack('i', mm.read(4))[0]
    print(f"[PADRE] Valor final: {valor_final}")  # 5
    mm.close()
```

### Compartir a través de un archivo mapeado

Si los procesos no son padre-hijo (por ejemplo, procesos independientes), podés usar un archivo como punto de encuentro:

**Proceso escritor:**

```python
#!/usr/bin/env python3
"""Proceso que escribe en memoria compartida via archivo."""
import mmap
import struct
import time

ARCHIVO = "/tmp/compartido.bin"
TAMAÑO = 256

# Crear archivo
with open(ARCHIVO, "wb") as f:
    f.write(b'\x00' * TAMAÑO)

with open(ARCHIVO, "r+b") as f:
    mm = mmap.mmap(f.fileno(), TAMAÑO)

    tiempos = []
    for i in range(10):
        mensaje = f"Dato #{i}: {time.ctime()}".encode()

        t0 = time.perf_counter()
        mm.seek(0)
        # Primero escribir largo, después el mensaje
        mm.write(struct.pack('i', len(mensaje)))
        mm.write(mensaje)
        # mm.flush()   # ← comentar/descomentar para comparar tiempos
        t1 = time.perf_counter()

        tiempos.append((t1 - t0) * 1_000_000)  # microsegundos
        print(f"[ESCRITOR] Escribí: {mensaje.decode()} ({tiempos[-1]:.1f} µs)")
        time.sleep(1)

    print(f"\nPromedio por escritura: {sum(tiempos)/len(tiempos):.1f} µs")
    mm.close()
```

> **Nota sobre `flush()`**: cuando ambos procesos usan `mmap` sobre el mismo archivo, **NO necesitás `flush()`** entre escrituras. Las páginas del kernel se comparten y los cambios son visibles al instante. Llamar `flush()` en cada iteración fuerza un round-trip al disco y mata la principal ventaja de mmap (la velocidad).
>
> **Probalo vos mismo**: descomentá la línea `mm.flush()` y compará los tiempos promedio. Vas a ver una diferencia notable (de microsegundos a milisegundos, según el disco).
>
> Sólo usá `flush()` cuando:
> - Querés **persistencia ante crashes** (que los datos sobrevivan un corte de luz)
> - El **lector NO usa mmap** y va a hacer `read()` normal
> - Necesitás un **snapshot consistente** en disco

**Proceso lector:**

```python
#!/usr/bin/env python3
"""Proceso que lee de memoria compartida via archivo."""
import mmap
import struct
import time

ARCHIVO = "/tmp/compartido.bin"
TAMAÑO = 256

with open(ARCHIVO, "r+b") as f:
    mm = mmap.mmap(f.fileno(), TAMAÑO)

    ultimo = ""
    for _ in range(15):
        mm.seek(0)
        largo = struct.unpack('i', mm.read(4))[0]
        if largo > 0:
            mensaje = mm.read(largo).decode()
            if mensaje != ultimo:
                print(f"[LECTOR] Leí: {mensaje}")
                ultimo = mensaje
        time.sleep(0.5)

    mm.close()
```

---

## multiprocessing.Value y multiprocessing.Array

Trabajar con `struct.pack` y `struct.unpack` para cada lectura y escritura es engorroso. Python ofrece wrappers más cómodos en el módulo `multiprocessing`.

### Value: compartir un valor simple

```python
from multiprocessing import Process, Value
import time

def incrementar(contador, n):
    """Incrementa el contador n veces."""
    for _ in range(n):
        contador.value += 1

# Crear valor compartido
# 'i' = entero con signo (mismos códigos que struct)
contador = Value('i', 0)

print(f"Valor inicial: {contador.value}")

p1 = Process(target=incrementar, args=(contador, 1000))
p2 = Process(target=incrementar, args=(contador, 1000))

p1.start()
p2.start()
p1.join()
p2.join()

print(f"Valor final: {contador.value}")
# OJO: probablemente NO sea 2000 - hay race condition!
# Esto lo resolveremos con sincronización en las próximas clases
```

Los códigos de tipo más comunes:

| Código | Tipo C | Tipo Python | Tamaño |
|--------|--------|-------------|--------|
| `'i'` | int | int | 4 bytes |
| `'d'` | double | float | 8 bytes |
| `'f'` | float | float | 4 bytes |
| `'c'` | char | bytes (1) | 1 byte |
| `'b'` | signed char | int | 1 byte |
| `'l'` | long | int | 4-8 bytes |

### Array: compartir una secuencia de valores

```python
from multiprocessing import Process, Array

def llenar_array(arr, inicio, fin, valor):
    """Llena una porción del array con un valor."""
    for i in range(inicio, fin):
        arr[i] = valor

# Crear array compartido de 10 enteros
arr = Array('i', 10)  # 10 enteros inicializados en 0

# También podés inicializar con valores:
# arr = Array('i', [1, 2, 3, 4, 5, 6, 7, 8, 9, 10])

p1 = Process(target=llenar_array, args=(arr, 0, 5, 1))
p2 = Process(target=llenar_array, args=(arr, 5, 10, 2))

p1.start()
p2.start()
p1.join()
p2.join()

print(f"Array: {list(arr)}")
# [1, 1, 1, 1, 1, 2, 2, 2, 2, 2]
```

### Array con doubles para cálculos numéricos

```python
from multiprocessing import Process, Array
import math

def calcular_senos(arr, inicio, fin):
    """Calcula seno para cada posición."""
    for i in range(inicio, fin):
        arr[i] = math.sin(i * 0.1)

# Array de 100 doubles
arr = Array('d', 100)

# Dividir trabajo en 4 procesos
procesos = []
chunk = 25
for i in range(4):
    p = Process(
        target=calcular_senos,
        args=(arr, i * chunk, (i + 1) * chunk)
    )
    p.start()
    procesos.append(p)

for p in procesos:
    p.join()

print(f"Primeros 10 valores: {[round(arr[i], 4) for i in range(10)]}")
```

---

## multiprocessing.shared_memory (Python 3.8+)

A partir de Python 3.8, el módulo `multiprocessing.shared_memory` ofrece una interfaz más moderna y flexible para memoria compartida. A diferencia de Value y Array, permite compartir bloques arbitrarios de bytes y tiene nombres que permiten conectar procesos independientes.

### SharedMemory: bloques de memoria con nombre

```python
from multiprocessing import shared_memory
import struct

# Crear un bloque de memoria compartida
shm = shared_memory.SharedMemory(create=True, size=1024, name="mi_bloque")
print(f"Nombre: {shm.name}")
print(f"Tamaño: {shm.size}")

# Acceder al buffer como bytearray
buffer = shm.buf

# Escribir datos
buffer[0:5] = b"Hola!"
struct.pack_into('i', buffer, 8, 42)  # Escribir entero en offset 8

# Leer datos
print(f"Texto: {bytes(buffer[0:5])}")
valor = struct.unpack_from('i', buffer, 8)[0]
print(f"Entero: {valor}")

# Limpiar
shm.close()
shm.unlink()  # Eliminar el bloque del sistema
```

### Conectar desde otro proceso

La gracia de `SharedMemory` es que podés conectarte por nombre:

**Proceso 1 (crea la memoria):**

```python
#!/usr/bin/env python3
"""Crea memoria compartida y espera."""
from multiprocessing import shared_memory
import time

shm = shared_memory.SharedMemory(create=True, size=256, name="canal_datos")
print(f"Memoria creada: {shm.name}")
print("Esperando que el otro proceso escriba...")

time.sleep(5)

# Leer lo que escribió el otro proceso
datos = bytes(shm.buf[0:50]).rstrip(b'\x00')
print(f"Recibí: {datos.decode()}")

shm.close()
shm.unlink()
```

**Proceso 2 (se conecta):**

```python
#!/usr/bin/env python3
"""Se conecta a memoria compartida existente."""
from multiprocessing import shared_memory

# Conectar por nombre (NO usar create=True)
shm = shared_memory.SharedMemory(name="canal_datos")
print(f"Conectado a: {shm.name}")

# Escribir datos
mensaje = b"Saludos desde el otro proceso!"
shm.buf[0:len(mensaje)] = mensaje
print(f"Escribí: {mensaje.decode()}")

shm.close()  # Cerrar pero NO unlink (no somos el dueño)
```

### ShareableList: lista compartida entre procesos

`ShareableList` es una lista de tamaño fijo que puede contener enteros, floats, bools, strings y None:

```python
from multiprocessing import shared_memory, Process

def modificar_lista(nombre):
    """Se conecta a la lista compartida y la modifica."""
    sl = shared_memory.ShareableList(name=nombre)
    sl[0] = 100
    sl[1] = 3.14
    sl[2] = "modificado"
    sl.shm.close()

# Crear lista compartida
sl = shared_memory.ShareableList(
    [0, 0.0, "original", True],
    name="mi_lista"
)
print(f"Antes: {list(sl)}")

p = Process(target=modificar_lista, args=(sl.shm.name,))
p.start()
p.join()

print(f"Después: {list(sl)}")
# [100, 3.14, 'modificado', True]

sl.shm.close()
sl.shm.unlink()
```

### SharedMemory con multiprocessing.Process

```python
from multiprocessing import Process, shared_memory
import struct
import time

def worker(shm_name, worker_id, offset, cantidad):
    """Cada worker escribe su porción del buffer compartido."""
    shm = shared_memory.SharedMemory(name=shm_name)

    for i in range(cantidad):
        pos = (offset + i) * 4  # 4 bytes por entero
        struct.pack_into('i', shm.buf, pos, worker_id * 1000 + i)

    print(f"[Worker {worker_id}] Escribí {cantidad} valores desde offset {offset}")
    shm.close()

# Crear memoria compartida para 40 enteros (160 bytes)
NUM_ENTEROS = 40
shm = shared_memory.SharedMemory(create=True, size=NUM_ENTEROS * 4)

# 4 workers, cada uno escribe 10 enteros
procesos = []
for w in range(4):
    p = Process(target=worker, args=(shm.name, w, w * 10, 10))
    p.start()
    procesos.append(p)

for p in procesos:
    p.join()

# Leer resultados
valores = struct.unpack_from(f'{NUM_ENTEROS}i', shm.buf)
print(f"Valores: {valores}")

shm.close()
shm.unlink()
```

---

## close() vs unlink(): no confundirlos

Esta distinción es importante y fuente de errores comunes:

- **`close()`**: desconecta este proceso de la memoria compartida. El bloque sigue existiendo en el sistema.
- **`unlink()`**: elimina el bloque de memoria compartida del sistema. Solo debe hacerlo el proceso "dueño".

```python
from multiprocessing import shared_memory

# Proceso "dueño": crea y al final hace unlink
shm = shared_memory.SharedMemory(create=True, size=100, name="ejemplo")
# ... usar ...
shm.close()
shm.unlink()  # Elimina del sistema

# Proceso "cliente": solo hace close
shm = shared_memory.SharedMemory(name="ejemplo")
# ... usar ...
shm.close()   # Se desconecta, pero no elimina
# NO hacer shm.unlink() acá
```

Si olvidás hacer `unlink()`, la memoria queda asignada en el sistema hasta que reinicies. Si hacés `unlink()` antes de que otros procesos terminen de usar la memoria, van a tener problemas.

---

## ¿Cuándo usar memoria compartida vs pipes/colas?

### Usá memoria compartida cuando:

- Necesitás **máxima velocidad** de comunicación
- Compartís **grandes volúmenes de datos** (arrays, matrices, imágenes)
- Múltiples procesos necesitan **leer los mismos datos** frecuentemente
- Los datos se **actualizan in-place** (no se envían copias completas)

### Usá pipes o colas cuando:

- Necesitás **comunicación secuencial** (mensajes uno tras otro)
- La **sincronización implícita** te simplifica la vida (el lector espera al escritor)
- Los datos son **pequeños** y la velocidad no es crítica
- Preferís **simplicidad** sobre rendimiento

### Tabla resumen

| Criterio | Pipe/Queue | Memoria compartida |
|----------|------------|-------------------|
| Velocidad | Buena | Excelente |
| Sincronización | Incluida | Manual |
| Simplicidad | Alta | Baja |
| Datos grandes | Ineficiente | Ideal |
| Procesos independientes | Fácil (Queue) | Requiere nombre/archivo |
| Riesgo de bugs | Bajo | Alto (race conditions) |

---

## El peligro: race conditions

Cuando dos procesos acceden a la misma memoria sin coordinación, pueden pasar cosas raras:

```python
from multiprocessing import Process, Value

def incrementar(contador, n):
    for _ in range(n):
        # Esto NO es atómico:
        # 1. Lee valor actual
        # 2. Suma 1
        # 3. Escribe nuevo valor
        # Otro proceso puede meterse entre el paso 1 y el 3
        contador.value += 1

contador = Value('i', 0)

p1 = Process(target=incrementar, args=(contador, 100000))
p2 = Process(target=incrementar, args=(contador, 100000))

p1.start()
p2.start()
p1.join()
p2.join()

print(f"Esperado: 200000")
print(f"Obtenido: {contador.value}")
# Probablemente sea MENOR que 200000!
```

Ejecutá este programa varias veces y vas a ver que el resultado cambia. Eso es una **race condition**: el resultado depende de la "carrera" entre los procesos. Esto es un tema central que profundizaremos en las clases 8 y 9 sobre sincronización.

### Anticipo: la solución con Lock

```python
from multiprocessing import Process, Value, Lock

def incrementar_seguro(contador, lock, n):
    for _ in range(n):
        with lock:  # Solo un proceso a la vez
            contador.value += 1

contador = Value('i', 0)
lock = Lock()

p1 = Process(target=incrementar_seguro, args=(contador, lock, 100000))
p2 = Process(target=incrementar_seguro, args=(contador, lock, 100000))

p1.start()
p2.start()
p1.join()
p2.join()

print(f"Esperado: 200000")
print(f"Obtenido: {contador.value}")
# Ahora sí: 200000 siempre
```

No te preocupes por entender Lock en detalle ahora, lo veremos a fondo más adelante.

---

## Conceptos clave

1. **Memoria compartida elimina las copias** - Los procesos acceden directamente a la misma región de memoria física, sin pasar por el kernel.

2. **mmap mapea archivos o memoria anónima** al espacio de direcciones del proceso. Es la base de toda la memoria compartida en Linux.

3. **mmap anónimo (`mmap(-1, tamaño)`)** crea memoria compartida sin archivo, ideal para padre-hijo con fork.

4. **Value y Array** son wrappers cómodos de `multiprocessing` para compartir tipos simples entre procesos.

5. **SharedMemory** (Python 3.8+) permite compartir bloques de memoria con nombre, conectando incluso procesos independientes.

6. **close() no es unlink()** - `close()` desconecta al proceso, `unlink()` elimina la memoria del sistema.

7. **Sin sincronización hay race conditions** - Múltiples procesos escribiendo en la misma memoria sin coordinación produce resultados impredecibles.

---

## Preparación para la próxima clase

En la clase 7 veremos **multiprocessing avanzado**: Pool para distribuir trabajo entre múltiples procesos, Queue y Pipe como canales de comunicación de alto nivel, y cómo combinar todo para construir programas concurrentes eficientes.

---

*Computación II - 2026 - Clase 6*
