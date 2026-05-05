# Clase 6: mmap y Memoria Compartida - Extra Manijas

Material opcional para profundizar.

---

## mmap para archivos grandes

### El problema de los archivos enormes

Imaginá que tenés un archivo de log de 10 GB y necesitás buscar un patrón. Si lo leés con `read()`, necesitás 10 GB de RAM (o ir leyendo de a pedazos). Con mmap, el kernel mapea el archivo a tu espacio de direcciones pero solo carga en RAM las páginas que realmente accedés.

```python
import mmap
import os
import time

def buscar_con_read(archivo, patron):
    """Búsqueda tradicional leyendo el archivo."""
    with open(archivo, "rb") as f:
        chunk_size = 1024 * 1024  # 1 MB
        posiciones = []
        offset = 0
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            pos = 0
            while True:
                pos = chunk.find(patron, pos)
                if pos == -1:
                    break
                posiciones.append(offset + pos)
                pos += 1
            offset += len(chunk)
    return posiciones

def buscar_con_mmap(archivo, patron):
    """Búsqueda con mmap."""
    with open(archivo, "rb") as f:
        mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
        posiciones = []
        pos = 0
        while True:
            pos = mm.find(patron, pos)
            if pos == -1:
                break
            posiciones.append(pos)
            pos += 1
        mm.close()
    return posiciones

# Generar archivo de prueba (100 MB)
ARCHIVO = "/tmp/archivo_grande.bin"
TAMAÑO = 100 * 1024 * 1024

if not os.path.exists(ARCHIVO):
    print("Generando archivo de prueba de 100 MB...")
    with open(ARCHIVO, "wb") as f:
        import random
        for i in range(TAMAÑO // 1024):
            datos = os.urandom(1024)
            f.write(datos)
            # Insertar patron cada ~10 MB
            if i % (10 * 1024) == 0:
                f.write(b"PATRON_BUSCADO")

patron = b"PATRON_BUSCADO"

# Comparar
inicio = time.time()
r1 = buscar_con_read(ARCHIVO, patron)
t_read = time.time() - inicio

inicio = time.time()
r2 = buscar_con_mmap(ARCHIVO, patron)
t_mmap = time.time() - inicio

print(f"read(): {len(r1)} ocurrencias en {t_read:.3f}s")
print(f"mmap(): {len(r2)} ocurrencias en {t_mmap:.3f}s")
print(f"Speedup: {t_read/t_mmap:.1f}x")

os.unlink(ARCHIVO)
```

### Ventajas de mmap para archivos grandes

1. **Paginación bajo demanda:** Solo se cargan las páginas que tocás. Un archivo de 10 GB puede mapearse sin usar 10 GB de RAM.
2. **Caché del kernel:** Las páginas mapeadas usan el page cache del kernel. Si otro proceso lee el mismo archivo, comparte las mismas páginas físicas.
3. **Acceso aleatorio eficiente:** Saltar a cualquier posición es O(1), sin necesidad de `seek()` + `read()`.
4. **Sin doble buffering:** Con `read()`, los datos pasan del page cache al buffer de userspace. Con mmap, accedés directamente al page cache.

### Procesamiento de archivo grande por regiones

Para archivos que no caben en el espacio de direcciones (32 bits), podés mapear por regiones:

```python
import mmap
import os

def procesar_por_regiones(archivo, tamaño_region=64*1024*1024):
    """Procesar archivo grande mapeando regiones de 64 MB."""
    tamaño_archivo = os.path.getsize(archivo)

    with open(archivo, "r+b") as f:
        offset = 0
        while offset < tamaño_archivo:
            # Calcular tamaño de esta región
            region = min(tamaño_region, tamaño_archivo - offset)

            # Mapear región (offset debe ser múltiplo del tamaño de página)
            mm = mmap.mmap(f.fileno(), region, offset=offset)

            # Procesar...
            # Por ejemplo, contar líneas:
            count = mm[:].count(b'\n')
            print(f"Región {offset//tamaño_region}: {count} líneas")

            mm.close()
            offset += region
```

---

## /dev/shm: memoria compartida en el filesystem

Linux expone la memoria compartida POSIX a través del filesystem `/dev/shm`. Es un tmpfs (filesystem en RAM) donde cada archivo es un segmento de memoria compartida.

### Explorando /dev/shm

```bash
# Ver qué hay en /dev/shm
ls -la /dev/shm/

# Ver cuánta memoria se está usando
df -h /dev/shm/

# Los SharedMemory de Python aparecen acá
python3 -c "
from multiprocessing import shared_memory
shm = shared_memory.SharedMemory(create=True, size=1024, name='test_shm')
print(f'Creado: {shm.name}')
import subprocess
subprocess.run(['ls', '-la', '/dev/shm/'])
shm.close()
shm.unlink()
"
```

