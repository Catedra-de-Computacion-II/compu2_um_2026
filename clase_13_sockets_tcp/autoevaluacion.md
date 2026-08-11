# Clase 13: Sockets TCP - Autoevaluación

> Completá esta autoevaluación **después** de leer el contenido y hacer los ejercicios.
> No mires las respuestas antes de intentarlo.

---

## Parte 1: La API

**Pregunta 1.** ¿Qué idea introdujo Berkeley en 4.2BSD que hizo exitosa la API de sockets?

a) Cifrar las conexiones por defecto
b) Tratar una conexión de red como un descriptor de archivo
c) Eliminar la necesidad de direcciones IP
d) Hacer todas las operaciones asincrónicas

**Pregunta 2.** ¿Qué crea `socket.socket(socket.AF_INET, socket.SOCK_STREAM)`?

a) Un socket UDP sobre IPv4
b) Un socket TCP sobre IPv4
c) Un socket TCP sobre IPv6
d) Un socket local Unix

**Pregunta 3.** ¿Qué combinación corresponde a UDP sobre IPv6?

a) `AF_INET`, `SOCK_STREAM`
b) `AF_INET6`, `SOCK_STREAM`
c) `AF_INET6`, `SOCK_DGRAM`
d) `AF_UNIX`, `SOCK_DGRAM`

**Pregunta 4.** ¿Cuál es el orden correcto de llamadas en un servidor TCP?

a) `socket`, `listen`, `bind`, `accept`
b) `socket`, `bind`, `listen`, `accept`
c) `socket`, `accept`, `bind`, `listen`
d) `socket`, `bind`, `accept`, `listen`

**Pregunta 5.** ¿Qué devuelve `accept()`?

a) Los datos enviados por el cliente
b) Una tupla (socket nuevo, dirección del cliente)
c) El mismo socket, ya conectado
d) El descriptor de archivo del cliente

**Pregunta 6.** Después de `accept()`, ¿por cuál socket se le mandan datos al cliente?

a) Por el socket que escucha
b) Por el socket nuevo que devolvió `accept()`
c) Por cualquiera de los dos, es indistinto
d) Hay que crear un tercero

**Pregunta 7.** ¿Qué significa el argumento de `listen(5)`?

a) Acepta como máximo 5 clientes en total
b) Tamaño de la cola de conexiones pendientes de `accept()`
c) Espera 5 segundos por conexión
d) Reintenta 5 veces si falla

**Pregunta 8.** ¿Para qué sirve `SO_REUSEADDR` y cuándo hay que aplicarlo?

a) Para compartir el puerto entre procesos; después del `bind()`
b) Para poder hacer `bind()` aunque haya conexiones en TIME_WAIT; antes del `bind()`
c) Para reutilizar el socket tras cerrarlo; antes del `listen()`
d) Para permitir varias IPs; después del `listen()`

---

## Parte 2: recv y send

**Pregunta 9.** ¿Qué devuelve `recv(4096)`?

a) Exactamente 4096 bytes, siempre
b) Como máximo 4096 bytes; puede devolver menos
c) Como mínimo 4096 bytes
d) Una línea completa de hasta 4096 bytes

**Pregunta 10.** `recv()` devuelve `b''`. ¿Qué significa?

a) Llegó un mensaje vacío
b) El otro extremo cerró la conexión
c) Hubo un error de red
d) Venció el timeout

**Pregunta 11.** ¿Qué le pasa a un `while True` que llama a `recv()` sin chequear el caso anterior?

a) Termina normalmente
b) Gira infinitamente consumiendo 100% de CPU
c) Lanza una excepción
d) Se bloquea sin consumir CPU

**Pregunta 12.** ¿Cuál es la diferencia entre `send()` y `sendall()`?

a) Ninguna, son sinónimos
b) `send()` puede enviar menos bytes de los pedidos y devuelve cuántos mandó
c) `sendall()` es más lento pero cifra los datos
d) `send()` es para TCP y `sendall()` para UDP

