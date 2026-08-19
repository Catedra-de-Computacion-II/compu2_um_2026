# Clase 1: Docker Intro - Autoevaluación

Respondé estas preguntas para verificar tu comprensión. Las respuestas están al final.

---

## Conceptos (10 preguntas)

### Pregunta 1
¿Cuál es la diferencia principal entre un contenedor y una máquina virtual?

a) Los contenedores son más lentos
b) Los contenedores son más seguros
c) Los contenedores comparten el kernel del host, las VMs tienen su propio kernel
d) No hay diferencia significativa

### Pregunta 2
¿Qué es una imagen Docker?

a) Una copia del sistema operativo del host
b) Un template inmutable a partir del cual se crean contenedores
c) Un archivo de configuración
d) Un contenedor guardado

### Pregunta 3
¿Qué sucede cuando ejecutás `docker run ubuntu` sin ningún comando adicional?

a) Da un error porque falta el comando
b) Ubuntu arranca y queda corriendo indefinidamente
c) Abre un shell interactivo
d) Ubuntu arranca, no tiene nada que hacer, y termina inmediatamente

### Pregunta 4
¿Para qué sirven las opciones `-it` en `docker run -it ubuntu bash`?

a) Para modo interactivo con terminal (interactive + tty)
b) Para instalar paquetes
c) Para correr en background
d) Para correr más rápido

### Pregunta 5
¿Qué pasa con los archivos creados dentro de un contenedor cuando el contenedor se elimina?

a) Se mueven a /tmp
b) Se guardan automáticamente en el host
c) Se pierden (a menos que uses volúmenes)
d) Se guardan en Docker Hub

### Pregunta 6
¿Qué comando muestra los contenedores que están corriendo actualmente?

a) `docker ps`
b) `docker containers`
c) `docker list`
d) `docker images`

### Pregunta 7
¿Qué es Docker Hub?

a) El kernel de Docker
b) Un registro público de imágenes Docker
c) El daemon de Docker
d) Una herramienta de desarrollo

### Pregunta 8
Si querés correr Python 3.9 específicamente, ¿qué comando usás?

a) `docker run python --version 3.9`
b) `docker run python-3.9`
c) `docker run python/3.9`
d) `docker run python:3.9`

### Pregunta 9
¿Qué hace la opción `-v $(pwd):/app` en docker run?

a) Define una variable de entorno
b) Descarga la aplicación desde Docker Hub
c) Monta el directorio actual del host en /app dentro del contenedor
d) Crea un volumen vacío llamado "app"

### Pregunta 10
¿Por qué Docker es útil para este curso?

a) Porque es más rápido que Python nativo
b) Porque reemplaza a Git
c) Porque garantiza que todos trabajamos en el mismo ambiente
d) Porque es obligatorio para programación concurrente

---

## Comandos (5 preguntas)

### Pregunta 11
¿Qué comando elimina todos los contenedores detenidos?

a) `docker rm -all`
b) `docker clean`
c) `docker delete stopped`
d) `docker container prune`

### Pregunta 12
¿Cómo ves las imágenes descargadas en tu sistema?

a) `docker list images`
b) `docker show`
c) `docker images`
d) `docker ps`

### Pregunta 13
¿Qué comando ejecuta un proceso dentro de un contenedor que ya está corriendo?

a) `docker run`
b) `docker start`
c) `docker attach`
d) `docker exec`

### Pregunta 14
¿Cómo detenés un contenedor que está corriendo?

a) `docker stop <id>`
b) `docker pause`
c) `docker kill`
d) `docker end`

### Pregunta 15
¿Qué opción hace que un contenedor corra en background (detached)?

a) `-bg`
b) `--background`
c) `-d`
d) `-b`

---

## Respuestas

<details>
<summary>Click para ver respuestas</summary>

### Conceptos
1. **c** - Los contenedores comparten el kernel, las VMs tienen su propio kernel
2. **b** - Un template inmutable a partir del cual se crean contenedores
3. **d** - Ubuntu arranca, no tiene nada que hacer, y termina inmediatamente
4. **a** - Para modo interactivo con terminal
5. **c** - Se pierden (a menos que uses volúmenes)
6. **a** - `docker ps`
7. **b** - Un registro público de imágenes Docker
8. **d** - `docker run python:3.9`
9. **c** - Monta el directorio actual del host en /app dentro del contenedor
10. **c** - Porque garantiza que todos trabajamos en el mismo ambiente

### Comandos
11. **d** - `docker container prune`
12. **c** - `docker images`
13. **d** - `docker exec`
14. **a** - `docker stop <id>`
15. **c** - `-d`

### Puntuación
- 13-15: Excelente, estás listo para la próxima clase
- 10-12: Bien, pero repasá los conceptos que fallaste
- 7-9: Necesitás practicar más con los comandos
- <7: Volvé a leer el material y hacer los ejercicios

</details>

---

*Computación II - 2026 - Clase 1*
