# Clase 15: UDP - Autoevaluación

> Completá esta autoevaluación **después** de leer el contenido y hacer los ejercicios.
> No mires las respuestas antes de intentarlo.

---

## Parte 1: La API

**Pregunta 1.** ¿Qué constante crea un socket UDP?

a) `SOCK_RAW`
b) `SOCK_DGRAM`
c) `SOCK_UDP`
d) `SOCK_STREAM`

**Pregunta 2.** ¿Qué llamadas de TCP desaparecen en un servidor UDP?

a) `bind()` y `close()`
b) `socket()` y `bind()`
c) Ninguna, son iguales
d) `listen()` y `accept()`

**Pregunta 3.** ¿Por qué un servidor UDP no necesita un socket por cliente?

a) Porque UDP solo admite un cliente a la vez
b) Porque UDP multiplexa por PID
c) Porque no hay conexión: los datagramas llegan sueltos, cada uno con su origen
d) Porque el kernel crea los sockets automáticamente

**Pregunta 4.** ¿Qué devuelve `recvfrom()`?

a) Una tupla (datos, dirección del remitente)
b) La cantidad de bytes leídos
c) Solo los datos
d) Un socket nuevo

**Pregunta 5.** ¿Por qué un cliente UDP necesita `settimeout()` sí o sí?

a) Porque no hay cierre de conexión que detectar: sin timeout, `recvfrom()` espera para siempre
b) Porque UDP lo exige en el RFC
c) Por rendimiento
d) No lo necesita

**Pregunta 6.** ¿Hace falta `connect()` para mandar un datagrama?

a) Sí, siempre
b) Solo en IPv6
c) No: `sendto()` lleva el destino en cada llamada
d) Solo si el servidor está en otra máquina

---

## Parte 2: connect() en UDP

**Pregunta 7.** ¿Qué hace `connect()` en un socket UDP?

a) Nada, es un no-op
b) Establece una conexión con handshake de tres vías
c) Convierte el socket en TCP
d) Fija una dirección por defecto, filtra otros remitentes y habilita errores ICMP

**Pregunta 8.** Después de `connect()` en UDP, ¿cuántos paquetes se enviaron por la red?

a) Tres (el handshake)
b) Ninguno
c) Uno
d) Depende del sistema operativo

**Pregunta 9.** Con `connect()` a un puerto donde no hay nadie, `recv()` lanza:

a) `ConnectionRefusedError`, gracias al ICMP port unreachable
b) `TimeoutError`
c) `BrokenPipeError`
d) Nada, devuelve `b''`

**Pregunta 10.** ¿Por qué no conviene depender de ese mecanismo en Internet?

a) Porque Python no lo implementa bien
b) Porque solo funciona en IPv6
c) Porque es lento
d) Porque muchos firewalls filtran ICMP

---

## Parte 3: Datagramas y límites

**Pregunta 11.** Un cliente hace tres `sendto()` de 4, 4 y 5 bytes. ¿Qué lee el servidor?

a) Tres `recvfrom()` de 4, 4 y 5 bytes
b) Cualquier partición de los 13 bytes
c) Depende del MTU
d) Un `recvfrom()` de 13 bytes

**Pregunta 12.** Llega un datagrama de 100 bytes y hacés `recvfrom(10)`. ¿Qué pasa con los otros 90?

a) Se fragmentan en otro datagrama
b) Se descartan silenciosamente
c) Lanza una excepción
d) Quedan en el buffer para el próximo `recvfrom()`

**Pregunta 13.** ¿Qué tamaño de buffer conviene pasarle a `recvfrom()`?

a) 512 bytes
b) El tamaño exacto del mensaje esperado
c) 1472 bytes
d) 65535, el datagrama más grande posible

**Pregunta 14.** ¿Cuántos bytes de payload UDP entran en una trama Ethernet sin fragmentar?

a) 1500
b) 512
c) 1472 (1500 menos 20 de IP y 8 de UDP)
d) 65507

**Pregunta 15.** Si un datagrama se fragmenta en 10 paquetes y se pierde uno:

a) UDP retransmite el datagrama
b) Se pierde el datagrama entero
c) IP retransmite el fragmento faltante
d) Llegan los otros 9 y se reconstruye parcialmente

**Pregunta 16.** ¿Por qué DNS usa 512 bytes por defecto?

a) Por compatibilidad con IPv6
b) Para mantenerse debajo del MTU y evitar fragmentación
c) Porque las respuestas nunca son más grandes
d) Es el máximo que permite UDP

---

## Parte 4: Confiabilidad

**Pregunta 17.** ¿Qué recibe el emisor cuando un datagrama se pierde?

a) Un ICMP
b) Nada: no puede distinguir un envío exitoso de uno perdido
c) Un ACK negativo
d) Un error de red

**Pregunta 18.** Un cliente reintenta porque no recibió respuesta. ¿Qué se perdió?

a) Depende del timeout
b) Seguro su pedido
c) Seguro la respuesta
d) No puede saberlo: pudo ser cualquiera de los dos

**Pregunta 19.** ¿Por qué eso es un problema?

a) No es un problema
b) Porque si se perdió la respuesta, el servidor ya procesó el pedido y al reintentar lo procesa dos veces
c) Porque desperdicia ancho de banda
d) Porque el timeout se duplica

