# Clase 6: mmap y Memoria Compartida - Ejercicios Prácticos

## Ejercicio 1: Explorando mmap sobre archivos

### 1.1 Crear y mapear un archivo

```python
#!/usr/bin/env python3
"""Crear un archivo, mapearlo y modificarlo con mmap."""
import mmap

# Crear archivo con contenido
with open("/tmp/mmap_test.txt", "wb") as f:
    f.write(b"Linea 1: Hola mundo\n")
    f.write(b"Linea 2: Computacion II\n")
    f.write(b"Linea 3: mmap es genial\n")

# Mapear el archivo
with open("/tmp/mmap_test.txt", "r+b") as f:
    mm = mmap.mmap(f.fileno(), 0)

    # Leer todo el contenido
    print("=== Contenido completo ===")
    print(mm[:].decode())

    # Leer línea por línea
    print("=== Línea por línea ===")
    mm.seek(0)
    while True:
        linea = mm.readline()
        if not linea:
            break
        print(f"  {linea.decode().strip()}")

    # Buscar texto
    pos = mm.find(b"mmap")
    print(f"\n'mmap' encontrado en posición: {pos}")

    # Modificar una parte
    mm.seek(pos)
    mm.write(b"MMAP")  # Sobrescribir en mayúsculas

    # Ver resultado
    mm.seek(0)
    print(f"\n=== Después de modificar ===")
    print(mm[:].decode())

    mm.close()
```

### 1.2 mmap en modo solo lectura

```python
#!/usr/bin/env python3
"""Mapear archivo en modo solo lectura."""
import mmap

# Asegurate de tener el archivo del ejercicio anterior
with open("/tmp/mmap_test.txt", "rb") as f:
    mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)

    # Esto funciona:
    print(f"Contenido: {mm[:40]}")
    print(f"Tamaño: {mm.size()} bytes")

    # Esto lanza excepción:
    try:
        mm[0:4] = b"TEST"
    except TypeError as e:
        print(f"Error al escribir: {e}")

    mm.close()
```

**Tarea:** Creá un archivo con 5 líneas de texto. Mapealo con mmap, buscá una palabra específica con `find()` y reemplazala por otra del mismo largo. Verificá que el archivo en disco cambió usando `cat`.

---

## Ejercicio 2: mmap como estructura de datos binaria

### 2.1 Almacenar y leer números

```python
#!/usr/bin/env python3
"""Usar mmap como almacenamiento binario estructurado."""
import mmap
import struct
import os

ARCHIVO = "/tmp/numeros.bin"
NUM_ELEMENTOS = 10
TAMAÑO = NUM_ELEMENTOS * 4  # 4 bytes por entero

# Crear archivo con tamaño fijo
with open(ARCHIVO, "wb") as f:
    f.write(b'\x00' * TAMAÑO)

with open(ARCHIVO, "r+b") as f:
    mm = mmap.mmap(f.fileno(), TAMAÑO)

    # Escribir números
    print("Escribiendo números...")
    for i in range(NUM_ELEMENTOS):
        valor = (i + 1) * 100
        struct.pack_into('i', mm, i * 4, valor)
        print(f"  Posición {i}: {valor}")

    # Leer todos los números
    print("\nLeyendo números...")
    for i in range(NUM_ELEMENTOS):
        valor = struct.unpack_from('i', mm, i * 4)[0]
        print(f"  Posición {i}: {valor}")

    # Modificar uno
    struct.pack_into('i', mm, 3 * 4, 9999)
    print(f"\nPosición 3 modificada a: {struct.unpack_from('i', mm, 3 * 4)[0]}")

    mm.close()

os.unlink(ARCHIVO)
```

**Tarea:** Modificá el ejercicio para almacenar un "registro" con: un entero (id), un float (nota) y 20 bytes de texto (nombre). Escribí 5 registros y leelos.

Ayuda: el formato de struct sería `'i f 20s'` (entero + float + 20 chars).

---

