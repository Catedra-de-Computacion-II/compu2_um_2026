# Clase 12: Redes - Autoevaluación

> Completá esta autoevaluación **después** de leer el contenido y hacer los ejercicios.
> No mires las respuestas antes de intentarlo.

---

## Parte 1: Capas y modelos

**Pregunta 1.** ¿Cuál es la principal razón para organizar los protocolos en capas?

a) Reducir la cantidad de bytes transmitidos
b) Hacer la red más rápida
c) Aislar problemas: cada capa resuelve uno y abstrae a la de arriba
d) Cumplir con el estándar OSI

**Pregunta 2.** ¿Cuántas capas tiene el modelo TCP/IP?

a) 7
b) 5
c) Depende de la implementación
d) 4

**Pregunta 3.** ¿En qué capa del modelo TCP/IP opera el protocolo IP?

a) Transporte
b) Enlace
c) Aplicación
d) Internet

**Pregunta 4.** ¿Qué es el encapsulamiento?

a) Ocultar la dirección IP del emisor
b) Cifrar los datos antes de enviarlos
c) Cada capa envuelve los datos de la capa superior con su propio encabezado
d) Agrupar varios paquetes en uno solo

**Pregunta 5.** El modelo OSI tiene 7 capas pero nunca se implementó tal cual. ¿Por qué se sigue estudiando?

a) Porque es más rápido que TCP/IP
b) Porque es obligatorio por ley
c) Porque su vocabulario y numeración se usan como jerga común
d) Porque TCP/IP lo va a reemplazar pronto

---

## Parte 2: Direccionamiento

**Pregunta 6.** ¿Cuántos bits tiene una dirección IPv4?

a) 32
b) 16
c) 64
d) 128

**Pregunta 7.** ¿Qué significa la dirección `127.0.0.1`?

a) Broadcast a toda la red
b) Loopback: esta misma máquina
c) Una dirección sin asignar
d) El gateway por defecto

**Pregunta 8.** Un servidor hace `bind` en `0.0.0.0`. ¿Qué implica?

a) Escucha solo en loopback
b) Escucha en todas las interfaces de la máquina
c) No escucha en ninguna parte
d) Escucha solo en IPv6

**Pregunta 9.** ¿Cuántos bits tiene un número de puerto?

a) 32
b) 64
c) 16
d) 8

**Pregunta 10.** ¿Por qué los puertos menores a 1024 requieren privilegios de root en Unix?

a) Porque son más rápidos
b) Porque los usa el kernel internamente
c) Es una limitación histórica sin razón actual
d) Para evitar que un usuario cualquiera se haga pasar por un servicio estándar del sistema

**Pregunta 11.** ¿Qué identifica de forma única a una conexión TCP?

a) La IP de origen
b) El puerto de destino
c) El PID del proceso
d) La cuádrupla (IP origen, puerto origen, IP destino, puerto destino)

**Pregunta 12.** Un servidor web atiende a 10.000 clientes en el puerto 80. ¿Cómo los distingue?

a) No puede: 80 solo admite una conexión
b) Usa un puerto distinto para cada uno
c) Por la combinación de IP y puerto de origen de cada cliente
d) Por el PID de cada cliente

**Pregunta 13.** ¿Qué rango de puertos usa el sistema operativo para asignar a conexiones salientes?

a) 0-1023
b) El rango efímero (49152-65535 según IANA; en Linux suele ser 32768-60999)
c) Cualquiera, al azar
d) 1024-49151

**Pregunta 14.** ¿Qué es el TTL en una respuesta DNS?

a) Cuántos routers atravesó el paquete
b) El tiempo que tardó la consulta
c) La cantidad de reintentos permitidos
d) Cuántos segundos se puede cachear la respuesta

---

## Parte 3: TCP y UDP

**Pregunta 15.** ¿Cuántos paquetes intercambia el handshake de TCP?

a) 2
b) 3
c) 4
d) 1

**Pregunta 16.** Un cliente hace `send("HOLA")`, `send("COMO")` y `send("ESTAS")` sobre TCP. ¿Qué puede recibir el servidor?

a) Los tres mensajes en cualquier orden
b) Exactamente tres mensajes: "HOLA", "COMO", "ESTAS"
c) Cualquier partición de "HOLACOMOESTAS", incluyendo todo junto
d) Solo el último mensaje

**Pregunta 17.** Si TCP entrega los datos agrupados de forma distinta a como se enviaron, ¿es un bug?

a) Sí, pero solo si se pierde algún byte
b) Depende del sistema operativo
c) No, TCP garantiza orden e integridad de bytes, no límites de mensajes
d) Sí, TCP debe preservar los límites

**Pregunta 18.** ¿Qué garantiza UDP?

a) Nada sobre entrega ni orden, pero preserva los límites de cada datagrama
b) Entrega confiable pero sin orden
c) Entrega ordenada pero no confiable
d) Entrega confiable y ordenada

**Pregunta 19.** ¿Por qué DNS usa UDP para las consultas comunes?

