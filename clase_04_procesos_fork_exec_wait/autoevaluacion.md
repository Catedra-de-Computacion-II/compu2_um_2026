# Clase 4: Procesos - fork, exec, wait — Autoevaluación

> Respondé estas preguntas para verificar tu comprensión.

---

## Parte 1: fork

**Pregunta 1.** ¿Qué retorna `os.fork()` en el proceso padre?

a) El PID del hijo
b) 0
c) None
d) El PID del padre

**Pregunta 2.** ¿Qué retorna `os.fork()` en el proceso hijo?

a) 0
b) El PID del hijo
c) -1
d) El PID del padre

**Pregunta 3.** Después de un `fork()` exitoso, ¿cuántos procesos están ejecutando código?

a) 2
b) 1
c) Ninguno
d) Depende

**Pregunta 4.** ¿Qué es Copy-on-Write?

a) Un tipo de lock
b) Un tipo de archivo
c) Una técnica para evitar copiar memoria al hacer fork hasta que sea necesario
d) Un sistema de logs

---

## Parte 2: exec

**Pregunta 5.** ¿Qué hace `os.execvp(comando, args)` en el proceso actual?

a) Hace fork
b) Reemplaza el programa del proceso actual con el comando indicado
c) Crea un nuevo proceso
d) Espera a que el comando termine

**Pregunta 6.** Después de un `exec` exitoso, ¿qué PID tiene el proceso?

a) Un PID nuevo
b) El PID del comando ejecutado
c) 0
d) El mismo PID que antes del exec

**Pregunta 7.** ¿Qué letra de las variantes de exec indica que se busca en PATH?

a) `v`
b) `p`
c) `e`
d) `l`

---

## Parte 3: wait

**Pregunta 8.** ¿Qué es un proceso zombie?

a) Un proceso sin padre
b) Un proceso suspendido
c) Un proceso que terminó pero cuyo padre todavía no recogió su estado
d) Un proceso que consume mucha CPU

**Pregunta 9.** ¿Cómo se previene la creación de zombies?

a) Reiniciando el sistema
b) Llamando a `wait()` o `waitpid()` en el padre
c) Matando al hijo
d) Usando `kill -9`

**Pregunta 10.** ¿Qué hace `os.wait()`?

a) Bloquea hasta que cualquier hijo termine y devuelve su PID y status
b) Hace dormir al proceso
c) Espera N segundos
d) Mata al hijo

**Pregunta 11.** ¿Qué hace `os.waitpid(pid, 0)`?

a) Mata al proceso pid
b) Espera al proceso pid específico (bloquea hasta que termine)
c) Verifica si pid existe
d) Suspende al proceso pid

**Pregunta 12.** ¿Qué hace `os.waitpid(-1, os.WNOHANG)`?

a) Mata todos los procesos
b) Espera al padre
c) Espera a todos los hijos en paralelo
d) Verifica si algún hijo terminó sin bloquear; devuelve (0, 0) si ninguno

---

## Parte 4: patrón fork-exec

**Pregunta 13.** ¿Por qué `cd` en un shell no debe implementarse con fork+exec?

a) Porque es muy lento
b) Porque `cd` debe cambiar el directorio del shell mismo, no del hijo
c) Porque cd no existe como ejecutable
d) Por razones de seguridad

**Pregunta 14.** ¿Qué pasa si `exec` falla?

a) Retorna -1 y el código sigue ejecutándose en el mismo proceso
b) Mata el proceso
c) Crea un nuevo proceso
d) Reinicia el sistema

**Pregunta 15.** En el patrón fork-exec, ¿en cuál de los dos procesos se llama a `exec`?

a) En ninguno; exec se llama antes del fork
b) En el padre
c) En el hijo
d) En ambos

---

## Respuestas

<details>
<summary>Click para ver respuestas</summary>

| # | Resp | Explicación |
|---|------|-------------|
| 1 | a | El PID del hijo |
| 2 | a | 0 |
| 3 | a | El padre y el hijo, en paralelo |
| 4 | c | Técnica para no copiar memoria hasta que alguien escriba |
| 5 | b | Reemplaza el programa del proceso actual |
| 6 | d | El mismo PID (exec no cambia el PID) |
| 7 | b | `p` (path) |
| 8 | c | Proceso terminado no recogido por el padre |
| 9 | b | El padre debe llamar a `wait()` o `waitpid()` |
| 10 | a | Bloquea hasta que cualquier hijo termine |
| 11 | b | Espera al pid específico |
| 12 | d | Verifica sin bloquear (WNOHANG) |
| 13 | b | `cd` debe cambiar el directorio del proceso shell, no de un hijo |
| 14 | a | Retorna y el código del hijo sigue ejecutando (por eso se hace `os._exit(1)` después) |
| 15 | c | En el hijo (después del fork, en la rama `pid == 0`) |

</details>

---

*Computación II - 2026 - Clase 4*