## Ejercicio 3: mmap anónimo entre padre e hijo

### 3.1 Comunicación simple con fork

```python
#!/usr/bin/env python3
"""Padre e hijo se comunican vía mmap anónimo."""
import mmap
import os
import struct
import time

# Crear mmap anónimo
mm = mmap.mmap(-1, 256)

pid = os.fork()

if pid == 0:
    # === HIJO ===
    print(f"[HIJO {os.getpid()}] Escribiendo datos...")

    # Escribir un entero
    struct.pack_into('i', mm, 0, 42)

    # Escribir un string
    mensaje = b"Hola desde el hijo!"
    struct.pack_into('i', mm, 4, len(mensaje))  # largo
    mm[8:8+len(mensaje)] = mensaje

    print("[HIJO] Datos escritos, terminando")
    os._exit(0)

else:
    # === PADRE ===
    os.wait()
    print(f"[PADRE] Hijo terminó, leyendo datos...")

    # Leer entero
    numero = struct.unpack_from('i', mm, 0)[0]
    print(f"[PADRE] Número: {numero}")

    # Leer string
    largo = struct.unpack_from('i', mm, 4)[0]
    mensaje = bytes(mm[8:8+largo]).decode()
    print(f"[PADRE] Mensaje: {mensaje}")

    mm.close()
```

### 3.2 Múltiples hijos escribiendo en regiones separadas

```python
#!/usr/bin/env python3
"""Varios hijos escriben en regiones separadas del mmap."""
import mmap
import os
import struct

NUM_HIJOS = 4
TAMAÑO_POR_HIJO = 64
TAMAÑO_TOTAL = NUM_HIJOS * TAMAÑO_POR_HIJO

mm = mmap.mmap(-1, TAMAÑO_TOTAL)

hijos = []
for i in range(NUM_HIJOS):
    pid = os.fork()
    if pid == 0:
        # Hijo: escribe en su región
        offset = i * TAMAÑO_POR_HIJO

        # Escribir ID del hijo
        struct.pack_into('i', mm, offset, i)

        # Escribir PID
        struct.pack_into('i', mm, offset + 4, os.getpid())

        # Escribir un mensaje
        msg = f"Hijo {i} (PID {os.getpid()})".encode()
        mm[offset+8:offset+8+len(msg)] = msg

        os._exit(0)
    else:
        hijos.append(pid)

# Padre espera a todos
for pid in hijos:
    os.waitpid(pid, 0)

# Leer resultados
print("=== Datos escritos por los hijos ===")
for i in range(NUM_HIJOS):
    offset = i * TAMAÑO_POR_HIJO
    hijo_id = struct.unpack_from('i', mm, offset)[0]
    hijo_pid = struct.unpack_from('i', mm, offset + 4)[0]
    msg = bytes(mm[offset+8:offset+TAMAÑO_POR_HIJO]).rstrip(b'\x00').decode()
    print(f"  Región {i}: id={hijo_id}, pid={hijo_pid}, msg='{msg}'")

mm.close()
```

**Tarea:** Modificá el ejercicio 3.2 para que cada hijo calcule la suma de un rango de números (por ejemplo, hijo 0 suma 1-25, hijo 1 suma 26-50, etc.) y escriba el resultado en su región. El padre lee todos los resultados parciales y calcula la suma total.

---

## Ejercicio 4: mmap entre procesos con multiprocessing

### 4.1 Usando mmap con multiprocessing.Process

