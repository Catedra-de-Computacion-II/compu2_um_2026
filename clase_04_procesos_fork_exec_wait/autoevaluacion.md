# Clase 4: Procesos - fork, exec, wait — Autoevaluación

> Respondé estas preguntas para verificar tu comprensión.

---

## Parte 1: fork

**Pregunta 1.** ¿Qué retorna `os.fork()` en el proceso padre?

a) 0
b) El PID del hijo
c) El PID del padre
d) None

**Pregunta 2.** ¿Qué retorna `os.fork()` en el proceso hijo?

a) 0
b) El PID del hijo
c) El PID del padre
d) -1

**Pregunta 3.** Después de un `fork()` exitoso, ¿cuántos procesos están ejecutando código?

a) 1
b) 2
c) Depende
d) Ninguno

**Pregunta 4.** ¿Qué es Copy-on-Write?

a) Una técnica para evitar copiar memoria al hacer fork hasta que sea necesario
b) Un sistema de logs
c) Un tipo de archivo
d) Un tipo de lock

---

## Parte 2: exec

**Pregunta 5.** ¿Qué hace `os.execvp(comando, args)` en el proceso actual?

a) Crea un nuevo proceso
b) Reemplaza el programa del proceso actual con el comando indicado
c) Espera a que el comando termine
d) Hace fork

**Pregunta 6.** Después de un `exec` exitoso, ¿qué PID tiene el proceso?

a) El PID del comando ejecutado
b) Un PID nuevo
c) El mismo PID que antes del exec
d) 0

**Pregunta 7.** ¿Qué letra de las variantes de exec indica que se busca en PATH?

a) `l`
b) `v`
c) `p`
d) `e`

---

## Parte 3: wait

**Pregunta 8.** ¿Qué es un proceso zombie?

a) Un proceso que consume mucha CPU
b) Un proceso que terminó pero cuyo padre todavía no recogió su estado
c) Un proceso suspendido
d) Un proceso sin padre

**Pregunta 9.** ¿Cómo se previene la creación de zombies?

a) Matando al hijo
b) Llamando a `wait()` o `waitpid()` en el padre
c) Reiniciando el sistema
d) Usando `kill -9`

**Pregunta 10.** ¿Qué hace `os.wait()`?

a) Espera N segundos
b) Bloquea hasta que cualquier hijo termine y devuelve su PID y status
c) Hace dormir al proceso
d) Mata al hijo

**Pregunta 11.** ¿Qué hace `os.waitpid(pid, 0)`?

a) Mata al proceso pid
b) Espera al proceso pid específico (bloquea hasta que termine)
c) Suspende al proceso pid
d) Verifica si pid existe

**Pregunta 12.** ¿Qué hace `os.waitpid(-1, os.WNOHANG)`?

a) Mata todos los procesos
b) Verifica si algún hijo terminó sin bloquear; devuelve (0, 0) si ninguno
c) Espera al padre
d) Espera a todos los hijos en paralelo

---

## Parte 4: patrón fork-exec

**Pregunta 13.** ¿Por qué `cd` en un shell no debe implementarse con fork+exec?

a) Porque cd no existe como ejecutable
b) Porque `cd` debe cambiar el directorio del shell mismo, no del hijo
c) Porque es muy lento
d) Por razones de seguridad

**Pregunta 14.** ¿Qué pasa si `exec` falla?

a) Mata el proceso
b) Retorna -1 y el código sigue ejecutándose en el mismo proceso
c) Reinicia el sistema
d) Crea un nuevo proceso

**Pregunta 15.** En el patrón fork-exec, ¿en cuál de los dos procesos se llama a `exec`?

a) En el padre
b) En el hijo
c) En ambos
d) En ninguno; exec se llama antes del fork

---

## Respuestas

<details>
<summary>Click para ver respuestas</summary>

| # | Resp | Explicación |
|---|------|-------------|
| 1 | b | El PID del hijo |
| 2 | a | 0 |
| 3 | b | El padre y el hijo, en paralelo |
| 4 | a | Técnica para no copiar memoria hasta que alguien escriba |
| 5 | b | Reemplaza el programa del proceso actual |
| 6 | c | El mismo PID (exec no cambia el PID) |
| 7 | c | `p` (path) |
| 8 | b | Proceso terminado no recogido por el padre |
| 9 | b | El padre debe llamar a `wait()` o `waitpid()` |
| 10 | b | Bloquea hasta que cualquier hijo termine |
| 11 | b | Espera al pid específico |
| 12 | b | Verifica sin bloquear (WNOHANG) |
| 13 | b | `cd` debe cambiar el directorio del proceso shell, no de un hijo |
| 14 | b | Retorna y el código del hijo sigue ejecutando (por eso se hace `os._exit(1)` después) |
| 15 | b | En el hijo (después del fork, en la rama `pid == 0`) |

</details>

---

*Computación II - 2026 - Clase 4*
