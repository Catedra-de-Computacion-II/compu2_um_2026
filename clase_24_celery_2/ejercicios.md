# Clase 24: Celery II - Ejercicios Prácticos

El directorio `proyecto/` tiene el sistema completo: `docker-compose.yml`, `Dockerfile`, `api.py`, `tareas.py` y `requirements.txt`.

## Antes de empezar

> Si algo no arranca, el anexo de la clase 23 (`clase_23_celery_1/anexo_puesta_en_marcha.md`) tiene los errores habituales ordenados por el mensaje que ves. Vale igual acá, y la última sección es específica de esta clase.

```bash
cd proyecto
docker compose up -d --build
docker compose ps
curl localhost:8000/salud
```

Hoy **no hace falta entorno virtual**: las dependencias se instalan dentro de la imagen, vía `requirements.txt`. La primera vez el `--build` tarda unos minutos porque baja Python y los paquetes; después queda cacheado.

Tiene que responder algo así:

```json
{"api":"ok","workers":["celery@c4263a10f1af"]}
```

Si `workers` viene vacío, la API está bien pero ningún worker se registró: mirá `docker compose logs worker`.

Si el 8000 está ocupado en tu máquina:

```bash
PUERTO_API=8010 docker compose up -d --build
```

---

## Ejercicio 1: Orquestar y escalar (obligatorio)

### Objetivo

Comprobar que el escalado horizontal no requiere tocar el código.

### Parte A: el sistema arriba

1. Levantá todo y pegá la salida de `docker compose ps`. ¿Cuántos servicios hay?
2. Mirá el log de arranque: ¿en qué orden arrancaron? ¿Por qué la API esperó?
3. ¿Cuántos servicios publican puertos al host? ¿Por qué Redis no?
4. Entrá al contenedor de la API y verificá que `redis` resuelve:

```bash
docker compose exec api python -c "import socket; print(socket.gethostbyname('redis'))"
```

5. ¿Qué IP te dio? ¿Está en tu máquina esa IP?

### Parte B: medir el escalado

6. Con **1 worker**, medí 6 tareas de 4 segundos:

```bash
docker compose exec api python -c "
import time
from celery import group
from tareas import esperar
t0 = time.perf_counter()
group(esperar.s(4) for _ in range(6)).apply_async().get(timeout=90)
print(f'{time.perf_counter()-t0:.2f}s')
"
```

7. Escalá a 3 workers y repetí:

```bash
docker compose up -d --scale worker=3
```

8. Anotá los dos tiempos. ¿Qué proporción hay? ¿Coincide con la cantidad de slots?
9. ¿Modificaste una sola línea de Python entre las dos mediciones?
10. Escalá a 6 workers (12 slots) y repetí. ¿Mejora respecto de 3? ¿Por qué?

### Parte C: lo que no se puede escalar

11. Intentá `docker compose up -d --scale api=2`. ¿Qué error da?
12. Explicá por qué el worker sí y la API no.
13. ¿Qué habría que cambiar para poder tener 3 APIs? (Pensá en qué hace falta adelante.)
14. Agregale `container_name: mi_worker` al servicio worker y probá escalar. ¿Qué pasa?

### Parte D: sobrevivir a los reinicios

15. Encolá una tarea de 60 segundos.
16. Reiniciá la API: `docker compose restart api`.
17. Consultá el id. ¿Sigue ahí? ¿Por qué?
18. Ahora reiniciá el worker a mitad de una tarea. ¿Qué pasa con esa tarea? Relacionalo con `acks_late`.
19. Bajá **todo** (`docker compose down`), volvé a levantar y consultá un id viejo. ¿Está el resultado? ¿Por qué sí o por qué no?

---

## Ejercicio 2: La API asincrónica

### 2.1 El patrón

1. Hacé un POST y pegá la respuesta completa, con el código de estado (`curl -i`).
2. ¿Por qué 202 y no 200 ni 201?
3. Consultá el id tres veces: inmediatamente, a mitad y al final. Anotá los tres estados.
4. ¿Viste `STARTED`? ¿Qué línea de `tareas.py` lo hace posible?
5. Comentá `task_track_started` y repetí. ¿Qué estados ves ahora?

### 2.2 El cliente que desaparece

6. Encolá una tarea de 30 s y cerrá la terminal.
7. Desde otra terminal, consultá el id. ¿Funciona?
8. Explicá por qué esto no se puede hacer con el `run_in_executor` de la clase 21.

### 2.3 Errores

9. Mandá un `tipo` inválido. ¿Qué devuelve?
10. Encolá `descargar` con una URL que contenga "roto". Consultá el estado cada 2 segundos y anotá la secuencia completa.
11. ¿Viste el estado `RETRY`? ¿Cuántas veces?
12. ¿Qué estado queda al final?

---

## Ejercicio 3: Canvas

### 3.1 Las tres primitivas

```bash
docker compose exec api python
```

1. Armá un `chain` de tres pasos y verificá el resultado.
2. ¿Qué pasa si una tarea del medio falla? ¿Se ejecutan las siguientes?
3. Armá un `group` de 5 tareas. ¿En qué orden vuelven los resultados?
4. Armá un `chord` que calcule el promedio de 10 cuadrados.
5. En el chord, ¿qué recibe exactamente la tarea final? Imprimilo.

