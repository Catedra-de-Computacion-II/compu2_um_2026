# Python Avanzado para Programación de Sistemas

## ¿Por qué necesitás esto?

Hasta ahora probablemente usaste Python para resolver problemas algorítmicos: recorrer listas, manipular strings, hacer cálculos. Eso está bien para un curso de programación básica, pero la programación de sistemas es otra cosa.

En esta materia vas a escribir código que:
- Abre archivos y conexiones de red que *tienen* que cerrarse correctamente
- Crea procesos e hilos que compiten por recursos compartidos
- Procesa streams de datos que no caben en memoria
- Maneja errores que pueden ocurrir en cualquier momento por razones fuera de tu control

Para todo eso, necesitás herramientas de Python que probablemente viste por arriba o que nunca usaste. Este repaso no es opcional: sin estas herramientas, el código que escribas en la materia va a ser frágil, ineficiente o directamente incorrecto.

No te preocupes si algunos conceptos parecen abstractos al principio. Todo va a tener sentido cuando los uses en contextos reales.

---

## Context Managers: el arte de limpiar después de vos mismo

### El problema que resuelven

Mirá este código que parece inocente:

```python
f = open("datos.txt", "r")
contenido = f.read()
f.close()
```

¿Cuál es el problema? Si `f.read()` lanza una excepción (porque el archivo está corrupto, porque se llenó el disco, porque mil razones), `f.close()` nunca se ejecuta. El archivo queda abierto.

"¿Y qué?", podrías pensar. Bueno, el sistema operativo tiene un límite de archivos abiertos simultáneamente. Si tu programa abre archivos sin cerrarlos, eventualmente alcanza ese límite y no puede abrir más. El programa falla de formas misteriosas. Esto es especialmente crítico en servidores que corren por días o semanas.

La solución obvia es usar try/finally:

```python
f = open("datos.txt", "r")
try:
    contenido = f.read()
finally:
    f.close()
```

Funciona, pero es verboso. Y peor: tenés que acordarte de hacerlo cada vez. Un solo olvido y tenés un bug que puede tardar días en manifestarse.

### La solución elegante: with

Python resuelve esto con context managers y la palabra clave `with`:

```python
with open("datos.txt", "r") as f:
    contenido = f.read()
# Acá el archivo ya está cerrado, pase lo que pase
```

Esto es más que azúcar sintáctica. Es un patrón que garantiza que los recursos se liberen correctamente, incluso si ocurre una excepción. El archivo se cierra automáticamente cuando termina el bloque `with`, sin importar cómo termine.

### ¿Por qué vas a necesitar esto constantemente?

En esta materia vas a trabajar con recursos que requieren limpieza:

- **Archivos**: obvio, pero más de lo que pensás
- **Sockets de red**: conexiones que deben cerrarse
- **Locks de sincronización**: que deben liberarse para evitar deadlocks
- **Procesos hijos**: que deben esperarse para evitar zombies
- **Conexiones a bases de datos**: que deben commitear o rollbackear

Todos estos pueden (y deberían) manejarse con context managers.

### Cómo funciona por dentro

Un objeto es un context manager si implementa dos métodos especiales: `__enter__` y `__exit__`.

Cuando escribís `with algo as variable:`, Python hace esto:

1. Llama a `algo.__enter__()`
2. Asigna lo que devuelve a `variable`
3. Ejecuta el bloque de código
4. Llama a `algo.__exit__()`, pasándole información sobre cualquier excepción que haya ocurrido

Podés crear tus propios context managers. Por ejemplo, imaginate que querés medir cuánto tarda una operación:

```python
import time

class Timer:
    def __init__(self, nombre):
        self.nombre = nombre

    def __enter__(self):
        self.inicio = time.time()
        return self  # Esto es lo que se asigna después del 'as'

    def __exit__(self, tipo_exc, valor_exc, traceback):
        duracion = time.time() - self.inicio
        print(f"{self.nombre}: {duracion:.3f} segundos")
        return False  # No suprimir excepciones

# Uso
with Timer("Procesamiento"):
    # código que querés medir
    datos = [x**2 for x in range(1000000)]
```

