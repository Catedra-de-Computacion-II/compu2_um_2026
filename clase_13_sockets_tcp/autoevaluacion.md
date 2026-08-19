# Clase 13: Sockets TCP - Autoevaluación

> Completá esta autoevaluación **después** de leer el contenido y hacer los ejercicios.
> No mires las respuestas antes de intentarlo.

---

## Parte 1: La API

**Pregunta 1.** ¿Qué idea introdujo Berkeley en 4.2BSD que hizo exitosa la API de sockets?

a) Hacer todas las operaciones asincrónicas
b) Tratar una conexión de red como un descriptor de archivo
c) Eliminar la necesidad de direcciones IP
d) Cifrar las conexiones por defecto

**Pregunta 2.** ¿Qué crea `socket.socket(socket.AF_INET, socket.SOCK_STREAM)`?

a) Un socket UDP sobre IPv4
b) Un socket local Unix
c) Un socket TCP sobre IPv4
d) Un socket TCP sobre IPv6

**Pregunta 3.** ¿Qué combinación corresponde a UDP sobre IPv6?

a) `AF_INET6`, `SOCK_STREAM`
b) `AF_UNIX`, `SOCK_DGRAM`
c) `AF_INET`, `SOCK_STREAM`
d) `AF_INET6`, `SOCK_DGRAM`

**Pregunta 4.** ¿Cuál es el orden correcto de llamadas en un servidor TCP?

a) `socket`, `listen`, `bind`, `accept`
b) `socket`, `bind`, `accept`, `listen`
c) `socket`, `accept`, `bind`, `listen`
d) `socket`, `bind`, `listen`, `accept`

**Pregunta 5.** ¿Qué devuelve `accept()`?

a) El mismo socket, ya conectado
b) El descriptor de archivo del cliente
c) Una tupla (socket nuevo, dirección del cliente)
d) Los datos enviados por el cliente

**Pregunta 6.** Después de `accept()`, ¿por cuál socket se le mandan datos al cliente?

a) Por el socket que escucha
b) Hay que crear un tercero
c) Por el socket nuevo que devolvió `accept()`
d) Por cualquiera de los dos, es indistinto

**Pregunta 7.** ¿Qué significa el argumento de `listen(5)`?

a) Espera 5 segundos por conexión
b) Reintenta 5 veces si falla
c) Acepta como máximo 5 clientes en total
d) Tamaño de la cola de conexiones pendientes de `accept()`

**Pregunta 8.** ¿Para qué sirve `SO_REUSEADDR` y cuándo hay que aplicarlo?

a) Para reutilizar el socket tras cerrarlo; antes del `listen()`
b) Para compartir el puerto entre procesos; después del `bind()`
c) Para poder hacer `bind()` aunque haya conexiones en TIME_WAIT; antes del `bind()`
d) Para permitir varias IPs; después del `listen()`

---

## Parte 2: recv y send

**Pregunta 9.** ¿Qué devuelve `recv(4096)`?

a) Exactamente 4096 bytes, siempre
b) Una línea completa de hasta 4096 bytes
c) Como máximo 4096 bytes; puede devolver menos
d) Como mínimo 4096 bytes

**Pregunta 10.** `recv()` devuelve `b''`. ¿Qué significa?

a) El otro extremo cerró la conexión
b) Hubo un error de red
c) Llegó un mensaje vacío
d) Venció el timeout

**Pregunta 11.** ¿Qué le pasa a un `while True` que llama a `recv()` sin chequear el caso anterior?

a) Se bloquea sin consumir CPU
b) Lanza una excepción
c) Termina normalmente
d) Gira infinitamente consumiendo 100% de CPU

**Pregunta 12.** ¿Cuál es la diferencia entre `send()` y `sendall()`?

a) `sendall()` es más lento pero cifra los datos
b) Ninguna, son sinónimos
c) `send()` puede enviar menos bytes de los pedidos y devuelve cuántos mandó
d) `send()` es para TCP y `sendall()` para UDP

**Pregunta 13.** Hacés `send()` de 10 MB. ¿Qué es lo más probable?

a) Envía los 10 MB completos
b) Lanza una excepción por tamaño
c) Envía una fracción y devuelve ese número
d) Bloquea hasta enviar todo