a) Porque la consulta y respuesta son chicas y reintentar sale más barato que montar una conexión
b) Porque UDP es siempre más rápido
c) Porque TCP no soporta el puerto 53
d) Porque DNS no necesita direcciones IP

**Pregunta 20.** ¿Cuál de estas aplicaciones es mejor candidata para UDP?

a) Transferencia de un archivo grande
b) Streaming de voz en tiempo real
c) Una sesión SSH
d) Una transacción bancaria

**Pregunta 21.** ¿Qué tamaño tiene el encabezado de UDP comparado con el de TCP?

a) Iguales
b) 20 bytes contra 8
c) UDP no tiene encabezado
d) 8 bytes contra 20

**Pregunta 22.** "UDP es más rápido que TCP" es una afirmación:

a) Simplificada: si tu aplicación necesita confiabilidad y la implementás sobre UDP, puede terminar más lenta que TCP
b) Siempre cierta
c) Siempre falsa
d) Cierta solo en redes locales

**Pregunta 23.** ¿Por qué una conexión a un servidor lejano "tarda en abrir" aunque después vaya rápido?

a) Porque el handshake requiere un ida y vuelta completo antes del primer byte útil
b) Porque hay que resolver el DNS cada vez
c) Porque TCP comprime los datos iniciales
d) Porque el servidor está ocupado

---

## Parte 4: Herramientas y práctica

**Pregunta 24.** ¿Qué comando muestra los puertos TCP en escucha en tu máquina?

a) `traceroute -p`
b) `dig -listen`
c) `ss -tlnp`
d) `ping -l`

**Pregunta 25.** Hacés `ping` a un servidor y no responde. ¿Qué podés concluir?

a) El puerto 80 está cerrado
b) El servidor está caído con certeza
c) Tu conexión a Internet no funciona
d) Nada concluyente: muchos servidores filtran ICMP

**Pregunta 26.** ¿Qué hace `nc -l 8080`?

a) Se conecta al puerto 8080
b) Escucha en el puerto 8080 esperando una conexión
c) Escanea el puerto 8080
d) Cierra el puerto 8080

**Pregunta 27.** Al escribir peticiones HTTP a mano, ¿qué final de línea corresponde usar?

a) Cualquiera, es indistinto
b) `\r\n`
c) `\r`
d) `\n`

**Pregunta 28.** Levantás un servidor y al conectarte desde otra máquina no responde, pero desde localhost sí. ¿Cuál es la causa más probable?

a) Falta instalar netcat
b) El servidor hizo bind en `127.0.0.1` en lugar de `0.0.0.0`
c) El cable de red está desconectado
d) TCP no funciona entre máquinas

**Pregunta 29.** Aparece el error `Address already in use` al levantar un servidor. ¿Qué significa?

a) La dirección IP está duplicada en la red
b) El puerto no existe
c) Otro proceso ya está escuchando en ese puerto
d) Falta ejecutar como root

**Pregunta 30.** ¿Cuál es la diferencia entre lo que hace `nc` y lo que vamos a programar en la clase 13?

a) Ninguna conceptual; vamos a implementar lo mismo con la API de sockets
b) `nc` no puede actuar de servidor
c) Ninguna: `nc` está escrito en Python
d) `nc` usa UDP y los sockets de Python usan TCP

---

## Respuestas

<details>
<summary>Ver respuestas (intentá primero)</summary>

| # | Respuesta | Comentario |
|---|-----------|------------|
| 1 | c | Cada capa abstrae la complejidad de la de abajo |
| 2 | d | 4 capas: enlace, internet, transporte, aplicación |
| 3 | d | IP da nombre a la capa Internet |
| 4 | c | Los datos viajan anidados en encabezados sucesivos |
| 5 | c | La numeración OSI sobrevivió como vocabulario |
| 6 | a | 32 bits; IPv6 usa 128 |
| 7 | b | Loopback, la propia máquina |
| 8 | b | Todas las interfaces disponibles |
| 9 | c | 16 bits: 0 a 65535 |
| 10 | d | Impide usurpar servicios estándar |
| 11 | d | La cuádrupla, no solo el puerto |
| 12 | c | Cada cliente aporta origen distinto |
| 13 | b | El rango efímero; Linux usa uno propio |
| 14 | d | Segundos de cacheo permitido |
| 15 | b | SYN, SYN-ACK, ACK |
| 16 | c | TCP es un flujo, no preserva límites |
| 17 | c | No viola el contrato de TCP |
| 18 | a | Sin garantías, pero con límites preservados |
| 19 | a | Reintentar es más barato que el handshake |
| 20 | b | Llegar tarde es peor que no llegar |
| 21 | d | 8 contra 20 bytes |
| 22 | a | Depende de lo que necesite la aplicación |
| 23 | a | Ida y vuelta del handshake antes del primer dato |
| 24 | c | `ss -tlnp` |
| 25 | d | El filtrado de ICMP es habitual |
| 26 | b | `-l` es listen |
| 27 | b | Los protocolos de texto de Internet usan CRLF |
| 28 | b | Loopback no es alcanzable desde afuera |
| 29 | c | Puerto ocupado por otro proceso |
| 30 | a | `nc` es el mismo concepto, ya implementado |

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