El método `__exit__` recibe tres argumentos sobre la excepción (si hubo alguna). Si devuelve `True`, la excepción se suprime. Casi siempre querés devolver `False` para dejar que las excepciones se propaguen.

### La forma rápida: contextlib

Escribir una clase completa para cada context manager es tedioso. El módulo `contextlib` ofrece un decorador que simplifica esto:

```python
from contextlib import contextmanager
import tempfile
import shutil

@contextmanager
def directorio_temporal():
    """Crea un directorio temporal y lo borra al terminar."""
    path = tempfile.mkdtemp()
    try:
        yield path  # Acá se ejecuta el bloque with
    finally:
        shutil.rmtree(path)

# Uso
with directorio_temporal() as tmp:
    # Trabajar con tmp...
    # Guardar archivos temporales...
    pass
# El directorio y todo su contenido ya no existen
```

El truco está en `yield`. Todo lo que está antes del `yield` es el `__enter__`. Lo que está después del `yield` (en el `finally`) es el `__exit__`.

Este patrón lo vas a usar constantemente. Cada vez que necesites "hacer algo, ejecutar código, deshacer lo que hiciste", pensá en context managers.

---

## Decoradores: modificar funciones sin tocarlas

### Las funciones son objetos

Para entender decoradores, primero tenés que internalizar algo que en otros lenguajes no es tan evidente: en Python, las funciones son objetos como cualquier otro. Podés asignarlas a variables, pasarlas como argumentos, retornarlas de otras funciones.

```python
def saludar(nombre):
    return f"Hola, {nombre}"

# Una función es solo un valor
mi_funcion = saludar
print(mi_funcion("Ana"))  # "Hola, Ana"

# Podés pasarla como argumento
def ejecutar_dos_veces(funcion, argumento):
    funcion(argumento)
    funcion(argumento)

ejecutar_dos_veces(print, "hola")  # imprime "hola" dos veces
```

### Funciones que crean funciones

Como las funciones son valores, podés tener funciones que retornan otras funciones:

```python
def crear_multiplicador(factor):
    def multiplicar(x):
        return x * factor
    return multiplicar

doble = crear_multiplicador(2)
triple = crear_multiplicador(3)

print(doble(5))   # 10
print(triple(5))  # 15
```

Fijate lo que pasa acá: `crear_multiplicador` recibe un `factor` y devuelve una nueva función. Esa función "recuerda" el factor con el que fue creada. Esto se llama **closure**, y es fundamental para muchas técnicas avanzadas.

### ¿Qué es un decorador?

Un decorador es una función que recibe una función y devuelve una versión modificada de ella. La sintaxis con `@` es solo una forma conveniente de escribirlo:

```python
def mi_decorador(funcion):
    def wrapper(*args, **kwargs):
        print("Antes de la función")
        resultado = funcion(*args, **kwargs)
        print("Después de la función")
        return resultado
    return wrapper

@mi_decorador
def saludar(nombre):
    print(f"Hola, {nombre}")

# Esto es equivalente a escribir:
# saludar = mi_decorador(saludar)

saludar("Ana")
# Imprime:
# Antes de la función
# Hola, Ana
# Después de la función
```

El decorador "envuelve" la función original. Cada vez que llamás a `saludar`, en realidad estás llamando a `wrapper`, que hace algo extra y después llama a la función original.

### ¿Para qué sirve esto en la práctica?

Los decoradores son útiles cuando querés agregar comportamiento a muchas funciones sin duplicar código. Algunos ejemplos:

**Logging automático:**