### Usar archivos en /dev/shm directamente

Podés crear memoria compartida simplemente escribiendo archivos en `/dev/shm`:

```python
import mmap
import os

# Crear "memoria compartida" como archivo en /dev/shm
ARCHIVO = "/dev/shm/mi_memoria"
TAMAÑO = 4096

with open(ARCHIVO, "wb") as f:
    f.write(b'\x00' * TAMAÑO)

# Ahora cualquier proceso puede mapearlo
with open(ARCHIVO, "r+b") as f:
    mm = mmap.mmap(f.fileno(), TAMAÑO)

    mm[0:13] = b"Hola, /dev/shm"
    mm.flush()
    mm.close()

# Verificar que está en RAM (no en disco)
# /dev/shm es un tmpfs montado en RAM
print(f"Archivo existe: {os.path.exists(ARCHIVO)}")

# Limpiar
os.unlink(ARCHIVO)
```

### Ventajas de /dev/shm

- **Velocidad:** Es RAM pura, no hay I/O a disco
- **Visible:** Podés ver los segmentos compartidos con `ls`
- **Compatible:** Funciona con cualquier herramienta que opere sobre archivos
- **Límite configurable:** Por defecto es 50% de la RAM, ajustable con `mount -o remount,size=2G /dev/shm`

---

## Comparación de rendimiento: mmap vs pipes vs queues

### Benchmark completo

```python
#!/usr/bin/env python3
"""Benchmark: mmap vs pipe vs Queue para transferir datos."""
import mmap
import os
import time
import struct
from multiprocessing import Process, Queue, Pipe, shared_memory

TAMAÑO_DATOS = 1_000_000  # 1 millón de enteros
DATOS = list(range(TAMAÑO_DATOS))

def bench_queue():
    """Transferir datos via Queue."""
    q = Queue()

    def productor(q, datos):
        for d in datos:
            q.put(d)
        q.put(None)  # Sentinel

    def consumidor(q):
        while True:
            d = q.get()
            if d is None:
                break

    inicio = time.time()
    p = Process(target=productor, args=(q, DATOS))
    c = Process(target=consumidor, args=(q,))
    p.start()
    c.start()
    p.join()
    c.join()
    return time.time() - inicio

def bench_pipe():
    """Transferir datos via Pipe."""
    parent_conn, child_conn = Pipe()

    def productor(conn, datos):
        # Enviar en bloques para eficiencia
        chunk = 10000
        for i in range(0, len(datos), chunk):
            conn.send(datos[i:i+chunk])
        conn.send(None)
        conn.close()

    def consumidor(conn):
        while True:
            d = conn.recv()
            if d is None:
                break
        conn.close()

    inicio = time.time()
    p = Process(target=productor, args=(child_conn, DATOS))
    c = Process(target=consumidor, args=(parent_conn,))
    p.start()
    c.start()
    p.join()
    c.join()
    return time.time() - inicio

def bench_shm():
    """Transferir datos via SharedMemory."""
    tamaño = TAMAÑO_DATOS * 4 + 4  # enteros + flag

    shm = shared_memory.SharedMemory(create=True, size=tamaño)

    def productor(nombre, datos):
        shm_p = shared_memory.SharedMemory(name=nombre)
        for i, d in enumerate(datos):
            struct.pack_into('i', shm_p.buf, i * 4, d)
        # Marcar como listo
        struct.pack_into('i', shm_p.buf, len(datos) * 4, 1)
        shm_p.close()

    def consumidor(nombre, n):
        shm_c = shared_memory.SharedMemory(name=nombre)
        # Esperar
        while struct.unpack_from('i', shm_c.buf, n * 4)[0] != 1:
            pass
        # Leer
        for i in range(n):
            _ = struct.unpack_from('i', shm_c.buf, i * 4)[0]
        shm_c.close()

    inicio = time.time()
    p = Process(target=productor, args=(shm.name, DATOS))
    c = Process(target=consumidor, args=(shm.name, TAMAÑO_DATOS))
    p.start()
    c.start()
    p.join()
    c.join()
    t = time.time() - inicio

    shm.close()
    shm.unlink()
    return t

# Ejecutar benchmarks
print(f"Transfiriendo {TAMAÑO_DATOS:,} enteros entre procesos\n")

t_queue = bench_queue()
print(f"Queue:          {t_queue:.3f}s")

t_pipe = bench_pipe()
print(f"Pipe (chunks):  {t_pipe:.3f}s")

t_shm = bench_shm()
print(f"SharedMemory:   {t_shm:.3f}s")

print(f"\nSpeedup shm vs queue: {t_queue/t_shm:.1f}x")
print(f"Speedup shm vs pipe:  {t_pipe/t_shm:.1f}x")
```