**Pregunta 20.** ¿Para qué sirven los números de secuencia?

a) Para ordenar los datagramas por tamaño
b) Para que el servidor descarte duplicados y el cliente identifique a qué pedido corresponde cada respuesta
c) Para calcular el checksum
d) Para cifrar el contenido

**Pregunta 21.** En `struct.pack('!I', seq)`, ¿qué indica el `!`?

a) Que el campo es obligatorio
b) Que se debe comprimir
c) Orden de bytes de red (big-endian)
d) Que el entero tiene signo

**Pregunta 22.** Si implementás ventana deslizante, control de flujo y control de congestión sobre UDP:

a) UDP no lo permite
b) Estás reimplementando TCP, probablemente peor
c) Obtenés algo más rápido que TCP siempre
d) Es la práctica recomendada

**Pregunta 23.** ¿Cómo resuelve un videojuego en red el problema de los paquetes perdidos?

a) Ignora el problema
b) Manda el estado completo cada tick, así el siguiente paquete ya trae la información actualizada
c) Retransmite todo
d) Usa TCP para lo importante

---

## Parte 5: Broadcast, multicast y elección

**Pregunta 24.** ¿Qué hace falta antes de enviar a `255.255.255.255`?

a) `setsockopt(SOL_SOCKET, SO_BROADCAST, 1)`
b) Nada
c) Un `connect()` previo
d) Permisos de root

**Pregunta 25.** ¿Por qué TCP no puede hacer broadcast?

a) Sí puede
b) Porque el kernel lo prohíbe
c) Porque una conexión es punto a punto por definición
d) Por una limitación de la implementación

**Pregunta 26.** ¿Hasta dónde llega un broadcast?

a) Solo a la propia máquina
b) Hasta el borde de la red local: los routers no lo reenvían
c) A las máquinas del mismo puerto
d) A toda Internet

**Pregunta 27.** ¿Qué rango de direcciones está reservado para multicast?

a) 127.0.0.0/8
b) 192.168.0.0/16
c) 10.0.0.0/8
d) 224.0.0.0 a 239.255.255.255

**Pregunta 28.** ¿Cuál es la ventaja de multicast sobre broadcast?

a) Solo lo reciben quienes se suscribieron al grupo
b) No necesita `setsockopt`
c) Atraviesa routers siempre
d) Es más rápido

**Pregunta 29.** ¿Cuál de estos casos conviene en UDP?

a) Transferir un archivo de 2 GB
b) Una transacción bancaria
c) Audio en tiempo real
d) Una sesión SSH

**Pregunta 30.** ¿Qué es el head-of-line blocking y por qué importa acá?

a) Un bug de TCP
b) Un límite del MTU
c) Un problema exclusivo de UDP
d) Que TCP frena todo lo que viene atrás mientras retransmite un dato viejo, lo cual arruina audio y video

---

## Respuestas

<details>
<summary>Ver respuestas (intentá primero)</summary>

| # | Respuesta | Comentario |
|---|-----------|------------|
| 1 | b | `SOCK_DGRAM` |
| 2 | d | No hay conexión que aceptar |
| 3 | c | Cada datagrama trae su origen |
| 4 | a | Datos más dirección del remitente |
| 5 | a | Sin cierre que detectar, espera para siempre |
| 6 | c | El destino va en cada `sendto()` |
| 7 | d | No conecta: fija destino y filtra |
| 8 | b | Ninguno: es puramente local |
| 9 | a | El ICMP llega como excepción |
| 10 | d | El filtrado de ICMP es habitual |
| 11 | a | UDP preserva los límites |
| 12 | b | Se descartan; no quedan para después |
| 13 | d | 65535 siempre alcanza |
| 14 | c | 1500 - 20 - 8 |
| 15 | b | Un fragmento perdido mata el datagrama |
| 16 | b | Evitar fragmentación |
| 17 | b | El emisor no se entera |
| 18 | d | Ambigüedad inherente |
| 19 | b | Procesamiento duplicado |
| 20 | b | Deduplicar e identificar respuestas |
| 21 | c | Orden de red, igual que en la clase 13 |
| 22 | b | Terminás reimplementando TCP |
| 23 | b | Diseñar para que perder no importe |
| 24 | a | `SO_BROADCAST` explícito |
| 25 | c | Punto a punto por definición |
| 26 | b | No cruza routers |
| 27 | d | 224.0.0.0/4 |
| 28 | a | Solo los suscriptos |
| 29 | c | El dato viejo no sirve |
| 30 | d | Por eso audio y video usan UDP |

</details>

---

## Resultado de la autoevaluación

| Puntaje | Diagnóstico |
|---------|-------------|
| 27-30 correctas | Excelente. Avanzá a la clase 16 (IPv6) |
| 21-26 | Buen nivel. Repasá los temas donde fallaste |
| 14-20 | Nivel intermedio. Rehacé el ejercicio 3 (protocolo confiable) |
| < 14 | Repasá el contenido completo. Consultá con el docente antes de la próxima clase |

> Las preguntas 11 a 13 y 17 a 20 son el núcleo: los límites del datagrama y el costo de la confiabilidad. Si fallaste varias de esas, volvé sobre ellas aunque el total te haya dado bien.

---

*Computación II - 2026 - Clase 15*