```python
from functools import wraps

def log_llamadas(funcion):
    @wraps(funcion)  # Preserva nombre y docstring
    def wrapper(*args, **kwargs):
        print(f"Llamando a {funcion.__name__} con {args}, {kwargs}")
        resultado = funcion(*args, **kwargs)
        print(f"{funcion.__name__} retornó {resultado}")
        return resultado
    return wrapper

@log_llamadas
def sumar(a, b):
    return a + b

sumar(3, 5)
# Llamando a sumar con (3, 5), {}
# sumar retornó 8
```

**Validación de argumentos:**

```python
def solo_positivos(funcion):
    @wraps(funcion)
    def wrapper(*args, **kwargs):
        for arg in args:
            if isinstance(arg, (int, float)) and arg < 0:
                raise ValueError("Solo se permiten números positivos")
        return funcion(*args, **kwargs)
    return wrapper

@solo_positivos
def raiz_cuadrada(x):
    return x ** 0.5
```

**Retry automático:**

```python
import time

def reintentar(intentos=3, delay=1):
    def decorador(funcion):
        @wraps(funcion)
        def wrapper(*args, **kwargs):
            for i in range(intentos):
                try:
                    return funcion(*args, **kwargs)
                except Exception as e:
                    if i == intentos - 1:
                        raise
                    print(f"Intento {i+1} falló, reintentando...")
                    time.sleep(delay)
        return wrapper
    return decorador

@reintentar(intentos=5, delay=2)
def conectar_servidor():
    # Código que puede fallar temporalmente
    pass
```

Fijate que este último decorador recibe argumentos. Eso requiere un nivel extra de anidamiento: una función que retorna un decorador.

### Decoradores de la biblioteca estándar

Python incluye varios decoradores muy útiles:

**`@lru_cache`**: guarda en memoria los resultados de llamadas anteriores. Ideal para funciones costosas que se llaman con los mismos argumentos:

```python
from functools import lru_cache

@lru_cache(maxsize=128)
def fibonacci(n):
    if n < 2:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

# Sin cache: fibonacci(40) tarda segundos
# Con cache: es instantáneo
```

**`@property`**: hace que un método se comporte como un atributo:

```python
class Circulo:
    def __init__(self, radio):
        self.radio = radio

    @property
    def area(self):
        import math
        return math.pi * self.radio ** 2

    @property
    def diametro(self):
        return self.radio * 2

c = Circulo(5)
print(c.area)      # Parece un atributo, pero es un método
print(c.diametro)  # No necesitás paréntesis
```

**`@staticmethod` y `@classmethod`**: métodos que no dependen de la instancia:

```python
class Utilidades:
    @staticmethod
    def es_par(n):
        return n % 2 == 0

    @classmethod
    def crear_desde_string(cls, texto):
        return cls(int(texto))
```

---

## Generadores: procesar datos infinitos con memoria finita

### El problema de las listas

Imaginate que tenés que procesar un archivo de log de 10 GB. El enfoque ingenuo sería:

```python
with open("log_enorme.txt") as f:
    lineas = f.readlines()  # Lee TODO el archivo en memoria

for linea in lineas:
    procesar(linea)
```

Tu programa explota porque intentó cargar 10 GB en RAM. Podrías leer línea por línea, pero ¿qué pasa si querés encadenar operaciones, filtrar, transformar?

O pensá en esto: querés generar todos los números primos. ¿Cuántos? No sabés, los necesitás hasta que encuentres uno que cumpla cierta condición. No podés generar "todos los primos" de antemano porque son infinitos.

### Generadores: evaluación lazy

Un generador produce valores bajo demanda, uno a la vez. No calcula nada hasta que le pedís el siguiente valor:

```python
def numeros_pares():
    n = 0
    while True:  # Loop infinito, pero está bien
        yield n
        n += 2

# Esto no ejecuta nada todavía
gen = numeros_pares()

# Ahora sí pedimos valores
print(next(gen))  # 0
print(next(gen))  # 2
print(next(gen))  # 4
```

