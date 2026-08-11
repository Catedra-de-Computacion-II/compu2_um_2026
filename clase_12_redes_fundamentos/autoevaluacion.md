# Clase 12: Redes - Autoevaluación

> Completá esta autoevaluación **después** de leer el contenido y hacer los ejercicios.
> No mires las respuestas antes de intentarlo.

---

## Parte 1: Capas y modelos

**Pregunta 1.** ¿Cuál es la principal razón para organizar los protocolos en capas?

a) Hacer la red más rápida
b) Aislar problemas: cada capa resuelve uno y abstrae a la de arriba
c) Cumplir con el estándar OSI
d) Reducir la cantidad de bytes transmitidos

**Pregunta 2.** ¿Cuántas capas tiene el modelo TCP/IP?

a) 4
b) 5
c) 7
d) Depende de la implementación

**Pregunta 3.** ¿En qué capa del modelo TCP/IP opera el protocolo IP?

a) Enlace
b) Internet
c) Transporte
d) Aplicación

**Pregunta 4.** ¿Qué es el encapsulamiento?

a) Cifrar los datos antes de enviarlos
b) Cada capa envuelve los datos de la capa superior con su propio encabezado
c) Agrupar varios paquetes en uno solo
d) Ocultar la dirección IP del emisor

**Pregunta 5.** El modelo OSI tiene 7 capas pero nunca se implementó tal cual. ¿Por qué se sigue estudiando?

a) Porque es obligatorio por ley
b) Porque su vocabulario y numeración se usan como jerga común
c) Porque TCP/IP lo va a reemplazar pronto
d) Porque es más rápido que TCP/IP

---

## Parte 2: Direccionamiento

**Pregunta 6.** ¿Cuántos bits tiene una dirección IPv4?

a) 16
b) 32
c) 64
d) 128

**Pregunta 7.** ¿Qué significa la dirección `127.0.0.1`?

a) El gateway por defecto
b) Broadcast a toda la red
c) Loopback: esta misma máquina
d) Una dirección sin asignar

**Pregunta 8.** Un servidor hace `bind` en `0.0.0.0`. ¿Qué implica?

a) Escucha en todas las interfaces de la máquina
b) No escucha en ninguna parte
c) Escucha solo en loopback
d) Escucha solo en IPv6

**Pregunta 9.** ¿Cuántos bits tiene un número de puerto?

a) 8
b) 16
c) 32
d) 64

**Pregunta 10.** ¿Por qué los puertos menores a 1024 requieren privilegios de root en Unix?

a) Porque son más rápidos
b) Para evitar que un usuario cualquiera se haga pasar por un servicio estándar del sistema
c) Porque los usa el kernel internamente
d) Es una limitación histórica sin razón actual

**Pregunta 11.** ¿Qué identifica de forma única a una conexión TCP?

a) El puerto de destino
b) La IP de origen
c) La cuádrupla (IP origen, puerto origen, IP destino, puerto destino)
d) El PID del proceso

**Pregunta 12.** Un servidor web atiende a 10.000 clientes en el puerto 80. ¿Cómo los distingue?

a) Usa un puerto distinto para cada uno
b) Por la combinación de IP y puerto de origen de cada cliente
c) Por el PID de cada cliente
d) No puede: 80 solo admite una conexión

**Pregunta 13.** ¿Qué rango de puertos usa el sistema operativo para asignar a conexiones salientes?

a) 0-1023
b) 1024-49151
c) El rango efímero (49152-65535 según IANA; en Linux suele ser 32768-60999)
d) Cualquiera, al azar

**Pregunta 14.** ¿Qué es el TTL en una respuesta DNS?

a) El tiempo que tardó la consulta
b) Cuántos segundos se puede cachear la respuesta
c) Cuántos routers atravesó el paquete
d) La cantidad de reintentos permitidos

---

## Parte 3: TCP y UDP

**Pregunta 15.** ¿Cuántos paquetes intercambia el handshake de TCP?

a) 1
b) 2
c) 3
d) 4

**Pregunta 16.** Un cliente hace `send("HOLA")`, `send("COMO")` y `send("ESTAS")` sobre TCP. ¿Qué puede recibir el servidor?

a) Exactamente tres mensajes: "HOLA", "COMO", "ESTAS"
b) Cualquier partición de "HOLACOMOESTAS", incluyendo todo junto
c) Los tres mensajes en cualquier orden
d) Solo el último mensaje

**Pregunta 17.** Si TCP entrega los datos agrupados de forma distinta a como se enviaron, ¿es un bug?

a) Sí, TCP debe preservar los límites
b) No, TCP garantiza orden e integridad de bytes, no límites de mensajes
c) Sí, pero solo si se pierde algún byte
d) Depende del sistema operativo

**Pregunta 18.** ¿Qué garantiza UDP?

a) Entrega confiable y ordenada
b) Nada sobre entrega ni orden, pero preserva los límites de cada datagrama
c) Entrega ordenada pero no confiable
d) Entrega confiable pero sin orden

**Pregunta 19.** ¿Por qué DNS usa UDP para las consultas comunes?

a) Porque UDP es siempre más rápido
b) Porque la consulta y respuesta son chicas y reintentar sale más barato que montar una conexión
c) Porque DNS no necesita direcciones IP
d) Porque TCP no soporta el puerto 53

**Pregunta 20.** ¿Cuál de estas aplicaciones es mejor candidata para UDP?

a) Transferencia de un archivo grande
b) Una sesión SSH
c) Streaming de voz en tiempo real
d) Una transacción bancaria