**Pregunta 14.** ¿Qué hace `s.shutdown(socket.SHUT_WR)`?

a) Descarta los datos pendientes
b) Apaga el servidor
c) Cierra solo el sentido de escritura: avisa que no manda más, pero sigue recibiendo
d) Cierra el socket completamente

---

## Parte 3: Framing

**Pregunta 15.** Un cliente hace tres `sendall()` de 4, 4 y 5 bytes. ¿Qué puede leer el servidor?

a) Cualquier partición de los 13 bytes, incluido un solo `recv()`
b) Los tres mensajes en cualquier orden
c) Siempre un solo `recv()` de 13 bytes
d) Exactamente tres `recv()` de 4, 4 y 5 bytes

**Pregunta 16.** ¿Por qué TCP no preserva los límites de los mensajes?

a) Solo pasa en redes lentas
b) Porque el buffer del kernel es muy chico
c) Es un bug conocido de la implementación
d) Porque su contrato es entregar un flujo de bytes ordenado y confiable, no mensajes

**Pregunta 17.** ¿Qué es el framing?

a) El encapsulamiento entre capas
b) La técnica de reconstruir límites de mensajes sobre un flujo de bytes
c) Un algoritmo de compresión de TCP
d) La fragmentación de paquetes IP

**Pregunta 18.** ¿Cuál es la desventaja principal del framing por delimitador?

a) Requiere saber el tamaño de antemano
b) Hay que escapar o prohibir el delimitador dentro del contenido
c) No funciona con conexiones largas
d) Es más lento

**Pregunta 19.** En el framing por longitud, ¿por qué hace falta una función `recibir_exacto()`?

a) Porque `recv()` no acepta argumentos
b) Por elegancia del código
c) Porque `recv(n)` puede devolver menos de n bytes y el protocolo se desincronizaría
d) Para poder usar timeouts

**Pregunta 20.** Necesitás mandar imágenes por un socket. ¿Qué framing conviene?

a) Delimitador de espacio
b) Ninguno, TCP ya delimita
c) Delimitador `\n`
d) Prefijo de longitud

**Pregunta 21.** ¿Qué significa el `!` en `struct.pack('!I', n)`?

a) Que se debe invertir el entero
b) Que el valor es obligatorio
c) Que es un entero con signo
d) Orden de bytes de red (big-endian)

**Pregunta 22.** ¿Por qué existe la convención de orden de bytes de red?

a) Porque IP lo exige a nivel de hardware
b) Porque las arquitecturas difieren en cómo guardan enteros y hace falta un acuerdo
c) Por compatibilidad con IPv6
d) Porque big-endian es más rápido

---

## Parte 4: Datos y errores

**Pregunta 23.** ¿Qué pasa con `s.sendall('hola')`?

a) Envía solo el primer carácter
b) Funciona normalmente
c) Lanza `TypeError`: los sockets mandan bytes, no strings
d) Envía el string en ASCII

**Pregunta 24.** `'año'` tiene 3 caracteres. ¿Cuántos bytes ocupa en UTF-8?

a) 3
b) 6
c) 4
d) Depende del sistema operativo

**Pregunta 25.** ¿Por qué conviene decodificar mensajes completos y no cada `recv()`?

a) Porque `decode()` es lento
b) Por rendimiento
c) Porque un carácter multibyte puede quedar partido entre dos `recv()`
d) Porque `recv()` ya devuelve strings

**Pregunta 26.** ¿Qué excepción da conectarse a un puerto donde nadie escucha?

a) `BrokenPipeError`
b) `TimeoutError`
c) `OSError` Errno 98
d) `ConnectionRefusedError`

**Pregunta 27.** ¿Qué excepción da escribir en una conexión que el otro lado ya cerró?

a) `ConnectionRefusedError`
b) Ninguna, se descarta en silencio
c) `TimeoutError`
d) `BrokenPipeError`

**Pregunta 28.** ¿Cuál es el comportamiento por defecto de un socket sin `settimeout()`?

a) No bloquea nunca
b) Timeout de 30 segundos
c) Timeout de 5 minutos
d) Bloquea indefinidamente

---

## Parte 5: El servidor secuencial