La magia está en `yield`. Cuando una función tiene `yield`, no es una función común: es un generador. Cuando la llamás, no se ejecuta; devuelve un objeto generador. Cada vez que llamás `next()` (o iterás con `for`), la función avanza hasta el próximo `yield`, devuelve el valor, y se "pausa" ahí.

### Expresiones generadoras

Así como tenés list comprehensions, tenés generator expressions:

```python
# List comprehension: crea toda la lista en memoria
cuadrados_lista = [x**2 for x in range(1000000)]  # ~8 MB

# Generator expression: no crea nada hasta que iterás
cuadrados_gen = (x**2 for x in range(1000000))    # ~100 bytes
```

La diferencia es usar paréntesis en lugar de corchetes. El generador ocupa memoria constante sin importar cuántos elementos tenga.

### ¿Cuándo usar generadores?

**Archivos grandes**: en lugar de cargar todo en memoria:

```python
def procesar_log(archivo):
    with open(archivo) as f:
        for linea in f:  # f ya es un iterador!
            if "ERROR" in linea:
                yield linea

# Procesá un archivo de cualquier tamaño
for error in procesar_log("server.log"):
    analizar(error)
```

**Pipelines de procesamiento**: encadenando generadores:

```python
def leer_lineas(archivo):
    with open(archivo) as f:
        for linea in f:
            yield linea.strip()

def filtrar_vacias(lineas):
    for linea in lineas:
        if linea:
            yield linea

def parsear_json(lineas):
    import json
    for linea in lineas:
        yield json.loads(linea)

# Encadenamos todo
lineas = leer_lineas("datos.jsonl")
no_vacias = filtrar_vacias(lineas)
objetos = parsear_json(no_vacias)

for obj in objetos:
    procesar(obj)
```

Ningún paso carga todo en memoria. Cada elemento fluye por el pipeline uno a la vez.

**Secuencias infinitas o muy largas**:

```python
def fibonacci():
    a, b = 0, 1
    while True:
        yield a
        a, b = b, a + b

# Los primeros 20 Fibonacci
from itertools import islice
print(list(islice(fibonacci(), 20)))
```

### yield from: delegar a otro generador

A veces querés que un generador produzca valores de otro:

```python
def leer_multiples_archivos(archivos):
    for archivo in archivos:
        yield from leer_lineas(archivo)

# Equivalente a:
def leer_multiples_archivos(archivos):
    for archivo in archivos:
        for linea in leer_lineas(archivo):
            yield linea
```

`yield from` es más que azúcar sintáctica: también propaga excepciones y valores de retorno correctamente.

### send(): generadores que reciben, no solo producen

Hasta acá `yield` fue una salida: el generador produce y vos consumís. Pero `yield`
también es una **entrada**. Con `.send(valor)`, ese valor pasa a ser el resultado
de la expresión `yield` dentro del generador:

```python
def acumulador():
    """Suma lo que le vayan mandando."""
    total = 0
    while True:
        n = yield total          # produce el total, y RECIBE el próximo n
        total += n

a = acumulador()
next(a)              # arranca el generador; se detiene en el primer yield
print(a.send(10))    # 10
print(a.send(5))     # 15
print(a.send(3))     # 18
```

Fijate el detalle del `next(a)` inicial: un generador recién creado no ejecutó
nada todavía, así que hay que llevarlo hasta el primer `yield` antes de poder
mandarle algo. Si intentás `send()` de entrada, Python lanza `TypeError`.

Esto convierte al generador en algo distinto de un iterador: es una **función que
se suspende, recibe un dato del exterior y continúa donde estaba**. Es decir, una
tarea que se puede pausar y reanudar.

Y esa es exactamente la idea sobre la que está construido asyncio: cuando escribís
`resultado = await algo()`, la corrutina se suspende, alguien más la reanuda
pasándole el resultado, y sigue. `async`/`await` es azúcar sobre este mecanismo.

