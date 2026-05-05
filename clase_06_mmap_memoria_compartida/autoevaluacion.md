# Clase 6: mmap y Memoria Compartida - Autoevaluación

Respondé estas preguntas para verificar tu comprensión. Las respuestas están al final.

---

## Parte 1: Conceptos de memoria compartida (4 preguntas)

### Pregunta 1
¿Cuál es la principal ventaja de la memoria compartida frente a pipes/colas?

a) Es más fácil de programar
b) Incluye sincronización automática
c) Elimina las copias de datos entre procesos
d) Funciona entre máquinas diferentes

### Pregunta 2
¿Cuántas copias de datos se realizan al enviar información por un pipe?

a) 0
b) 1
c) 2 (al kernel y del kernel)
d) 3

### Pregunta 3
¿Cuál es el principal riesgo de usar memoria compartida sin sincronización?

a) Memory leaks
b) Race conditions
c) Deadlocks
d) Overflow de memoria

### Pregunta 4
¿Cuándo conviene usar memoria compartida en lugar de pipes?

a) Siempre, es superior en todo sentido
b) Cuando se comparten grandes volúmenes de datos y se necesita velocidad
c) Cuando los procesos están en diferentes máquinas
d) Cuando se necesita comunicación secuencial simple

---

## Parte 2: mmap (4 preguntas)

### Pregunta 5
¿Qué significa `mmap.mmap(-1, 1024)`?

a) Mapear el archivo -1 con tamaño 1024
b) Crear un mmap anónimo de 1024 bytes (sin archivo)
c) Error, -1 no es un file descriptor válido
d) Mapear los últimos 1024 bytes de un archivo

### Pregunta 6
¿Qué modo de acceso usás si querés modificar el mmap sin que los cambios se reflejen en el archivo?

a) `ACCESS_READ`
b) `ACCESS_WRITE`
c) `ACCESS_COPY`
d) `ACCESS_PRIVATE`

### Pregunta 7
¿Qué pasa si intentás mapear un archivo vacío con `mmap.mmap(f.fileno(), 0)`?

a) Se crea un mmap de tamaño 0
b) Se expande automáticamente el archivo
c) Se produce un error (ValueError o similar)
d) Se mapea 1 página por defecto

### Pregunta 8
¿Cómo se comparte un mmap anónimo entre padre e hijo?

a) Usando un nombre compartido
b) Se hereda automáticamente a través de `fork()`
c) Pasándolo como argumento a Process()
d) Escribiéndolo en un archivo temporal

---

## Parte 3: Value y Array (4 preguntas)

### Pregunta 9
¿Qué crea `Value('i', 0)`?

a) Una variable local con valor 0
b) Un entero compartido entre procesos, inicializado en 0
c) Un array de enteros de tamaño 0
d) Un pipe con buffer de tamaño 0

### Pregunta 10
¿Qué código de tipo usás para un float de doble precisión en Value/Array?

a) `'f'`
b) `'d'`
c) `'float'`
d) `'F'`

### Pregunta 11
En el siguiente código, ¿cuál es el problema?

```python
from multiprocessing import Process, Value

def incrementar(v, n):
    for _ in range(n):
        v.value += 1

v = Value('i', 0)
p1 = Process(target=incrementar, args=(v, 100000))
p2 = Process(target=incrementar, args=(v, 100000))
p1.start(); p2.start()
p1.join(); p2.join()
print(v.value)
```

a) No se puede pasar Value a un Process
b) `v.value += 1` no es atómico, hay race condition
c) Value no soporta el tipo 'i'
d) Falta llamar a v.close()

### Pregunta 12
¿Cómo inicializás un `Array` de 5 enteros con valores específicos?

a) `Array('i', size=5, init=[1,2,3,4,5])`
b) `Array('i', [1, 2, 3, 4, 5])`
c) `Array(int, 1, 2, 3, 4, 5)`
d) `Array('i', 5, values=[1,2,3,4,5])`

---

## Parte 4: SharedMemory (3 preguntas)

### Pregunta 13
¿Cuál es la diferencia entre `close()` y `unlink()` en SharedMemory?

a) Son sinónimos
b) `close()` desconecta al proceso, `unlink()` elimina la memoria del sistema
c) `close()` elimina la memoria, `unlink()` desconecta al proceso
d) `close()` es para el productor, `unlink()` para el consumidor

### Pregunta 14
¿Cómo se conecta un proceso a una SharedMemory existente?

a) `SharedMemory(create=True, name="nombre")`
b) `SharedMemory(name="nombre")` (sin create=True)
c) `SharedMemory.connect("nombre")`
d) `SharedMemory(attach="nombre")`

### Pregunta 15
¿Qué limitación tiene `ShareableList`?

a) Solo puede contener enteros
b) Su tamaño y tipos se fijan en la creación
c) No se puede compartir entre procesos
d) Requiere un archivo en disco

---

## Respuestas

<details>
<summary>Click para ver respuestas</summary>

### Parte 1: Conceptos de memoria compartida
1. **c** - Elimina las copias de datos entre procesos. Los procesos acceden directamente a la misma región de memoria física.
2. **c** - 2 copias: del proceso escritor al buffer del kernel, y del buffer del kernel al proceso lector.
3. **b** - Race conditions. Sin sincronización, múltiples procesos pueden leer/escribir simultáneamente y producir resultados inconsistentes.
4. **b** - Cuando se comparten grandes volúmenes de datos y se necesita velocidad. Para datos pequeños o comunicación simple, pipes/colas son más prácticos.

### Parte 2: mmap
5. **b** - Crear un mmap anónimo de 1024 bytes. El `-1` como file descriptor indica que no hay archivo asociado.
6. **c** - `ACCESS_COPY`. Crea una copia privada donde los cambios no se propagan al archivo original.
7. **c** - Se produce un error. No se puede mapear un archivo vacío; hay que darle tamaño antes de mapearlo.
8. **b** - Se hereda automáticamente a través de `fork()`. El hijo recibe una copia del mapping del padre, apuntando a la misma memoria física.

### Parte 3: Value y Array
9. **b** - Un entero compartido entre procesos, inicializado en 0. Internamente usa memoria compartida.
10. **b** - `'d'` (double). El código `'f'` es para float de simple precisión.
11. **b** - `v.value += 1` no es atómico. Internamente hace: leer, sumar, escribir. Otro proceso puede interferir entre esos pasos.
12. **b** - `Array('i', [1, 2, 3, 4, 5])`. Se pasa el código de tipo y una lista con los valores iniciales.

### Parte 4: SharedMemory
13. **b** - `close()` desconecta al proceso de la memoria compartida (pero sigue existiendo), `unlink()` elimina el bloque de memoria del sistema operativo.
14. **b** - `SharedMemory(name="nombre")` sin `create=True`. Esto se conecta a un bloque existente en lugar de crear uno nuevo.
15. **b** - Su tamaño y tipos se fijan en la creación. No se pueden agregar ni quitar elementos, y los strings no pueden exceder el largo del valor original.

### Puntuación
- 14-15: Excelente dominio de mmap y memoria compartida
- 11-13: Buen nivel
- 8-10: Necesitás repasar algunos conceptos
- <8: Revisá el material nuevamente

</details>

---

*Computación II - 2026 - Clase 6*