Los resultados típicos muestran que SharedMemory es significativamente más rápido para grandes volúmenes de datos, especialmente cuando no hay serialización involucrada.

---

## mmap en C: la syscall original

Python's `mmap` es un wrapper sobre la syscall `mmap(2)` de POSIX. Entender la versión C ayuda a comprender qué hace Python por debajo.

### mmap en C

```c
#include <stdio.h>
#include <stdlib.h>
#include <sys/mman.h>
#include <sys/wait.h>
#include <unistd.h>
#include <string.h>

int main() {
    // Crear mmap anónimo compartido
    // MAP_SHARED: cambios visibles entre procesos
    // MAP_ANONYMOUS: sin archivo
    int *memoria = mmap(
        NULL,                    // Dirección (NULL = el kernel elige)
        sizeof(int),             // Tamaño
        PROT_READ | PROT_WRITE,  // Permisos
        MAP_SHARED | MAP_ANONYMOUS,  // Flags
        -1,                      // File descriptor (-1 para anónimo)
        0                        // Offset
    );

    if (memoria == MAP_FAILED) {
        perror("mmap");
        exit(1);
    }

    *memoria = 0;

    pid_t pid = fork();
    if (pid == 0) {
        // Hijo incrementa
        for (int i = 0; i < 100000; i++) {
            (*memoria)++;  // Race condition!
        }
        _exit(0);
    }

    // Padre también incrementa
    for (int i = 0; i < 100000; i++) {
        (*memoria)++;
    }

    wait(NULL);
    printf("Valor final: %d (esperado: 200000)\n", *memoria);

    munmap(memoria, sizeof(int));
    return 0;
}
```

### Compilar y ejecutar

```bash
gcc -o mmap_demo mmap_demo.c
./mmap_demo
# Valor final: probablemente menor que 200000 (race condition)
```

### Correspondencia Python-C

| Python | C | Descripción |
|--------|---|-------------|
| `mmap.mmap(-1, size)` | `mmap(NULL, size, PROT_READ\|PROT_WRITE, MAP_SHARED\|MAP_ANONYMOUS, -1, 0)` | mmap anónimo |
| `mmap.mmap(fd, size)` | `mmap(NULL, size, PROT_READ\|PROT_WRITE, MAP_SHARED, fd, 0)` | mmap sobre archivo |
| `mm.close()` | `munmap(addr, size)` | Desmapear |
| `mm.flush()` | `msync(addr, size, MS_SYNC)` | Sincronizar a disco |
| `ACCESS_READ` | `PROT_READ` | Solo lectura |
| `ACCESS_WRITE` | `PROT_READ \| PROT_WRITE` | Lectura/escritura |
| `ACCESS_COPY` | `MAP_PRIVATE` | Copia privada |

### POSIX shared memory en C

```c
#include <stdio.h>
#include <stdlib.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>
#include <string.h>

int main() {
    const char *nombre = "/mi_shm";
    int tamaño = 4096;

    // Crear segmento de memoria compartida
    int fd = shm_open(nombre, O_CREAT | O_RDWR, 0666);
    ftruncate(fd, tamaño);

    // Mapear
    char *ptr = mmap(NULL, tamaño, PROT_READ | PROT_WRITE,
                     MAP_SHARED, fd, 0);

    // Escribir
    strcpy(ptr, "Hola desde C!");
    printf("Escrito: %s\n", ptr);

    // Limpiar
    munmap(ptr, tamaño);
    close(fd);
    shm_unlink(nombre);

    return 0;
}
```

```bash
# Compilar (necesita -lrt para shm_open)
gcc -o shm_demo shm_demo.c -lrt
./shm_demo
```

---

## Memory-mapped I/O para bases de datos

Muchas bases de datos usan mmap internamente. Es una técnica fundamental para acceder a archivos de datos de forma eficiente.

### Concepto: base de datos simple con mmap

