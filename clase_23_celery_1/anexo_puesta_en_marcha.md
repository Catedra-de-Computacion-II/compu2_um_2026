# Anexo: poner todo en marcha

Guía de instalación y de los errores con los que te vas a cruzar. Sirve para la clase 23 y para la 24.

Si algo no te funciona, buscá el síntoma en la sección **Cuando algo falla**, al final: está ordenada por el mensaje de error que ves, no por el tema.

---

## Qué hace falta

Tres cosas, y una de ellas ya la tenés desde la clase 1.

| | Para qué | Cómo verificar |
|---|---|---|
| Docker | levantar Redis (el broker) | `docker --version` |
| Python 3.11+ | correr los scripts y el worker | `python3 --version` |
| `celery` y `redis` | las bibliotecas | ver abajo |

No hace falta instalar Redis en tu máquina: corre dentro de un contenedor.

---

## Paso 1: Docker

Si venís haciendo las clases, ya lo tenés. Para confirmarlo:

```bash
docker --version
docker run --rm hello-world
```

El segundo comando descarga una imagen mínima, la corre y la borra. Si imprime un saludo, Docker funciona.

### Si da "permission denied"

```
permission denied while trying to connect to the Docker daemon socket
```

Tu usuario no está en el grupo `docker`. Se arregla una vez:

```bash
sudo usermod -aG docker $USER
```

Y después **cerrá sesión y volvé a entrar** (o reiniciá). El cambio de grupo no aplica a las terminales que ya estaban abiertas, que es la razón por la que muchos creen que no funcionó.

Mientras tanto podés usar `sudo docker ...`, pero conviene arreglarlo: todos los comandos de la clase asumen que no hace falta.

### `docker compose` con espacio, no `docker-compose`

Las versiones actuales traen Compose como **subcomando** de Docker:

```bash
docker compose version      # correcto hoy
```

El `docker-compose` con guion era un programa aparte (la versión 1), descontinuado. Si encontrás tutoriales viejos con guion, el reemplazo es directo: sacale el guion.

---

## Paso 2: el broker

Desde el directorio de la clase:

```bash
cd clase_23_celery_1
docker compose up -d
```

El `-d` es *detached*: lo deja corriendo de fondo y te devuelve la terminal.

Verificar que responde:

```bash
docker compose exec redis redis-cli ping
```

```
PONG
```

Ese `PONG` es la señal de que el broker está listo. Si no lo ves, no sigas: todo lo demás depende de esto.

Para bajarlo cuando termines:

```bash
docker compose down
```

### Por qué el puerto 6399

El `docker-compose.yml` mapea `6399:6379`. El 6379 es el puerto de Redis adentro del contenedor; el 6399 es por dónde lo alcanzás desde tu máquina.

Elegimos el 6399 y no el 6379 para no chocar con un Redis que ya tengas instalado o con otro proyecto. Si en tu máquina el 6399 también está ocupado, cambialo en el `docker-compose.yml` y **acordate de cambiarlo también en `tareas.py`**, donde está la URL del broker. Son los dos únicos lugares.

---

## Paso 3: las bibliotecas de Python

Acá está el error más común de la clase, así que vale leerlo antes de chocarlo.

### El problema

Esto, que es lo que dice cualquier tutorial:

```bash
pip install celery redis
```

En Debian 12+, Ubuntu 23.04+ y derivados falla así:

```
error: externally-managed-environment

× This environment is externally managed
╰─> To install Python packages system-wide, try apt install
    python3-xyz, where xyz is the package you are trying to
    install.

    If you wish to install a non-Debian-packaged Python package,
    create a virtual environment using python3 -m venv path/to/venv.
    ...
```

No es un error tuyo ni un Python roto. Es deliberado: el sistema operativo usa su propio Python para herramientas internas, y si instalás paquetes ahí podés romperlas. La distribución te lo bloquea a propósito.

### La solución: un entorno virtual

Un **entorno virtual** (*virtualenv* o *venv*) es una carpeta con una copia aislada de Python y sus paquetes. Lo que instalás adentro no toca el sistema, y podés borrarlo con un `rm -rf` sin consecuencias.