```python
#!/usr/bin/env python3
"""mmap compartido con multiprocessing.Process."""
import mmap
import struct
from multiprocessing import Process
import os

def worker(mm_fileno, offset, datos):
    """Worker que escribe datos en el mmap compartido."""
    # Nota: no podemos pasar el objeto mmap directamente,
    # pero con fork el hijo hereda el mmap del padre
    pass

# Con fork, los hijos heredan el mmap automáticamente
# Pero es más limpio usar una variable global o compartida

# Enfoque con archivo compartido:
ARCHIVO = "/tmp/mmap_mp.bin"
TAMAÑO = 256

with open(ARCHIVO, "wb") as f:
    f.write(b'\x00' * TAMAÑO)

def escribir_en_mmap(archivo, offset, mensaje):
    """Cada proceso abre el archivo y escribe."""
    with open(archivo, "r+b") as f:
        mm = mmap.mmap(f.fileno(), TAMAÑO)
        encoded = mensaje.encode()
        struct.pack_into('i', mm, offset, len(encoded))
        mm[offset+4:offset+4+len(encoded)] = encoded
        mm.close()

procesos = []
mensajes = [
    "Hola desde proceso 0",
    "Saludos del proceso 1",
    "Proceso 2 presente",
    "Proceso 3 reportando",
]

for i, msg in enumerate(mensajes):
    p = Process(target=escribir_en_mmap, args=(ARCHIVO, i * 64, msg))
    p.start()
    procesos.append(p)

for p in procesos:
    p.join()

# Leer resultados
with open(ARCHIVO, "r+b") as f:
    mm = mmap.mmap(f.fileno(), TAMAÑO)
    print("=== Mensajes de los procesos ===")
    for i in range(4):
        offset = i * 64
        largo = struct.unpack_from('i', mm, offset)[0]
        if largo > 0:
            msg = bytes(mm[offset+4:offset+4+largo]).decode()
            print(f"  Proceso {i}: {msg}")
    mm.close()

os.unlink(ARCHIVO)
```

---

## Ejercicio 5: Value y Array compartidos (Obligatorio)

### 5.1 Contador compartido - observando la race condition

```python
#!/usr/bin/env python3
"""
Demostración de race condition con Value.
Ejecutalo varias veces y observá cómo cambia el resultado.
"""
from multiprocessing import Process, Value
import time

def incrementar(contador, n, nombre):
    """Incrementa el contador n veces."""
    print(f"[{nombre}] Iniciando {n} incrementos...")
    for _ in range(n):
        contador.value += 1
    print(f"[{nombre}] Terminado")

# Crear valor compartido
contador = Value('i', 0)

# Lanzar 4 procesos que incrementan
N = 100000
procesos = []
for i in range(4):
    p = Process(target=incrementar, args=(contador, N, f"P{i}"))
    p.start()
    procesos.append(p)

for p in procesos:
    p.join()

esperado = 4 * N
print(f"\nEsperado: {esperado}")
print(f"Obtenido: {contador.value}")
print(f"Diferencia: {esperado - contador.value} (incrementos perdidos)")
```

### 5.2 Array compartido para cálculo paralelo

```python
#!/usr/bin/env python3
"""Cálculo paralelo usando Array compartido."""
from multiprocessing import Process, Array
import math
import time

def calcular_rango(resultado, inicio, fin):
    """Calcula el cuadrado de cada número en el rango."""
    for i in range(inicio, fin):
        resultado[i] = i * i

# Array compartido de 1000 enteros
TAMAÑO = 1000
resultado = Array('i', TAMAÑO)

# Dividir en 4 procesos
NUM_PROCESOS = 4
chunk = TAMAÑO // NUM_PROCESOS

inicio = time.time()

procesos = []
for i in range(NUM_PROCESOS):
    ini = i * chunk
    fin = (i + 1) * chunk if i < NUM_PROCESOS - 1 else TAMAÑO
    p = Process(target=calcular_rango, args=(resultado, ini, fin))
    p.start()
    procesos.append(p)

for p in procesos:
    p.join()

duracion = time.time() - inicio

# Verificar
print(f"Cálculo completado en {duracion:.4f}s")
print(f"resultado[0] = {resultado[0]}")    # 0
print(f"resultado[10] = {resultado[10]}")  # 100
print(f"resultado[99] = {resultado[99]}")  # 9801
print(f"resultado[999] = {resultado[999]}")  # 998001

# Verificar que todos son correctos
errores = sum(1 for i in range(TAMAÑO) if resultado[i] != i * i)
print(f"Errores: {errores}")
```

