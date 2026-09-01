# Computación II - 2026

## Universidad de Mendoza - Ingeniería en Informática

### Docentes
- Ing. Gabriel Quintero
- Ing. Carlos Taffernaberry

### Información del curso
- **Código:** 2038
- **Año:** 3º (Anual)
- **Carga horaria:** 4 hs semanales (120 hs totales)
- **Día de cursado:** Martes

---

## Estructura del repositorio

```
2026/
├── README.md                    # Este archivo
├── PLANIFICACION_2026.md       # Planificación detallada del curso
│
├── bloque_0_autonomo/          # Material para estudio autónomo
│   ├── git/                    # Git y GitHub
│   ├── argparse_getopt/        # Argumentos de línea de comandos
│   ├── filesystem_linux/       # Filesystem, inodos, permisos
│   └── python_avanzado/        # Context managers, decoradores, generadores
│
├── clase_01_docker_intro/      # Presentación + Docker básico
├── clase_02_docker_aplicado/   # Volúmenes, redes, compose
├── clase_03_procesos_fundamentos/  # Modelo de proceso
├── ...                         # (24 clases en total)
│
├── trabajos_practicos/
│   ├── TP1_monitoreo/         # Sistema de monitoreo concurrente
│   └── TP2_tareas/            # Plataforma de tareas distribuidas
│
└── extra_manijas_globales/     # Material avanzado opcional
```

---

## Estructura de cada unidad

Cada clase/unidad sigue esta estructura:

```
clase_XX_tema/
├── contenido.md           # Material teórico
├── ejercicios/            # Ejercicios progresivos
│   ├── basico/
│   ├── intermedio/
│   └── avanzado/
├── extra_manijas.md       # Profundización opcional
├── autoevaluacion.md      # Quiz de autoevaluación
└── slides/                # Diapositivas (si aplica)
```

---

## Cronograma resumido

**24 clases.** El 2º término lectivo finaliza el 13/11/2026; no se dicta clase en
las semanas de mesas de exámenes (14-18/09) ni de recuperaciones (09-13/11).

### Primer cuatrimestre

| Clase | Tema |
|-------|------|
| 1-2 | Docker: introducción y aplicado |
| 3-4 | Procesos: fundamentos / fork, exec, wait |
| 5-6 | Pipes / Señales |
| 7 | mmap y memoria compartida |
| 8-9 | Multiprocessing: fundamentos y avanzado |
| 10-11 | Threading / Sincronización |
| 12-13 | Redes: fundamentos / Sockets TCP |
| 14 | Servidores concurrentes |
| 15 | UDP — **Entrega TP1** |

### Segundo cuatrimestre

| Clase | Fecha | Tema |
|-------|-------|------|
| 16 | 01/09 | socketserver |
| 17 | 08/09 | I/O Multiplexing |
| — | 15/09 | *(mesas de exámenes: sin clase)* |
| 18 | 22/09 | HTTP + FastAPI — **Enunciado TP2** |
| 19 | 29/09 | De yield a asyncio |
| 20 | 06/10 | Asyncio en red |
| 21 | 13/10 | Asyncio avanzado |
| 22 | 20/10 | concurrent.futures |
| 23 | 27/10 | Celery I |
| 24 | 03/11 | Celery II — **Entrega TP2** |
| — | 09-13/11 | *(recuperaciones y firma de regularidades)* |

> El cronograma del segundo cuatrimestre está ajustado al calendario académico de
> la Facultad de Ingeniería. IPv6 pasó a material de estudio autónomo
> (`bloque_0_autonomo/ipv6/`).

---

## Cómo usar este material

### Para estudiantes

1. **Antes de la primera clase:**
   - Completar el Bloque 0 autónomo
   - Instalar Docker y configurar entorno

2. **Antes de cada clase:**
   - Leer el contenido teórico
   - Intentar los ejercicios básicos

3. **Después de cada clase:**
   - Completar ejercicios intermedios y avanzados
   - Revisar extra manijas si te interesa profundizar
   - Hacer la autoevaluación

4. **Para los TPs:**
   - Seguir las instrucciones en cada carpeta de TP
   - Respetar las fechas de entrega

### Para docentes

Ver `PLANIFICACION_2026.md` para:
- Detalle de cada clase
- Criterios de evaluación
- Material de evaluación docente (no distribuir)

---

## Requisitos técnicos

- Python 3.10+
- Docker y Docker Compose
- Git
- Editor de código (VS Code recomendado)
- Sistema Linux o WSL2

### Instalación rápida (Ubuntu/Debian)

```bash
# Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# Python
sudo apt install python3 python3-pip python3-venv

# Herramientas adicionales
sudo apt install git build-essential
```

---

## Contacto

- **Consultas:** usar el canal de Discord/Slack del curso
- **Issues:** reportar en el repositorio de GitHub
- **Email:** solo para temas administrativos

---

*Computación II - Ciclo 2026*