En la clase de asyncio vamos a construir un scheduler cooperativo usando solo
generadores y `send()`, para que quede claro que el event loop no es magia.

---

## Closures y funciones de orden superior

### Closures: funciones que recuerdan

Ya vimos un ejemplo de closure con el multiplicador. Veamos otro más útil:

```python
def crear_logger(prefijo):
    def log(mensaje):
        print(f"[{prefijo}] {mensaje}")
    return log

log_db = crear_logger("DATABASE")
log_net = crear_logger("NETWORK")

log_db("Conexión establecida")   # [DATABASE] Conexión establecida
log_net("Timeout en servidor")   # [NETWORK] Timeout en servidor
```

La función interna "recuerda" el valor de `prefijo` que tenía cuando fue creada. Cada logger tiene su propio prefijo encapsulado.

### Modificar variables capturadas

Si querés modificar (no solo leer) una variable del scope externo, necesitás `nonlocal`:

```python
def crear_contador():
    cuenta = 0

    def incrementar():
        nonlocal cuenta  # Sin esto, Python crea una variable local
        cuenta += 1
        return cuenta

    return incrementar

contador = crear_contador()
print(contador())  # 1
print(contador())  # 2
print(contador())  # 3
```

Sin `nonlocal`, Python asumiría que `cuenta` es una variable local de `incrementar` y daría error porque la estás usando antes de definirla.

### Funciones de orden superior

Son funciones que reciben o devuelven otras funciones. Las más conocidas son `map`, `filter` y `reduce`:

```python
numeros = [1, 2, 3, 4, 5]

# map: aplica una función a cada elemento
dobles = list(map(lambda x: x * 2, numeros))  # [2, 4, 6, 8, 10]

# filter: mantiene elementos que cumplen condición
pares = list(filter(lambda x: x % 2 == 0, numeros))  # [2, 4]

# reduce: acumula valores (está en functools)
from functools import reduce
suma = reduce(lambda acc, x: acc + x, numeros)  # 15
```

Generalmente las list comprehensions son más legibles:

```python
dobles = [x * 2 for x in numeros]
pares = [x for x in numeros if x % 2 == 0]
```

Pero `map` y `filter` devuelven iteradores (lazy), lo que puede ser ventajoso con datos grandes.

### partial: pre-configurar argumentos

A veces querés una versión de una función con algunos argumentos ya fijados:

```python
from functools import partial

def potencia(base, exponente):
    return base ** exponente

cuadrado = partial(potencia, exponente=2)
cubo = partial(potencia, exponente=3)

print(cuadrado(5))  # 25
print(cubo(5))      # 125
```

Esto es útil cuando tenés que pasar una función que espera cierta firma, pero la tuya tiene argumentos extra que querés fijar.

---

## Manejo de excepciones: cuando las cosas salen mal

### La estructura completa

Python tiene una estructura de manejo de excepciones bastante completa:

```python
try:
    # Código que puede fallar
    resultado = operacion_riesgosa()

except TipoEspecifico as e:
    # Manejar este tipo de error
    print(f"Error específico: {e}")

except (TipoA, TipoB) as e:
    # Manejar varios tipos
    print(f"Error A o B: {e}")

except Exception as e:
    # Cualquier otra excepción
    print(f"Error inesperado: {e}")

else:
    # Se ejecuta SOLO si no hubo excepción
    print(f"Éxito: {resultado}")

finally:
    # Se ejecuta SIEMPRE, haya o no excepción
    limpiar_recursos()
```

El bloque `else` es útil para código que solo tiene sentido si el `try` funcionó. El `finally` es para limpieza que debe ocurrir siempre (aunque generalmente es mejor usar context managers).

### Cuándo capturar qué

Un error común es capturar `Exception` sin pensar:

```python
# MAL: oculta todos los errores
try:
    algo()
except Exception:
    pass  # Silenciosamente ignora todo
```

Esto hace que los bugs sean invisibles. Solo capturá las excepciones que sabés manejar:

```python
# BIEN: maneja solo lo esperado
try:
    contenido = leer_archivo(path)
except FileNotFoundError:
    contenido = crear_contenido_default()
except PermissionError:
    print(f"No tengo permiso para leer {path}")
    raise
```

### Excepciones personalizadas

Para aplicaciones serias, creá tus propias excepciones:

```python
class ErrorDeAplicacion(Exception):
    """Clase base para errores de esta aplicación."""
    pass

class ConfiguracionInvalida(ErrorDeAplicacion):
    """La configuración proporcionada no es válida."""
    pass

class ConexionFallida(ErrorDeAplicacion):
    """No se pudo establecer conexión con el servidor."""
    def __init__(self, servidor, puerto, causa=None):
        self.servidor = servidor
        self.puerto = puerto
        self.causa = causa
        mensaje = f"No se pudo conectar a {servidor}:{puerto}"
        if causa:
            mensaje += f" ({causa})"
        super().__init__(mensaje)
```

Esto permite que el código que llama distinga entre diferentes tipos de errores:

```python
try:
    conectar()
except ConexionFallida as e:
    print(f"Problema de red con {e.servidor}")
except ConfiguracionInvalida:
    print("Revisá el archivo de configuración")
```

### Encadenar excepciones

Cuando capturás una excepción y lanzás otra, podés preservar la información original:

```python
try:
    datos = json.loads(texto)
except json.JSONDecodeError as e:
    raise ConfiguracionInvalida("El archivo no es JSON válido") from e
```

Esto produce un traceback que muestra ambas excepciones, facilitando el debugging.

---

## Estructuras de datos avanzadas

### El módulo collections

Python incluye estructuras de datos especializadas que simplifican patrones comunes:

**`defaultdict`**: diccionario que crea valores por defecto

```python
from collections import defaultdict

# Sin defaultdict
conteo = {}
for palabra in texto.split():
    if palabra not in conteo:
        conteo[palabra] = 0
    conteo[palabra] += 1

# Con defaultdict
conteo = defaultdict(int)  # int() retorna 0
for palabra in texto.split():
    conteo[palabra] += 1  # Automáticamente crea la entrada si no existe
```

**`Counter`**: contar cosas es tan común que tiene su propia clase

```python
from collections import Counter

palabras = ["manzana", "banana", "manzana", "naranja", "manzana"]
conteo = Counter(palabras)

print(conteo["manzana"])       # 3
print(conteo.most_common(2))   # [('manzana', 3), ('banana', 1)]
```

**`deque`**: cola eficiente de doble extremo

```python
from collections import deque

# Las listas son lentas para insertar/eliminar al principio
# deque es O(1) en ambos extremos
cola = deque(maxlen=5)  # Máximo 5 elementos
for i in range(10):
    cola.append(i)  # Los viejos se descartan automáticamente

print(list(cola))  # [5, 6, 7, 8, 9]
```

**`namedtuple`**: tuplas con nombres

```python
from collections import namedtuple

Punto = namedtuple('Punto', ['x', 'y'])
p = Punto(3, 4)

print(p.x, p.y)      # 3 4 - Acceso por nombre
print(p[0], p[1])    # 3 4 - También por índice
```

### dataclasses: clases modernas

Desde Python 3.7, `dataclasses` simplifica la creación de clases que principalmente guardan datos:

```python
from dataclasses import dataclass, field
from typing import List

@dataclass
class Estudiante:
    nombre: str
    legajo: int
    notas: List[float] = field(default_factory=list)

    @property
    def promedio(self):
        return sum(self.notas) / len(self.notas) if self.notas else 0.0

# Automáticamente genera __init__, __repr__, __eq__
e = Estudiante("Ana García", 12345, [8.5, 9.0, 7.5])
print(e)  # Estudiante(nombre='Ana García', legajo=12345, notas=[8.5, 9.0, 7.5])
print(e.promedio)  # 8.333...
```