**Pregunta 21.** ¿Qué tamaño tiene el encabezado de UDP comparado con el de TCP?

a) 8 bytes contra 20
b) 20 bytes contra 8
c) Iguales
d) UDP no tiene encabezado

**Pregunta 22.** "UDP es más rápido que TCP" es una afirmación:

a) Siempre cierta
b) Simplificada: si tu aplicación necesita confiabilidad y la implementás sobre UDP, puede terminar más lenta que TCP
c) Siempre falsa
d) Cierta solo en redes locales

**Pregunta 23.** ¿Por qué una conexión a un servidor lejano "tarda en abrir" aunque después vaya rápido?

a) Porque el servidor está ocupado
b) Porque el handshake requiere un ida y vuelta completo antes del primer byte útil
c) Porque hay que resolver el DNS cada vez
d) Porque TCP comprime los datos iniciales

---

## Parte 4: Herramientas y práctica

**Pregunta 24.** ¿Qué comando muestra los puertos TCP en escucha en tu máquina?

a) `ping -l`
b) `ss -tlnp`
c) `dig -listen`
d) `traceroute -p`

**Pregunta 25.** Hacés `ping` a un servidor y no responde. ¿Qué podés concluir?

a) El servidor está caído con certeza
b) Nada concluyente: muchos servidores filtran ICMP
c) El puerto 80 está cerrado
d) Tu conexión a Internet no funciona

**Pregunta 26.** ¿Qué hace `nc -l 8080`?

a) Se conecta al puerto 8080
b) Escucha en el puerto 8080 esperando una conexión
c) Escanea el puerto 8080
d) Cierra el puerto 8080

**Pregunta 27.** Al escribir peticiones HTTP a mano, ¿qué final de línea corresponde usar?

a) `\n`
b) `\r\n`
c) `\r`
d) Cualquiera, es indistinto

**Pregunta 28.** Levantás un servidor y al conectarte desde otra máquina no responde, pero desde localhost sí. ¿Cuál es la causa más probable?

a) El cable de red está desconectado
b) El servidor hizo bind en `127.0.0.1` en lugar de `0.0.0.0`
c) TCP no funciona entre máquinas
d) Falta instalar netcat

**Pregunta 29.** Aparece el error `Address already in use` al levantar un servidor. ¿Qué significa?

a) La dirección IP está duplicada en la red
b) Otro proceso ya está escuchando en ese puerto
c) El puerto no existe
d) Falta ejecutar como root

**Pregunta 30.** ¿Cuál es la diferencia entre lo que hace `nc` y lo que vamos a programar en la clase 13?

a) Ninguna: `nc` está escrito en Python
b) Ninguna conceptual; vamos a implementar lo mismo con la API de sockets
c) `nc` usa UDP y los sockets de Python usan TCP
d) `nc` no puede actuar de servidor

---

## Respuestas

<details>
<summary>Ver respuestas (intentá primero)</summary>

| # | Respuesta | Comentario |
|---|-----------|------------|
| 1 | b | Cada capa abstrae la complejidad de la de abajo |
| 2 | a | 4 capas: enlace, internet, transporte, aplicación |
| 3 | b | IP da nombre a la capa Internet |
| 4 | b | Los datos viajan anidados en encabezados sucesivos |
| 5 | b | La numeración OSI sobrevivió como vocabulario |
| 6 | b | 32 bits; IPv6 usa 128 |
| 7 | c | Loopback, la propia máquina |
| 8 | a | Todas las interfaces disponibles |
| 9 | b | 16 bits: 0 a 65535 |
| 10 | b | Impide usurpar servicios estándar |
| 11 | c | La cuádrupla, no solo el puerto |
| 12 | b | Cada cliente aporta origen distinto |
| 13 | c | El rango efímero; Linux usa uno propio |
| 14 | b | Segundos de cacheo permitido |
| 15 | c | SYN, SYN-ACK, ACK |
| 16 | b | TCP es un flujo, no preserva límites |
| 17 | b | No viola el contrato de TCP |
| 18 | b | Sin garantías, pero con límites preservados |
| 19 | b | Reintentar es más barato que el handshake |
| 20 | c | Llegar tarde es peor que no llegar |
| 21 | a | 8 contra 20 bytes |
| 22 | b | Depende de lo que necesite la aplicación |
| 23 | b | Ida y vuelta del handshake antes del primer dato |
| 24 | b | `ss -tlnp` |
| 25 | b | El filtrado de ICMP es habitual |
| 26 | b | `-l` es listen |
| 27 | b | Los protocolos de texto de Internet usan CRLF |
| 28 | b | Loopback no es alcanzable desde afuera |
| 29 | b | Puerto ocupado por otro proceso |
| 30 | b | `nc` es el mismo concepto, ya implementado |

</details>

---

## Resultado de la autoevaluación

| Puntaje | Diagnóstico |
|---------|-------------|
| 27-30 correctas | Excelente. Avanzá a la clase 13 (Sockets TCP) |
| 21-26 | Buen nivel. Repasá los temas donde fallaste |
| 14-20 | Nivel intermedio. Releé el contenido y rehacé los ejercicios 3, 4 y 6 |
| < 14 | Repasá el contenido completo. Consultá con el docente antes de la próxima clase |

> Las preguntas 11, 16 y 17 son las que más se usan como base en el resto del bloque. Si fallaste alguna de esas, volvé sobre ellas aunque el puntaje total te haya dado bien.

---

*Computación II - 2026 - Clase 12*