```bash
cd clase_23_celery_1

python3 -m venv venv              # crear (una sola vez)
source venv/bin/activate          # activar (cada vez que abrís una terminal)
pip install celery redis          # instalar, ya sin error
```

Cuando está activado, el prompt cambia:

```
(venv) gabriel@maquina:~/clase_23_celery_1$
```

Ese `(venv)` es la señal de que estás adentro. Para salir, `deactivate`.

Verificar que quedó bien:

```bash
python3 -c "import celery, redis; print(celery.__version__)"
```

```
5.6.3
```

### Lo importante del venv en esta clase

**Cada terminal necesita su propia activación.** La clase usa tres terminales, y el venv hay que activarlo en las tres:

```bash
source venv/bin/activate     # en la terminal 2 (el worker)
source venv/bin/activate     # en la terminal 3 (los scripts)
```

Si te olvidás, el síntoma es `ModuleNotFoundError: No module named 'celery'` o `command not found: celery`. No es que se haya desinstalado: es que esa terminal no está en el entorno.

### Alternativa: pipx o el gestor de tu distro

Si preferís no usar venv:

```bash
sudo apt install python3-celery python3-redis    # Debian/Ubuntu
```

Funciona, pero las versiones de la distro suelen ir atrasadas. Para la materia, el venv es el camino recomendado y además es lo que vas a usar en cualquier proyecto real.

---

## Paso 4: las tres terminales

Celery se entiende mejor cuando se ve que son procesos separados. Dejá las tres abiertas.

**Terminal 1 — el broker.** Se levanta una vez y se olvida:

```bash
cd clase_23_celery_1
docker compose up -d
docker compose exec redis redis-cli ping     # PONG
```

**Terminal 2 — el worker.** Queda ocupada mostrando logs: eso es normal, no está colgada.

```bash
cd clase_23_celery_1
source venv/bin/activate
celery -A tareas worker --loglevel=info --concurrency=2
```

Tiene que imprimir el banner y terminar con:

```
[tasks]
  . tareas.dividir
  . tareas.lenta
  . tareas.saludar
  . tareas.sumar

celery@tu-maquina ready.
```

Ese `ready.` es la señal. Para pararlo, `Ctrl+C`.

**Terminal 3 — vos.** Desde acá corrés los scripts:

```bash
cd clase_23_celery_1
source venv/bin/activate
python3 encolar.py
python3 consultar.py
```

> **Para el experimento del principio de la clase**, el de los tres pasos, la terminal 2 tiene que estar **apagada**. La gracia es encolar sin que haya nadie para ejecutar. Si el worker está corriendo, toma la tarea al instante y `LLEN celery` te va a dar 0 en lugar de 1.

---

## Cuando algo falla

Ordenado por el mensaje que ves.

### `error: externally-managed-environment`

Falta el entorno virtual. Ver el paso 3.

### `ModuleNotFoundError: No module named 'celery'`

El venv no está activado **en esa terminal**:

```bash
source venv/bin/activate
```

Si ya está activado y sigue fallando, no instalaste los paquetes adentro: repetí el `pip install`.

### `command not found: celery`

Lo mismo: el comando `celery` vive dentro del venv.

### `permission denied ... docker daemon socket`

Falta el grupo docker, y después cerrar sesión. Ver el paso 1.

### `Connection refused`, o `Retry limit exceeded while trying to reconnect`

El broker no está arriba, o no es el puerto que creés.

El traceback es largo y engañoso: lo último que imprime es un `RuntimeError` sobre el *result store*, que suena a otra cosa. La causa real está más arriba:

```
redis.exceptions.ConnectionError: Error 111 connecting to localhost:6399. Connection refused.
```

Cuando un error de estos te desconcierte, leé el traceback **de arriba hacia abajo**, no solo la última línea: Python muestra primero la causa y después las consecuencias.

Revisá en orden:

```bash
docker compose ps                              # ¿corre?
docker compose exec redis redis-cli ping       # ¿responde?
docker compose logs redis                      # ¿qué dice?
```

