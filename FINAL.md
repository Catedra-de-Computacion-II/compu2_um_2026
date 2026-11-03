
## Requisitos examen final

Para poder rendir el examen final es requisito haber regularizado la materia a fin del semestre.

El examen final consistirá en la exposición de un código integrador desarrollado por el alumno, cuyo tema será acordado previamente con el profesor.

Para definir los requisitos y alcances del trabajo, **antes de entrar a codear** será necesario plantear una arquitectura del proyecto, problema que solucionará, tareas que ejecutarían, entidades, herramientas de sincronismo concurrencia, justificaciones. Una vez que el **tema ha sido discutido y aprobado** para su desarrollo, se acordará un repositorio GIT donde se irán cargando los cambios periódicos en su desarrollo.

### Consideraciones del código:
El código debe solucionar un problema haciendo uso de las herramientas vistas en clase. Debe incluir aspectos como:
* Uso de Sockets con conexión de clientes múltiples de manera concurrente.
* Uso de mecanismos de IPC
* Uso de asincronismo de I/O
* Uso de cola de tareas distribuidas
* Parseo de argumentos por línea de comandos

Otros aspectos adicionales que puede considerarse:
* Despliegue en contenedores Docker
* Almacenamiento de datos en bases de datos
* Uso de Celery para resolver tareas en paralelo.
* Incorporación de entorno visual (web, desktop, etc).

### Definiendo los detalles del proyecto

Los detalles conceptuales del proyecto se deben presentar en el repositorio git de alumno.
Dentro de un directorio llamado **final/**. La intención es la de volcar las ideas a datos concretos de implementación. El repo del proyecto deberá contener un directorio **"doc/"** con la siguiente información: 

* Una descripción verbal de la aplicación (*Quiero armar una app cli-serv que haga esto y esto, donde el cliente envíe xx y el server haga xxxx, se usa concurrencia acá, se usa paralelismo acá, estas entidades se comunican de manera asincrónica usando xxxx, bla, bla*).
* Un gráfico de la arquitectura de la de la app (nodos, conectividad, mecanismos de IPC a implementar).
* Una lista de las funcionalidades de cada entidad (qué hacer el cliente, qué hace el servidor, qué hace cada elemento, etc.).

La intención es interactuar con los profesores para definir y depurar las propuestas, recortando funcionalidad si el proyecto es demasiado extenso, añadiendo funcionalidades si es muy simple, etc. Los cambios de requisitos deberán siempre *commitearse* al repo git.

### Desarrollo

Una vez que la aplicación a desarrollar sea **aprobada** con el profesor de la cátedra, podrá comenzar el desarrollo de la misma.
Durante el desarrollo de la app deberán realizarse commits periódicos en el repo, que reflejen los cambios y progreso del desarrollo.
Asimismo, deberán consultarse los inconvenientes que surjan durante el desarrollo, con la intención de ajustar detalles de los requisitos planteados inicialmente (*doc*).
Una vez desarrollada la app, deberá ser presentada al profesor al menos una semana antes de la mesa de examen final (si puede ser antes mejor, para evitar cambios de ultimo momento), para que éste pueda visarla y permitirle inscribirse a la mesa.

Deberán añadirse algunos archivos markdown adicionales en el repositorio git del proyecto para poder presentarlo en el examen:
* **INSTALL.md**: contendrá las instrucciones para clonar e instalar/lanzar la aplicación, o despliegue de la misma.
* **README.md**: contendrá la ayuda y uso básico de la aplicación.
* **INFO.md**: contendrá un breve informe sobre las decisiones principales de diseño del sistema, y su justificación (ej, por qué un determinado modelo de datos, o tipo de almacenamiento, o uso de multiproceso/multithread, etc).
* **TODO.md**: contendrá una lista detallada de mejoras y posibles nuevas características/features del sistema para futuras versiones.

### Examen final

Durante la presentación, el alumno expondrá el funcionamiento de la aplicación, explicará el código fuente y tecnologías utilizadas, y el tribunal de la mesa podrá:
* Realizar preguntas teóricas sobre los contenidos prácticos expuestos por el alumno.
* Pedir justificaciones de los mecanismos utilizados (*por qué XX y no YY, etc.*)
* Solicitar pequeños *fixes* de bugs detectados durante la presentación, y pequeñas modificaciones del código.

### Notas:

* No tiene fecha **límite de presentación** (mientras no se les venza la regularidad de la materia :P ). Pueden presentarlo a lo largo del año. El único requisito es que, una vez que decidan en qué mesa van a rendir, más tardar una semana antes de la mesa deben tener el código completo y aprobado. Se pueden definir los requisitos de la app, realizar el desarrollo y aprobarlo en cualquier momento, y dejar el código listo para ser presentado en la siguiente mesa disponible.

* El código deberá ser desarrollado de **manera incremental**, por lo que se valoran cambios progresivos (*commits*) en el repositorio de software durante todo el proceso de desarrollo. En la medida que vayan desarrollando la app, vayan commiteando seguido, no esperen a tener una versión funcional para commitear, no importa si funciona o no, commiteen igual! Eso les sirve para que podamos charlar dificultades, inconvenientes, para que yo pueda ver la evolución del proyecto, y de paso, a ustedes les queda un backup de todo lo que van haciendo (ya no es excusa el "se me rompió el disco, me robaron la compu y tenía todo ahí, etc... tenemos git, aprovechenlo!).

* La idea de ese **doc/** en el repositorio es que podamos quedar con una idea fina de lo que van a hacer. A mi me sirve para saber que tienen noción de los alcances de sus apps, lo que tienen que armar, y a ustedes les sirve de guía para no *irse por las ramas* y acotarse a eso. Igualmente durante el desarrollo pueden charlarse cambios, pero lo ideal es que quede lo más definido posible al principio.