```python
#!/usr/bin/env python3
"""
Mini base de datos basada en mmap.
Almacena registros de tamaño fijo en un archivo mapeado.
"""
import mmap
import struct
import os

class MmapDB:
    """Base de datos simple con registros de tamaño fijo."""

    # Formato: ID (int) + Nombre (32 bytes) + Edad (int) + Activo (bool/byte)
    FORMATO = 'i 32s i b'
    TAMAÑO_REGISTRO = struct.calcsize(FORMATO)
    HEADER_SIZE = 8  # Almacena cantidad de registros

    def __init__(self, archivo, max_registros=1000):
        self.archivo = archivo
        self.max_registros = max_registros
        self.tamaño = self.HEADER_SIZE + max_registros * self.TAMAÑO_REGISTRO

        # Crear archivo si no existe
        if not os.path.exists(archivo):
            with open(archivo, 'wb') as f:
                f.write(b'\x00' * self.tamaño)

        self.f = open(archivo, 'r+b')
        self.mm = mmap.mmap(self.f.fileno(), self.tamaño)

    def _get_count(self):
        return struct.unpack_from('q', self.mm, 0)[0]

    def _set_count(self, n):
        struct.pack_into('q', self.mm, 0, n)

    def insertar(self, id, nombre, edad, activo=True):
        count = self._get_count()
        if count >= self.max_registros:
            raise Exception("Base llena")

        offset = self.HEADER_SIZE + count * self.TAMAÑO_REGISTRO
        nombre_bytes = nombre.encode('utf-8')[:32].ljust(32, b'\x00')
        struct.pack_into(self.FORMATO, self.mm, offset,
                        id, nombre_bytes, edad, int(activo))

        self._set_count(count + 1)
        self.mm.flush()

    def leer(self, indice):
        count = self._get_count()
        if indice >= count:
            return None

        offset = self.HEADER_SIZE + indice * self.TAMAÑO_REGISTRO
        id, nombre, edad, activo = struct.unpack_from(
            self.FORMATO, self.mm, offset)
        return {
            'id': id,
            'nombre': nombre.rstrip(b'\x00').decode('utf-8'),
            'edad': edad,
            'activo': bool(activo)
        }

    def buscar(self, campo, valor):
        """Búsqueda lineal (simple pero funcional)."""
        resultados = []
        count = self._get_count()
        for i in range(count):
            reg = self.leer(i)
            if reg and reg[campo] == valor:
                resultados.append(reg)
        return resultados

    def count(self):
        return self._get_count()

    def cerrar(self):
        self.mm.close()
        self.f.close()

# Uso
db = MmapDB("/tmp/mini_db.dat")

db.insertar(1, "Ana García", 22)
db.insertar(2, "Carlos López", 25)
db.insertar(3, "María Pérez", 22)
db.insertar(4, "Juan Martín", 30)

print(f"Total registros: {db.count()}")

for i in range(db.count()):
    print(f"  {db.leer(i)}")

print(f"\nBúsqueda edad=22: {db.buscar('edad', 22)}")

db.cerrar()
os.unlink("/tmp/mini_db.dat")
```

### Bases de datos reales que usan mmap

- **SQLite:** Tiene un modo WAL con mmap para lecturas rápidas
- **LMDB (Lightning Memory-Mapped Database):** Toda la base es un archivo mmap'd. Extremadamente rápida para lecturas
- **MongoDB (WiredTiger):** Usa mmap para el storage engine
- **Redis (snapshots):** Los archivos RDB se pueden cargar con mmap

### Ventajas de mmap para bases de datos

1. **El kernel maneja el caché:** No necesitás implementar tu propio buffer pool
2. **Lectura sin copias:** Los datos van directo del page cache al proceso
3. **Persistencia automática:** El kernel se encarga de escribir a disco
4. **Compartir entre conexiones:** Múltiples procesos pueden mapear el mismo archivo

### Limitaciones

1. **No controlás cuándo se escribe a disco:** El kernel decide cuándo flush
2. **I/O errors se convierten en SIGBUS:** Si el disco falla, tu proceso recibe una señal
3. **Tamaño limitado en 32 bits:** Solo podés mapear ~3 GB en un proceso de 32 bits
4. **No apto para archivos en red:** mmap sobre NFS puede causar problemas

---

## Recursos adicionales

- [mmap(2) man page](https://man7.org/linux/man-pages/man2/mmap.2.html) - Documentación de la syscall
- [shm_overview(7)](https://man7.org/linux/man-pages/man7/shm_overview.7.html) - Overview de POSIX shared memory
- [Python mmap docs](https://docs.python.org/3/library/multiprocessing.shared_memory.html) - Documentación de shared_memory
- [Are You Sure You Want to Use MMAP in Your Database Management System?](https://db.cs.cmu.edu/papers/2022/cidr2022-p13-crotty.pdf) - Paper de CMU sobre tradeoffs de mmap en DBMS

---

*Computación II - 2026 - Clase 6 - Material opcional*