**Pregunta 13.** Hacés `send()` de 10 MB. ¿Qué es lo más probable?

a) Envía los 10 MB completos
b) Envía una fracción y devuelve ese número
c) Lanza una excepción por tamaño
d) Bloquea hasta enviar todo

**Pregunta 14.** ¿Qué hace `s.shutdown(socket.SHUT_WR)`?

a) Cierra el socket completamente
b) Cierra solo el sentido de escritura: avisa que no manda más, pero sigue recibiendo
c) Apaga el servidor
d) Descarta los datos pendientes

---

## Parte 3: Framing

**Pregunta 15.** Un cliente hace tres `sendall()` de 4, 4 y 5 bytes. ¿Qué puede leer el servidor?

a) Exactamente tres `recv()` de 4, 4 y 5 bytes
b) Cualquier partición de los 13 bytes, incluido un solo `recv()`
c) Siempre un solo `recv()` de 13 bytes
d) Los tres mensajes en cualquier orden

**Pregunta 16.** ¿Por qué TCP no preserva los límites de los mensajes?

a) Es un bug conocido de la implementación
b) Porque su contrato es entregar un flujo de bytes ordenado y confiable, no mensajes
c) Porque el buffer del kernel es muy chico
d) Solo pasa en redes lentas

**Pregunta 17.** ¿Qué es el framing?

a) Un algoritmo de compresión de TCP
b) La técnica de reconstruir límites de mensajes sobre un flujo de bytes
c) El encapsulamiento entre capas
d) La fragmentación de paquetes IP

**Pregunta 18.** ¿Cuál es la desventaja principal del framing por delimitador?

a) Es más lento
b) Hay que escapar o prohibir el delimitador dentro del contenido
c) No funciona con conexiones largas
d) Requiere saber el tamaño de antemano

**Pregunta 19.** En el framing por longitud, ¿por qué hace falta una función `recibir_exacto()`?

a) Por elegancia del código
b) Porque `recv(n)` puede devolver menos de n bytes y el protocolo se desincronizaría
c) Porque `recv()` no acepta argumentos
d) Para poder usar timeouts

**Pregunta 20.** Necesitás mandar imágenes por un socket. ¿Qué framing conviene?

a) Delimitador `\n`
b) Prefijo de longitud
c) Delimitador de espacio
d) Ninguno, TCP ya delimita

**Pregunta 21.** ¿Qué significa el `!` en `struct.pack('!I', n)`?

a) Que el valor es obligatorio
b) Orden de bytes de red (big-endian)
c) Que se debe invertir el entero
d) Que es un entero con signo

**Pregunta 22.** ¿Por qué existe la convención de orden de bytes de red?

a) Porque big-endian es más rápido
b) Porque las arquitecturas difieren en cómo guardan enteros y hace falta un acuerdo
c) Porque IP lo exige a nivel de hardware
d) Por compatibilidad con IPv6

---

## Parte 4: Datos y errores

**Pregunta 23.** ¿Qué pasa con `s.sendall('hola')`?

a) Funciona normalmente
b) Lanza `TypeError`: los sockets mandan bytes, no strings
c) Envía el string en ASCII
d) Envía solo el primer carácter

**Pregunta 24.** `'año'` tiene 3 caracteres. ¿Cuántos bytes ocupa en UTF-8?

a) 3
b) 4
c) 6
d) Depende del sistema operativo

**Pregunta 25.** ¿Por qué conviene decodificar mensajes completos y no cada `recv()`?

a) Por rendimiento
b) Porque un carácter multibyte puede quedar partido entre dos `recv()`
c) Porque `decode()` es lento
d) Porque `recv()` ya devuelve strings

**Pregunta 26.** ¿Qué excepción da conectarse a un puerto donde nadie escucha?

a) `TimeoutError`
b) `ConnectionRefusedError`
c) `BrokenPipeError`
d) `OSError` Errno 98