**Pregunta 29.** El servidor eco de la clase atiende un cliente a la vez. Mientras atiende al primero, un segundo cliente hace `connect()`. ¿Qué pasa?

a) El servidor se cae
b) Se conecta y es atendido en paralelo
c) El `connect()` tiene éxito y la conexión queda `ESTAB`, esperando en la cola de `listen()`
d) Recibe `ConnectionRefusedError` inmediatamente

**Pregunta 30.** Siguiendo la anterior, ¿quién completó el handshake de ese segundo cliente?

a) Nadie: el handshake queda a medias
b) El bucle del servidor, antes de bloquearse
c) El kernel, con independencia de que la aplicación llame a `accept()`
d) El propio cliente

**Pregunta 31.** ¿Cuál de estas NO es una forma de resolver la limitación del servidor secuencial?

a) Un thread por cliente
b) Un proceso por cliente
c) Multiplexar con `select()`
d) Aumentar el `listen()` a un número grande

**Pregunta 32.** ¿Por qué "el cliente conectó bien" no implica "el servidor lo está atendiendo"?

a) La afirmación sí implica lo otro
b) Porque TCP no confirma las conexiones
c) Porque el cliente puede mentir
d) Porque el kernel acepta la conexión y la encola; la aplicación puede tardar en llamar a `accept()`

---

## Respuestas

<details>
<summary>Ver respuestas (intentá primero)</summary>

| # | Respuesta | Comentario |
|---|-----------|------------|
| 1 | b | Todo lo que sabías de archivos siguió valiendo |
| 2 | c | `AF_INET` + `SOCK_STREAM` = TCP/IPv4 |
| 3 | d | `AF_INET6` + `SOCK_DGRAM` |
| 4 | d | bind reclama, listen abre la cola, accept toma |
| 5 | c | Socket NUEVO más dirección |
| 6 | c | El que escucha nunca transmite datos |
| 7 | d | Tamaño de la cola de pendientes |
| 8 | c | Antes del bind; si no, no tiene efecto |
| 9 | c | Es un tope, no una cantidad pedida |
| 10 | a | Señal de cierre del otro extremo |
| 11 | d | El bug número uno de quien empieza |
| 12 | c | Por eso se usa `sendall()` |
| 13 | c | Verificado en el ejercicio: manda una fracción |
| 14 | c | Cierre de media conexión; el otro ve `b''` |
| 15 | a | TCP es un flujo, no mensajes |
| 16 | d | Es su contrato, no un defecto |
| 17 | b | Lo pone la aplicación, no el protocolo |
| 18 | b | Hay que escapar el delimitador |
| 19 | c | Sin el bucle, el protocolo se desincroniza |
| 20 | d | Binario arbitrario: longitud |
| 21 | d | Big-endian, orden de red |
| 22 | b | Little vs big endian según arquitectura |
| 23 | c | Python 3 es estricto con bytes |
| 24 | c | La `ñ` ocupa 2 bytes |
| 25 | c | El carácter partido rompe `decode()` |
| 26 | d | `ConnectionRefusedError` |
| 27 | d | `BrokenPipeError` |
| 28 | d | Bloquea para siempre |
| 29 | c | El handshake ya ocurrió; falta el `accept()` |
| 30 | c | El kernel, no la aplicación |
| 31 | d | Agranda la cola pero no atiende más rápido |
| 32 | d | Conectado no es lo mismo que atendido |

</details>

---

## Resultado de la autoevaluación

| Puntaje | Diagnóstico |
|---------|-------------|
| 29-32 correctas | Excelente. Avanzá a la clase 14 (Servidores concurrentes) |
| 23-28 | Buen nivel. Repasá los temas donde fallaste |
| 16-22 | Nivel intermedio. Rehacé el ejercicio 3 (framing) y el 2 (recv) |
| < 16 | Repasá el contenido completo. Consultá con el docente antes de la próxima clase |

> Las preguntas 9 a 11 y 15 a 19 son el núcleo de la clase. Si fallaste varias de esas, el resto del bloque de redes se te va a hacer cuesta arriba: volvé sobre ellas aunque el total te haya dado bien.

---

*Computación II - 2026 - Clase 13*