Sin `@dataclass`, tendrías que escribir:

```python
class Estudiante:
    def __init__(self, nombre, legajo, notas=None):
        self.nombre = nombre
        self.legajo = legajo
        self.notas = notas if notas is not None else []

    def __repr__(self):
        return f"Estudiante(nombre={self.nombre!r}, legajo={self.legajo!r}, notas={self.notas!r})"

    def __eq__(self, other):
        if not isinstance(other, Estudiante):
            return NotImplemented
        return (self.nombre, self.legajo, self.notas) == (other.nombre, other.legajo, other.notas)
```

Mucho código repetitivo que `@dataclass` genera automáticamente.

### Type hints: documentación ejecutable

Python es dinámico, pero desde la versión 3.5 podés agregar anotaciones de tipo:

```python
from typing import List, Dict, Optional, Callable

def procesar_datos(
    items: List[str],
    transformar: Callable[[str], str],
    config: Optional[Dict[str, str]] = None
) -> List[str]:
    """Procesa una lista de strings aplicando una transformación."""
    resultado = [transformar(item) for item in items]
    return resultado
```

Los tipos no se verifican en runtime (Python sigue siendo dinámico), pero:
- Documentan el código claramente
- Los IDEs los usan para autocompletado y detección de errores
- Herramientas como `mypy` pueden verificarlos estáticamente

En código de sistemas donde los bugs son costosos, los type hints ayudan a prevenir errores antes de que ocurran.

---

## Cómo encaja todo esto

Estas herramientas no son académicas. Veamos un ejemplo que combina varias:

```python
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Iterator
import socket

@dataclass
class Mensaje:
    origen: str
    contenido: str

@contextmanager
def conexion_servidor(host: str, puerto: int) -> Iterator[socket.socket]:
    """Context manager para conexiones de red."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect((host, puerto))
        yield sock
    finally:
        sock.close()

def leer_mensajes(sock: socket.socket) -> Iterator[Mensaje]:
    """Generador que lee mensajes del socket."""
    buffer = b""
    while True:
        datos = sock.recv(1024)
        if not datos:
            break
        buffer += datos
        while b"\n" in buffer:
            linea, buffer = buffer.split(b"\n", 1)
            yield Mensaje(origen=sock.getpeername()[0],
                         contenido=linea.decode())

# Uso combinando todo
try:
    with conexion_servidor("servidor.ejemplo.com", 8080) as conn:
        for mensaje in leer_mensajes(conn):
            procesar(mensaje)
except ConnectionRefusedError:
    print("El servidor no está disponible")
```

Este código:
- Usa un context manager para garantizar que la conexión se cierre
- Usa un generador para procesar mensajes sin cargar todo en memoria
- Usa dataclass para representar mensajes de forma clara
- Usa type hints para documentar qué espera cada función
- Maneja excepciones específicas de forma apropiada

Es el tipo de código que vas a escribir en esta materia.

---

## Resumen

| Concepto | Para qué lo usás |
|----------|------------------|
| Context managers (`with`) | Garantizar limpieza de recursos |
| Decoradores (`@`) | Agregar comportamiento a funciones |
| Generadores (`yield`) | Procesar datos lazy, sin cargar en memoria |
| Closures | Funciones con estado encapsulado |
| Type hints | Documentar y verificar tipos |
| dataclasses | Clases de datos sin boilerplate |
| collections | Estructuras de datos especializadas |

Estas herramientas son fundamentales para el código que vas a escribir en la materia. No te preocupes si no las dominás todavía: las vas a practicar en cada ejercicio, en cada TP. La repetición hace la maestría.

---

*Computación II - 2026 - Bloque 0 Autónomo*