**Pregunta 27.** ¿Qué excepción da escribir en una conexión que el otro lado ya cerró?

a) `ConnectionRefusedError`
b) `BrokenPipeError`
c) `TimeoutError`
d) Ninguna, se descarta en silencio

**Pregunta 28.** ¿Cuál es el comportamiento por defecto de un socket sin `settimeout()`?

a) Timeout de 30 segundos
b) Bloquea indefinidamente
c) No bloquea nunca
d) Timeout de 5 minutos

---

## Parte 5: El servidor secuencial

**Pregunta 29.** El servidor eco de la clase atiende un cliente a la vez. Mientras atiende al primero, un segundo cliente hace `connect()`. ¿Qué pasa?

a) Recibe `ConnectionRefusedError` inmediatamente
b) El `connect()` tiene éxito y la conexión queda `ESTAB`, esperando en la cola de `listen()`
c) Se conecta y es atendido en paralelo
d) El servidor se cae

**Pregunta 30.** Siguiendo la anterior, ¿quién completó el handshake de ese segundo cliente?

a) El bucle del servidor, antes de bloquearse
b) El kernel, con independencia de que la aplicación llame a `accept()`
c) Nadie: el handshake queda a medias
d) El propio cliente

**Pregunta 31.** ¿Cuál de estas NO es una forma de resolver la limitación del servidor secuencial?

a) Un thread por cliente
b) Un proceso por cliente
c) Aumentar el `listen()` a un número grande
d) Multiplexar con `select()`

**Pregunta 32.** ¿Por qué "el cliente conectó bien" no implica "el servidor lo está atendiendo"?

a) Porque el cliente puede mentir
b) Porque el kernel acepta la conexión y la encola; la aplicación puede tardar en llamar a `accept()`
c) Porque TCP no confirma las conexiones
d) La afirmación sí implica lo otro

---

## Respuestas

<details>
<summary>Ver respuestas (intentá primero)</summary>

| # | Respuesta | Comentario |
|---|-----------|------------|
| 1 | b | Todo lo que sabías de archivos siguió valiendo |
| 2 | b | `AF_INET` + `SOCK_STREAM` = TCP/IPv4 |
| 3 | c | `AF_INET6` + `SOCK_DGRAM` |
| 4 | b | bind reclama, listen abre la cola, accept toma |
| 5 | b | Socket NUEVO más dirección |
| 6 | b | El que escucha nunca transmite datos |
| 7 | b | Tamaño de la cola de pendientes |
| 8 | b | Antes del bind; si no, no tiene efecto |
| 9 | b | Es un tope, no una cantidad pedida |
| 10 | b | Señal de cierre del otro extremo |
| 11 | b | El bug número uno de quien empieza |
| 12 | b | Por eso se usa `sendall()` |
| 13 | b | Verificado en el ejercicio: manda una fracción |
| 14 | b | Cierre de media conexión; el otro ve `b''` |
| 15 | b | TCP es un flujo, no mensajes |
| 16 | b | Es su contrato, no un defecto |
| 17 | b | Lo pone la aplicación, no el protocolo |
| 18 | b | Hay que escapar el delimitador |
| 19 | b | Sin el bucle, el protocolo se desincroniza |
| 20 | b | Binario arbitrario: longitud |
| 21 | b | Big-endian, orden de red |
| 22 | b | Little vs big endian según arquitectura |
| 23 | b | Python 3 es estricto con bytes |
| 24 | b | La `ñ` ocupa 2 bytes |
| 25 | b | El carácter partido rompe `decode()` |
| 26 | b | `ConnectionRefusedError` |
| 27 | b | `BrokenPipeError` |
| 28 | b | Bloquea para siempre |
| 29 | b | El handshake ya ocurrió; falta el `accept()` |
| 30 | b | El kernel, no la aplicación |
| 31 | c | Agranda la cola pero no atiende más rápido |
| 32 | b | Conectado no es lo mismo que atendido |

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
