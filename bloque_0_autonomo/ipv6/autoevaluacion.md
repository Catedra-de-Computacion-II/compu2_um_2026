# Clase 16: IPv6 - Autoevaluación

> Completá esta autoevaluación **después** de leer el contenido y hacer los ejercicios.
> No mires las respuestas antes de intentarlo.

---

## Parte 1: Direcciones

**Pregunta 1.** ¿Cuántos bits tiene una dirección IPv6?

a) 64
b) 32
c) 256
d) 128

**Pregunta 2.** ¿Cuántas veces puede aparecer `::` en una dirección?

a) Todas las que haga falta
b) Una sola vez
c) Máximo dos
d) Ninguna, es opcional

**Pregunta 3.** ¿Por qué esa restricción?

a) Por compatibilidad con IPv4
b) Por rendimiento del parser
c) Porque el RFC no lo definió
d) Porque con dos sería ambiguo cuántos grupos de ceros representa cada uno

**Pregunta 4.** ¿Cuál es la forma comprimida de `2001:0db8:0000:0000:0000:ff00:0042:8329`?

a) `2001:db8:0:0:0:ff00:42:8329`
b) `2001:db8::ff00:42:8329`
c) `21:db8::ff:42:8329`
d) `2001:0db8::ff00:0042:8329`

**Pregunta 5.** ¿Qué es `::1`?

a) Una dirección inválida
b) La primera dirección de la red
c) Broadcast
d) Loopback: el equivalente de `127.0.0.1`

**Pregunta 6.** ¿Qué significa `::` sola?

a) Multicast
b) Loopback
c) Sin especificar / todas las interfaces (el `0.0.0.0` de IPv6)
d) La dirección del router

**Pregunta 7.** ¿Cómo se escribe una URL con dirección IPv6 y puerto?

a) `http://2001:db8::1:8080/`
b) `http://{2001:db8::1}:8080/`
c) `http://2001:db8::1/8080`
d) `http://[2001:db8::1]:8080/`

**Pregunta 8.** ¿Por qué IPv6 y no IPv5?

a) Se saltearon el 5 por superstición
b) El número 5 ya lo había usado un protocolo experimental de streaming
c) IPv5 falló en pruebas
d) IPv5 es la versión de pago

---

## Parte 2: Tipos y alcance

**Pregunta 9.** Una interfaz IPv6 típicamente tiene:

a) Una por cada puerto abierto
b) Varias direcciones con alcances distintos
c) Ninguna hasta que se configure DHCP
d) Exactamente una dirección

**Pregunta 10.** ¿Qué caracteriza a una dirección `fe80::`?

a) Es multicast
b) Es link-local: se autoconfigura y no sale del segmento físico
c) Es privada pero ruteable dentro de la organización
d) Es global y ruteable

**Pregunta 11.** ¿Por qué `fe80::1` sola es ambigua?

a) Porque falta el puerto
b) No es ambigua
c) Porque no está comprimida
d) Porque toda interfaz tiene una `fe80::` y hay que decir por cuál mandar

**Pregunta 12.** ¿Cómo se especifica la interfaz?

a) `fe80::1%eth0`
b) `fe80::1/eth0`
c) `eth0:fe80::1`
d) `fe80::1@eth0`

**Pregunta 13.** ¿Cuántos elementos tiene la tupla de dirección de un socket IPv6?

a) Depende del sistema
b) 2: dirección y puerto
c) 3: dirección, puerto y familia
d) 4: dirección, puerto, flowinfo y scope_id

**Pregunta 14.** ¿Qué pasa con `host, puerto = sock.getsockname()` en un socket IPv6?

a) Devuelve una tupla vacía
b) Devuelve la dirección sin el puerto
c) Funciona igual que en IPv4
d) Lanza `ValueError: too many values to unpack`

**Pregunta 15.** ¿Qué es la autoconfiguración sin estado (SLAAC)?

a) Un protocolo de enrutamiento
b) Un servidor DHCP más rápido
c) Asignación manual de direcciones
d) La máquina consigue dirección combinando el prefijo que anuncia el router con un identificador propio

---

## Parte 3: Programar con las dos familias

**Pregunta 16.** ¿Qué constante crea un socket IPv6?

a) `AF_INET`
b) `AF_INET6`
c) `AF_UNSPEC`
d) `AF_IPV6`

**Pregunta 17.** ¿Qué hace `getaddrinfo()`?

a) Consulta la tabla de ruteo
b) Configura la interfaz de red
c) Devuelve solo la IPv4 de un nombre
d) Traduce nombre y servicio a una lista de posibilidades de ambas familias, ordenadas por preferencia

**Pregunta 18.** ¿Por qué hay que iterar la lista de `getaddrinfo()` y no usar solo la primera?

a) Porque la primera siempre es inválida
b) Porque tener una dirección no garantiza que la ruta funcione: si falla hay que probar la siguiente
c) Por elegancia
d) No hace falta iterar

**Pregunta 19.** ¿Qué hace `socket.create_connection()` internamente?

a) Llama a `getaddrinfo()` y prueba las direcciones en orden
b) Usa siempre IPv6 si está disponible
c) Requiere que le pases la familia
d) Crea un socket IPv4

**Pregunta 20.** ¿Para qué sirve `IPV6_V6ONLY`?

a) Para controlar si un socket IPv6 acepta también conexiones IPv4
b) Para forzar el uso de IPv6 en el cliente
c) Para desactivar IPv4 en el sistema
d) Para validar direcciones

**Pregunta 21.** ¿Por qué hay que ponerlo explícitamente?

a) Porque si no, el bind falla
b) Porque Python lo exige
c) Porque el valor por defecto varía entre sistemas operativos
d) No hace falta ponerlo

