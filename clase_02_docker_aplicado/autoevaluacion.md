# Clase 2: Docker Aplicado - Autoevaluación

Responde estas preguntas para verificar tu comprensión. Las respuestas están al final.

---

## Parte 1: Volúmenes (5 preguntas)

### Pregunta 1
¿Qué problema fundamental resuelven los volúmenes en Docker?

a) Mejoran la seguridad
b) Permiten persistir datos más allá del ciclo de vida del contenedor
c) Reducen el tamaño de las imágenes
d) Hacen los contenedores más rápidos

### Pregunta 2
¿Cuál es la diferencia principal entre un bind mount y un named volume?

a) Los bind mounts son más rápidos
b) Los bind mounts montan una ruta específica del host, los named volumes son gestionados por Docker
c) No hay diferencia, son sinónimos
d) Los named volumes no persisten datos

### Pregunta 3
¿Qué comando lista todos los volúmenes de Docker?

a) `docker volumes`
b) `docker show volumes`
c) `docker volume list`
d) `docker volume ls`

### Pregunta 4
En la opción `-v /host/path:/container/path`, ¿cuál es la ruta del contenedor?

a) `/host/path`
b) Depende del orden
c) Ambas son del contenedor
d) `/container/path`

### Pregunta 5
¿Qué sucede con un named volume cuando eliminas el contenedor que lo usa?

a) Se corrompe
b) Se elimina automáticamente
c) Permanece disponible para otros contenedores
d) Se convierte en bind mount

---

## Parte 2: Redes (4 preguntas)

### Pregunta 6
¿Qué ventaja tiene crear una red personalizada frente a usar la red bridge por defecto?

a) Permite resolución DNS por nombre de contenedor
b) Es más rápida
c) Es más segura automáticamente
d) Usa menos memoria

### Pregunta 7
¿Qué comando crea una red llamada "mi_red"?

a) `docker create network mi_red`
b) `docker net create mi_red`
c) `docker network create mi_red`
d) `docker network new mi_red`

### Pregunta 8
Si dos contenedores están en la misma red personalizada, ¿cómo se conectan entre sí?

a) Por nombre de contenedor (DNS automático)
b) Solo por IP
c) Solo a través del host
d) No pueden conectarse

### Pregunta 9
¿Qué tipo de red usarías si necesitas que un contenedor comparta el stack de red del host?

a) none
b) bridge
c) host
d) overlay

---

## Parte 3: Dockerfile (5 preguntas)

### Pregunta 10
¿Qué instrucción establece el directorio de trabajo dentro del contenedor?

a) `DIR /app`
b) `CHDIR /app`
c) `WORKDIR /app`
d) `CD /app`

### Pregunta 11
¿Cuál es la diferencia entre `COPY` y `ADD`?

a) `ADD` puede extraer archivos tar y descargar URLs, `COPY` solo copia
b) `COPY` es más nuevo y reemplaza a `ADD`
c) No hay diferencia
d) `ADD` solo funciona con directorios

### Pregunta 12
¿Por qué es importante el orden de las instrucciones en un Dockerfile?

a) El orden afecta el cache de capas - lo que cambia menos va primero
b) El orden no importa
c) Docker las ejecuta en paralelo
d) Solo importa que FROM sea primero

### Pregunta 13
¿Qué diferencia hay entre `CMD` y `ENTRYPOINT`?

a) `CMD` solo acepta un argumento
b) `CMD` puede sobrescribirse fácilmente, `ENTRYPOINT` define el ejecutable base
c) `ENTRYPOINT` es obsoleto
d) Son exactamente iguales

### Pregunta 14
¿Qué hace la instrucción `EXPOSE 8000`?

a) Documenta que el contenedor escucha en el puerto 8000
b) Redirige el puerto 8000 al 80
c) Bloquea el puerto 8000
d) Publica automáticamente el puerto 8000

---

## Parte 4: Docker Compose (6 preguntas)

### Pregunta 15
¿Qué problema resuelve Docker Compose?

a) Orquesta múltiples contenedores como una aplicación unificada
b) Reemplaza a Kubernetes
c) Comprime los contenedores
d) Hace las imágenes más pequeñas

### Pregunta 16
¿Qué comando levanta todos los servicios definidos en docker-compose.yml?

a) `docker-compose start`
b) `docker-compose run`
c) `docker-compose launch`
d) `docker-compose up`

### Pregunta 17
¿Qué hace la opción `-d` en `docker-compose up -d`?

a) Modo detached (segundo plano)
b) Modo desarrollo
c) Elimina contenedores previos
d) Modo debug

### Pregunta 18
¿Qué significa `depends_on` en un servicio de Compose?

a) Instala dependencias de Python
b) Define el orden de inicio de contenedores
c) Comparte volúmenes
d) Copia archivos de otro servicio

### Pregunta 19
¿Cómo defines una variable de entorno en docker-compose.yml?

a) `vars: [MI_VAR=valor]`
b) `export MI_VAR=valor`
c) `env: MI_VAR=valor`
d) `environment: - MI_VAR=valor`

### Pregunta 20
¿Qué archivo se aplica automáticamente junto con docker-compose.yml?

a) docker-compose.prod.yml
b) docker-compose.dev.yml
c) docker-compose.local.yml
d) docker-compose.override.yml

---

## Respuestas

<details>
<summary>Click para ver respuestas</summary>

### Parte 1: Volúmenes
1. **b** - Permiten persistir datos más allá del ciclo de vida del contenedor
2. **b** - Los bind mounts montan una ruta específica del host, los named volumes son gestionados por Docker
3. **d** - `docker volume ls`
4. **d** - `/container/path` (formato: host:contenedor)
5. **c** - Permanece disponible para otros contenedores

### Parte 2: Redes
6. **a** - Permite resolución DNS por nombre de contenedor
7. **c** - `docker network create mi_red`
8. **a** - Por nombre de contenedor (DNS automático)
9. **c** - host

### Parte 3: Dockerfile
10. **c** - `WORKDIR /app`
11. **a** - `ADD` puede extraer archivos tar y descargar URLs, `COPY` solo copia
12. **a** - El orden afecta el cache de capas - lo que cambia menos va primero
13. **b** - `CMD` puede sobrescribirse fácilmente, `ENTRYPOINT` define el ejecutable base
14. **a** - Documenta que el contenedor escucha en el puerto 8000

### Parte 4: Docker Compose
15. **a** - Orquesta múltiples contenedores como una aplicación unificada
16. **d** - `docker-compose up`
17. **a** - Modo detached (segundo plano)
18. **b** - Define el orden de inicio de contenedores
19. **d** - `environment: - MI_VAR=valor`
20. **d** - docker-compose.override.yml

### Puntuación
- 18-20: Excelente dominio de Docker aplicado
- 14-17: Buen nivel, listo para usar Docker en proyectos
- 10-13: Necesitas repasar algunos conceptos
- <10: Revisa el material y practica más

</details>

---

*Computación II - 2026 - Clase 2*