### 3.2 Las firmas

6. ¿Qué diferencia hay entre `sumar.s(2, 3)` y `sumar.delay(2, 3)`?
7. ¿Qué tipo de objeto devuelve `.s()`? Imprimilo con `type()`.
8. Compará `.s()` con `functools.partial`. ¿En qué se parecen?
9. ¿Por qué `duplicar.s()` va sin argumentos dentro de un chain?
10. Buscá `.si()` (immutable signature). ¿Para qué sirve?

### 3.3 Un pipeline de verdad

11. Armá este flujo con Canvas:
    - bajar 4 "archivos" en paralelo (simulá con `esperar`)
    - hashear cada uno
    - generar un informe con todos los hashes
12. ¿Qué primitivas usaste y en qué orden?
13. Mirá el flujo en Flower. ¿Se ve la estructura?

---

## Ejercicio 4: Fallas e idempotencia

### 4.1 Reintentos

1. Encolá `inestable` con `exito_cada=10` y mirá el log del worker. ¿Cuántos intentos hizo?
2. Anotá los tiempos entre intentos. ¿Crecen? ¿Según qué fórmula?
3. ¿Qué pasa cuando se agotan los `max_retries`?
4. Cambiá `autoretry_for` a `(ValueError,)` en `descargar` y encolá una URL rota. ¿Reintenta? ¿Por qué no?
5. Explicá por qué reintentar un `ValueError` por datos mal formados es inútil.

### 4.2 Idempotencia (clave)

6. Encolá `cobrar_mal` tres veces con el **mismo** `pedido_id`. ¿Cuál es el total?
7. Hacé lo mismo con `cobrar_bien`. ¿Cuál es el total?
8. Explicá qué hace exactamente que la segunda sea idempotente.
9. Seguí la cadena de razonamiento completa: ¿por qué `acks_late=True` **obliga** a que las tareas sean idempotentes?
10. ¿Por qué no existe *exactly once*? Buscá "Two Generals Problem" y resumilo en tres renglones.

### 4.3 Hacer idempotente lo que no lo es

Para cada tarea, decí si es idempotente y, si no, reescribila:

11. `incrementar_contador(usuario_id)`
12. `enviar_mail(destinatario, asunto, cuerpo)`
13. `generar_pdf(reporte_id)` que escribe en `/reportes/{reporte_id}.pdf`
14. `cobrar(tarjeta, monto)`
15. `UPDATE stock SET cantidad = cantidad - 1 WHERE id = 5`
16. `UPDATE stock SET cantidad = 99 WHERE id = 5`

---

## Ejercicio 5: Observar

1. Abrí Flower en `http://localhost:5555`.
2. Escalá a 3 workers y encolá 50 tareas de 2 segundos. Mirá la pestaña Workers mientras corren.
3. ¿Se reparten parejo? ¿Hay alguno que acapare? (Pensá en `prefetch`.)
4. Mirá la pestaña Broker: ¿la cola crece y baja, o crece sin bajar?
5. Encolá 200 tareas de 5 segundos con 1 worker. ¿Qué pasa con la cola? ¿Cómo se ve "me faltan workers" en el dashboard?
6. Probá los tres `inspect` por línea de comandos:

```bash
docker compose exec worker celery -A tareas inspect active
docker compose exec worker celery -A tareas inspect stats
docker compose exec worker celery -A tareas inspect registered
```

7. Provocá el error clásico: encolá una tarea que el worker no tenga registrada. ¿Cómo lo diagnosticás con `inspect registered`?

---

## Verificación del ejercicio obligatorio

### Ejercicio 1: Orquestar y escalar

- [ ] El sistema completo levantado, con la salida de `docker compose ps`
- [ ] Explicaste por qué la API espera a que Redis esté *healthy*
- [ ] Verificaste que `redis` resuelve por DNS dentro de la red
- [ ] Las dos mediciones (1 worker y 3 workers) con números propios
- [ ] Dijiste la proporción y la relacionaste con los slots
- [ ] Confirmaste que no cambiaste código entre las mediciones
- [ ] Probaste que `--scale api=2` falla y explicaste por qué
- [ ] Probaste que el resultado sobrevive a reiniciar la API

---

## Ejercicios adicionales

### Dos colas, dos prioridades

Hacé que las tareas `hashear` vayan a una cola `pesada` y las demás a `rapida`. Levantá dos servicios de worker en el compose, cada uno consumiendo de una sola cola. ¿Qué ganás con eso?

### Celery Beat

Agregá un servicio `beat` al compose que encole una tarea de limpieza cada minuto. Pista: `celery -A tareas beat`. ¿Por qué Beat **no** se puede escalar con `--scale`?

### Healthcheck para el worker

El worker no tiene healthcheck. Escribile uno usando `celery inspect ping`. ¿Qué gana Compose con eso?

### El sistema sin la API

Sacá el servicio `api` del compose y encolá tareas desde un script en tu máquina (fuera de Docker). ¿Qué tenés que cambiar en la URL del broker y por qué?

### Límite de memoria

Agregale al worker un límite de memoria (`deploy.resources.limits.memory`) y encolá una tarea que consuma mucho. ¿Qué pasa con la tarea? Relacionalo con `acks_late` y el OOM killer de la clase 7.

---

*Computación II - 2026 - Clase 24*