**Tarea:** Creá un programa que:
1. Tenga un `Array('d', 100)` compartido (doubles).
2. Lance 4 procesos que calculen `math.sin(i * 0.01)` para su porción del array.
3. El padre espere a todos y muestre los primeros 20 resultados.
4. Bonus: usá un `Value('d', 0.0)` para que cada proceso acumule la suma de sus resultados. Observá si el total es correcto o si hay race condition.

---

## Ejercicio 6: SharedMemory y ShareableList

### 6.1 SharedMemory básico

```python
#!/usr/bin/env python3
"""Compartir datos con SharedMemory entre procesos."""
from multiprocessing import Process, shared_memory
import struct

def productor(shm_name, num_valores):
    """Produce valores en la memoria compartida."""
    shm = shared_memory.SharedMemory(name=shm_name)

    for i in range(num_valores):
        struct.pack_into('i', shm.buf, i * 4, i * i)

    # Marcar como listo (último byte)
    shm.buf[-1] = 1

    print(f"[PRODUCTOR] Escribí {num_valores} valores")
    shm.close()

def consumidor(shm_name, num_valores):
    """Lee valores de la memoria compartida."""
    shm = shared_memory.SharedMemory(name=shm_name)

    # Esperar a que el productor termine (polling simple)
    import time
    while shm.buf[-1] != 1:
        time.sleep(0.01)

    valores = []
    for i in range(num_valores):
        val = struct.unpack_from('i', shm.buf, i * 4)[0]
        valores.append(val)

    print(f"[CONSUMIDOR] Leí: {valores}")
    shm.close()

# Crear memoria compartida
NUM = 10
shm = shared_memory.SharedMemory(create=True, size=NUM * 4 + 1)

p_prod = Process(target=productor, args=(shm.name, NUM))
p_cons = Process(target=consumidor, args=(shm.name, NUM))

p_cons.start()
p_prod.start()

p_prod.join()
p_cons.join()

shm.close()
shm.unlink()
```

### 6.2 ShareableList para datos mixtos

```python
#!/usr/bin/env python3
"""ShareableList para compartir datos de distintos tipos."""
from multiprocessing import Process, shared_memory

def actualizar_datos(nombre_shm):
    """Actualiza datos en la lista compartida."""
    sl = shared_memory.ShareableList(name=nombre_shm)

    # Modificar valores
    sl[0] = 42              # int
    sl[1] = 3.14159         # float
    sl[2] = "actualizado"   # str (máx largo del original)
    sl[3] = False           # bool

    print(f"[WORKER] Lista actualizada: {list(sl)}")
    sl.shm.close()

# Crear lista compartida con valores iniciales
# OJO: el tipo y tamaño máximo de cada elemento se fija en la creación
sl = shared_memory.ShareableList(
    [0, 0.0, "          ", True],  # Espacios para reservar lugar para strings
    name="mi_lista_comp"
)

print(f"Antes:   {list(sl)}")

p = Process(target=actualizar_datos, args=(sl.shm.name,))
p.start()
p.join()

print(f"Después: {list(sl)}")

sl.shm.close()
sl.shm.unlink()
```

---

## Ejercicio de síntesis: procesamiento paralelo con memoria compartida

### Objetivo

Crear un programa donde múltiples procesos trabajen sobre datos compartidos: un "banco" con cuentas cuyos saldos se almacenan en memoria compartida.