**Pregunta 22.** Un socket dual-stack recibe una conexión IPv4 desde `192.168.1.5`. ¿Qué dirección ve el servidor?

a) `192.168.1.5`
b) `fe80::192.168.1.5`
c) `::ffff:192.168.1.5`
d) `::1`

**Pregunta 23.** ¿Por qué importa normalizar esas direcciones?

a) Por estética en los logs
b) No importa
c) Porque ocupan más espacio
d) Porque el mismo cliente aparece escrito distinto y eso rompe filtros, listas de bloqueo y estadísticas

**Pregunta 24.** ¿Cuál es la forma correcta de soportar ambas familias en un cliente?

a) Duplicar el código para cada familia
b) Un `if` que elige la familia según una variable de configuración
c) `getaddrinfo()` (o `create_connection()`) y probar en orden
d) Usar siempre IPv4 por compatibilidad

---

## Parte 4: El protocolo

**Pregunta 25.** ¿Qué tamaño tiene el encabezado IPv6?

a) Fijo, 40 bytes
b) Variable, como IPv4
c) Fijo, 128 bytes
d) Fijo, 20 bytes

**Pregunta 26.** ¿Por qué IPv6 eliminó el checksum de la capa de red?

a) Por un error de diseño
b) Porque IPv6 no puede tener errores
c) Porque las capas de arriba y abajo ya verifican, y recalcularlo en cada salto era costoso
d) Para ahorrar 2 bytes

**Pregunta 27.** ¿Qué consecuencia tuvo eso para UDP?

a) El checksum UDP, opcional en IPv4, pasó a ser obligatorio en IPv6
b) UDP no funciona sobre IPv6
c) Ninguna
d) UDP perdió el campo de longitud

**Pregunta 28.** En IPv6, ¿quién fragmenta los paquetes?

a) Cualquier router del camino
b) El receptor
c) No hay fragmentación
d) Solo el emisor; los routers responden ICMPv6 Packet Too Big

**Pregunta 29.** ¿Qué pasa si un firewall bloquea todo ICMPv6?

a) Nada, como en IPv4
b) Mejora la seguridad sin efectos secundarios
c) Solo deja de andar el ping
d) La red deja de funcionar: se rompen el descubrimiento de vecinos, la autoconfiguración y el path MTU discovery

**Pregunta 30.** ¿Cuál fue el principal parche que estiró la vida de IPv4?

a) NAT
b) DHCP
c) Subredes
d) Multicast

**Pregunta 31.** ¿Qué rompe NAT?

a) La conectividad entrante y el modelo extremo a extremo
b) El DNS
c) Los puertos efímeros
d) El enrutamiento

**Pregunta 32.** Tenés dirección IPv6 global pero `ping6` a Internet falla. ¿Qué significa?

a) La dirección es inválida
b) IPv6 está deshabilitado en el kernel
c) Falta configurar el DNS
d) Tenés dirección pero no ruta: el ISP no provee tránsito IPv6

---

## Respuestas

<details>
<summary>Ver respuestas (intentá primero)</summary>

| # | Respuesta | Comentario |
|---|-----------|------------|
| 1 | d | 128 bits contra 32 de IPv4 |
| 2 | b | Una sola vez |
| 3 | d | Dos `::` serían ambiguos |
| 4 | b | Ceros a la izquierda fuera, y `::` en la secuencia larga |
| 5 | d | El `127.0.0.1` de IPv6 |
| 6 | c | Equivale a `0.0.0.0` |
| 7 | d | Corchetes para separar del puerto |
| 8 | b | ST consumió el número 5 |
| 9 | b | Link-local siempre, global si hay router |
| 10 | b | No la reenvían los routers |
| 11 | d | Toda interfaz tiene la suya |
| 12 | a | El scope ID va con `%` |
| 13 | d | Por eso el desempaquetado en 2 rompe |
| 14 | d | `ValueError`, verificado en el ejercicio |
| 15 | d | Prefijo del router + identificador propio |
| 16 | b | `AF_INET6` |
| 17 | d | Lista de ambas familias en orden de preferencia |
| 18 | b | Dirección no implica ruta |
| 19 | a | Por eso da soporte dual gratis |
| 20 | a | Controla el dual-stack del socket |
| 21 | c | Linux suele traer 0; Windows y OpenBSD, 1 |
| 22 | c | Dirección IPv4 mapeada |
| 23 | d | Mismo cliente, dos escrituras |
| 24 | c | `getaddrinfo()` y probar en orden |
| 25 | a | 40 bytes fijos |
| 26 | c | Redundante y caro de recalcular |
| 27 | a | Ya no hay checksum de red que cubra el hueco |
| 28 | d | Solo el emisor |
| 29 | d | ICMPv6 es estructural en IPv6 |
| 30 | a | NAT |
| 31 | a | Conectividad entrante y extremo a extremo |
| 32 | d | Dirección sin ruta, común en Argentina |

</details>

---

## Resultado de la autoevaluación

| Puntaje | Diagnóstico |
|---------|-------------|
| 29-32 correctas | Excelente. Avanzá a la clase 17 (I/O Multiplexing) |
| 23-28 | Buen nivel. Repasá los temas donde fallaste |
| 16-22 | Nivel intermedio. Rehacé el ejercicio 3 (dual-stack) |
| < 16 | Repasá el contenido completo. Consultá con el docente antes de la próxima clase |

> Las preguntas 13, 14, 18 y 20 a 24 son las que más importan en la práctica: son los errores que rompen código real. Si fallaste varias, volvé sobre ellas aunque el total te haya dado bien.

---

*Computación II - 2026 - Clase 16*
