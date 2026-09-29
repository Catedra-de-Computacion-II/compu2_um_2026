# Requisitos del examen final

**Computación II — Universidad de Mendoza — 2026**

---

Para poder rendir el examen final es requisito haber **regularizado la materia** al final del cursado.

El examen final consiste en la exposición de un **código integrador** desarrollado por el alumno, cuyo tema se acuerda previamente con el profesor.

Para definir los requisitos y alcances del trabajo, **antes de empezar a programar** hay que plantear la arquitectura del proyecto: qué problema resuelve, qué tareas ejecuta, qué entidades participan, qué mecanismos de concurrencia y sincronización usa, y por qué. Una vez que el **tema fue discutido y aprobado**, se acuerda un repositorio Git donde se van cargando los cambios durante el desarrollo.

---

## Qué tiene que tener el código

El proyecto debe resolver un problema real usando las herramientas vistas en clase. Es **obligatorio** que incluya:

| Requisito | Dónde se vio |
|-----------|--------------|
| Sockets con múltiples clientes concurrentes | Clases 13 y 14 |
| Mecanismos de IPC | Clases 5 a 9 |
| Asincronismo de I/O | Clases 18 a 21 |
| Cola de tareas distribuidas | Clases 23 y 24 |
| Parseo de argumentos de línea de comandos | Bloque 0 (`argparse_getopt`) |

No hace falta que el proyecto use *todo* de forma forzada: lo que se evalúa es que cada mecanismo esté ahí porque el problema lo justifica. Un socket puesto para cumplir el requisito, sin razón de diseño, cuenta en contra.

Aspectos adicionales que suman:

- Despliegue en contenedores Docker (clases 1 y 2)
- Almacenamiento en base de datos
- Celery para tareas en paralelo
- Interfaz visual (web, escritorio, TUI)

---

## Definir el proyecto antes de codear

Los detalles conceptuales se presentan en el repositorio Git del alumno, dentro de un directorio **`doc/`**. La idea es volcar la propuesta a decisiones concretas de implementación.

Ese directorio debe contener:

- **Una descripción en prosa de la aplicación.** Qué hace, quién le habla a quién, dónde hay concurrencia, dónde paralelismo, qué entidades se comunican de forma asincrónica y con qué mecanismo.
- **Un diagrama de la arquitectura**: nodos, conectividad, mecanismos de IPC a implementar.
- **Una lista de funcionalidades por entidad**: qué hace el cliente, qué hace el servidor, qué hace cada componente.

La intención es interactuar con los profesores para definir y depurar la propuesta: recortar funcionalidad si el proyecto es demasiado extenso, agregar si queda simple. **Todo cambio de requisitos se commitea al repositorio.**

---

## Desarrollo

Una vez que la aplicación fue **aprobada**, empieza el desarrollo.

Durante el proceso hay que hacer **commits frecuentes** que reflejen el progreso, y consultar los inconvenientes que surjan para ajustar los requisitos planteados al principio.

La aplicación debe presentarse al profesor **al menos una semana antes de la mesa de examen** —cuanto antes mejor, para evitar cambios de último momento— para que pueda revisarla y habilitar la inscripción a la mesa.

### Documentación obligatoria

Además del `doc/`, el repositorio debe incluir:

| Archivo | Contenido |
|---------|-----------|
| **`INSTALL.md`** | Cómo clonar, instalar y lanzar la aplicación, o desplegarla |
| **`README.md`** | Ayuda y uso básico |
| **`INFO.md`** | Informe breve sobre las decisiones de diseño y su justificación: por qué ese modelo de datos, ese tipo de almacenamiento, multiproceso contra multithread, etc. |
| **`TODO.md`** | Mejoras y funcionalidades pendientes para futuras versiones |

---

## El examen

Durante la presentación, el alumno expone el funcionamiento de la aplicación y explica el código fuente y las tecnologías utilizadas. El tribunal puede:

- Hacer **preguntas teóricas** sobre los contenidos que el código pone en juego.
- Pedir **justificaciones** de los mecanismos elegidos: *¿por qué X y no Y?*
- Solicitar **modificaciones en vivo**: corregir un bug detectado durante la presentación, o agregar un cambio menor.

Ese último punto merece una aclaración: no se espera que resuelvan algo complejo sobre la marcha, sino que puedan moverse con soltura dentro de su propio código. **Si no podés explicar y modificar lo que entregaste, no aprueba** — aunque funcione perfecto.

---

## Sobre el uso de IA

Vale el mismo criterio que en los trabajos prácticos: **usar IA está permitido y recomendado**. Lo que se evalúa no es quién escribió el código sino que vos entiendas qué hace y por qué.

En el final eso se verifica directamente: vas a tener que explicar decisiones de diseño, justificar alternativas descartadas y modificar el código delante del tribunal. Un proyecto generado sin comprensión se nota en los primeros cinco minutos.

---

## Notas

**No hay fecha límite de presentación**, mientras no se venza la regularidad. Pueden presentarlo a lo largo del año: definir los requisitos, desarrollar y aprobar el código en cualquier momento, y dejarlo listo para la mesa que les convenga. El único requisito es tener el código completo y aprobado **una semana antes** de la mesa elegida.

**El código debe desarrollarse de manera incremental.** Se valoran los commits progresivos durante todo el proceso. Commiteen seguido, no esperen a tener una versión funcional: no importa si anda o no, commiteen igual. Eso permite charlar dificultades sobre código real, deja ver la evolución del proyecto, y de paso les queda un respaldo de todo lo que hicieron. Ya no vale el "se me rompió el disco": tenemos Git, aprovéchenlo.

**El `doc/` no es burocracia.** Sirve para que los profesores sepan que tienen noción del alcance de su aplicación, y a ustedes para acotarse y no irse por las ramas. Durante el desarrollo se pueden charlar cambios, pero conviene que quede lo más definido posible al principio.

---

## Relación con los trabajos prácticos

El final **no es una extensión del TP2**. Los TP son ejercicios acotados con consigna cerrada; el final es un proyecto propio, con un problema que eligen ustedes y una arquitectura que tienen que justificar.

Dicho eso, los dos TP dejan material aprovechable: el TP1 ejercita procesos, señales e IPC, y el TP2 asincronismo y colas de tareas. Un final puede retomar ideas de ahí, pero tiene que resolver un problema distinto y con decisiones propias.

---

*Computación II - 2026*