```python
#!/usr/bin/env python3
"""
Banco con cuentas en memoria compartida.
Múltiples procesos realizan transferencias.

NOTA: Este ejercicio intencionalmente NO usa sincronización
para que puedas observar las race conditions.
"""
from multiprocessing import Process, Array, Value
import random
import time

NUM_CUENTAS = 5
SALDO_INICIAL = 1000
NUM_PROCESOS = 3
TRANSFERENCIAS_POR_PROCESO = 100

def mostrar_saldos(cuentas, etiqueta):
    """Muestra los saldos de todas las cuentas."""
    saldos = [cuentas[i] for i in range(NUM_CUENTAS)]
    total = sum(saldos)
    print(f"[{etiqueta}] Saldos: {saldos} | Total: {total}")

def cajero(cuentas, cajero_id, num_transferencias):
    """Un cajero que realiza transferencias entre cuentas."""
    for _ in range(num_transferencias):
        # Elegir dos cuentas diferentes al azar
        origen = random.randint(0, NUM_CUENTAS - 1)
        destino = random.randint(0, NUM_CUENTAS - 1)
        while destino == origen:
            destino = random.randint(0, NUM_CUENTAS - 1)

        # Transferir un monto aleatorio
        monto = random.randint(1, 50)

        if cuentas[origen] >= monto:
            # Estas dos operaciones NO son atómicas
            cuentas[origen] -= monto
            cuentas[destino] += monto

    print(f"[Cajero {cajero_id}] Completó {num_transferencias} transferencias")

# Crear array compartido con saldos iniciales
cuentas = Array('i', [SALDO_INICIAL] * NUM_CUENTAS)

print(f"=== Banco con {NUM_CUENTAS} cuentas ===")
print(f"=== Saldo total esperado: {NUM_CUENTAS * SALDO_INICIAL} ===\n")

mostrar_saldos(cuentas, "INICIO")

# Lanzar cajeros
procesos = []
for i in range(NUM_PROCESOS):
    p = Process(target=cajero, args=(cuentas, i, TRANSFERENCIAS_POR_PROCESO))
    p.start()
    procesos.append(p)

for p in procesos:
    p.join()

mostrar_saldos(cuentas, "FINAL")

# Verificar integridad
total_final = sum(cuentas[i] for i in range(NUM_CUENTAS))
total_esperado = NUM_CUENTAS * SALDO_INICIAL

if total_final != total_esperado:
    print(f"\n¡ERROR! Se perdieron ${total_esperado - total_final}")
    print("Esto es una race condition - se necesita sincronización")
else:
    print(f"\nTodo correcto (pero fue suerte - ejecutalo varias veces)")
```

### Tareas sobre el ejercicio de síntesis

1. **Ejecutalo varias veces.** Observá si el total de dinero se conserva o se pierde/gana dinero mágicamente.

2. **Aumentá `TRANSFERENCIAS_POR_PROCESO` a 10000.** ¿Se nota más la race condition?

3. **Agregá un log:** modificá la función `cajero` para que escriba cada transferencia en una `ShareableList` o en un archivo, indicando origen, destino y monto.

4. **Pensá:** ¿Cómo resolverías la race condition? (No hace falta implementarlo, lo veremos en clases futuras.)

---

## Verificación del ejercicio obligatorio

### Ejercicio 5: Value y Array compartidos

Tu implementación debe:

- [ ] Crear un `Value` compartido y demostrar la race condition
- [ ] Crear un `Array` compartido y dividir el trabajo entre procesos
- [ ] Verificar los resultados y reportar errores
- [ ] Mostrar la diferencia entre el valor esperado y el obtenido

---

## Ejercicios adicionales

### mmap como caché de disco

Implementá un programa que lea un archivo grande (generá uno de al menos 10 MB con datos aleatorios) usando mmap y comparalo con lectura secuencial normal. Medí el tiempo de cada enfoque.

### Chat simple con SharedMemory

Implementá un "chat" primitivo entre dos procesos usando SharedMemory. Cada proceso tiene un turno para escribir un mensaje que el otro lee. Usá un byte como flag de "hay mensaje nuevo".

### Monitor de temperatura

Simulá un sistema de sensores: N procesos "sensores" escriben temperaturas en un Array compartido, y un proceso "monitor" lee periódicamente y muestra el promedio, máximo y mínimo.

---

*Computación II - 2026 - Clase 6*