Si `docker compose ps` no muestra nada, estás en el directorio equivocado: el comando busca el `docker-compose.yml` en la carpeta actual.

### `port is already allocated`

Otro proceso ocupa el puerto. Para ver quién:

```bash
docker ps                      # ¿es otro contenedor tuyo?
ss -tlnp | grep 6399           # ¿es un programa del sistema?
```

Dos salidas: parar lo que estorba, o cambiar el puerto en el `docker-compose.yml` (y en `tareas.py`).

En la clase 24, la API tiene preparada una variable para esto:

```bash
PUERTO_API=8010 docker compose up -d
```

### La tarea queda en PENDING para siempre

El caso más frecuente, y tiene tres causas posibles. Revisalas en este orden:

1. **No hay worker corriendo.** Mirá la terminal 2.
2. **El worker está en otro broker.** Comparalo: la URL del banner del worker contra la de `tareas.py`. Tienen que ser idénticas.
3. **El worker no conoce la tarea.** Buscá su nombre en la lista `[tasks]` del banner. Si no aparece, ese worker no tiene registrada esa tarea: la agregaste a `tareas.py` después de levantarlo, o está escrita en otro archivo que Celery no importa.

Recordá también lo que vimos en clase: `PENDING` significa "el backend no sabe nada de este id", no "está en la cola". Un id mal copiado da `PENDING` igual que uno encolado.

### `Error: Unable to load celery application.`

El worker no encontró `tareas.py`. El `-A tareas` es un **import de Python**, así que busca el archivo en el directorio desde donde lanzaste el comando.

Casi siempre es eso: estás parado en otro lado.

```bash
pwd       # tenés que estar en clase_23_celery_1
ls        # tiene que aparecer tareas.py
```

Si el archivo está y el error sigue, probá importarlo a mano para ver el error de verdad:

```bash
python3 -c "import tareas"
```

### Cambié `tareas.py` y el worker ignora el cambio

El worker carga el código **al arrancar**. Después de editar, `Ctrl+C` y volvelo a levantar.

(En la clase 24 esto no pasa con la API porque uvicorn corre con `--reload`; el worker no tiene equivalente por default.)

### El worker arranca y se cierra solo

Mirá las últimas líneas antes del cierre. Casi siempre es un error de sintaxis o un import que falla en `tareas.py`. Probalo por separado:

```bash
python3 -c "import tareas"
```

Si eso falla, el worker no tiene chance.

---

## Para la clase 24

El anexo vale igual, con dos diferencias.

**Ya no hace falta el venv** para correr el sistema: todo vive en contenedores y las dependencias se instalan dentro de la imagen, vía `requirements.txt`. El venv te sirve solo si querés correr algo suelto desde tu máquina.

**Se levanta todo junto:**

```bash
cd clase_24_celery_2/proyecto
docker compose up -d --build
```

El `--build` construye la imagen la primera vez y cuando cambies el `Dockerfile` o el `requirements.txt`. Tarda unos minutos la primera vez: está bajando Python y los paquetes.

Comandos que vas a usar seguido:

```bash
docker compose ps                        # qué está corriendo
docker compose logs -f worker            # seguir el log de un servicio
docker compose up -d --scale worker=3    # tres workers
docker compose restart api               # reiniciar uno solo
docker compose exec api bash             # entrar a un contenedor
docker compose down                      # bajar todo
```

Ese `docker compose exec api bash` es la herramienta de diagnóstico más útil: te deja adentro del contenedor, donde podés probar si `redis` resuelve, si el import funciona, y todo lo demás.

---

## Dejar la máquina limpia

Al terminar:

```bash
docker compose down          # para y borra los contenedores
docker compose down -v       # además borra los volúmenes (los datos)
```

Para ver si quedó algo dando vueltas:

```bash
docker ps                    # contenedores corriendo
docker ps -a                 # incluidos los parados
```

El venv se borra con `rm -rf venv`. No deja nada en el sistema — esa es toda la gracia.

---

*Computación II - 2026 - Clase 23*
