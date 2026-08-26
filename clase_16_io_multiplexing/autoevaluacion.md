# Clase 16: Direccionamiento IPv4 e I/O Multiplexing - Autoevaluación

> Completá esta autoevaluación **después** de leer el contenido y hacer los ejercicios.
> No mires las respuestas antes de intentarlo.

---

## Parte 0: Direccionamiento IPv4

**Pregunta 1.** En `192.168.1.37/24`, ¿qué indica el `/24`?

a) La cantidad de hosts
b) Que los primeros 24 bits identifican la red
c) El número de subred
d) La versión del protocolo

**Pregunta 2.** ¿Cuántas direcciones tiene un `/24`?

a) 24
b) 128
c) 256
d) 1024

**Pregunta 3.** ¿Cuántos hosts usables?

a) 256
b) 254
c) 255
d) 252

**Pregunta 4.** ¿Por qué se pierden dos?

a) Las reserva el router
b) Son la dirección de red y la de broadcast
c) Las usa el DHCP
d) Es un límite del protocolo

**Pregunta 5.** ¿Cuál abarca más direcciones, un `/24` o un `/30`?

a) El `/30`
b) El `/24`
c) Son iguales
d) Depende de la máscara

**Pregunta 6.** Docker crea `172.17.0.0/16`. ¿Cuántas direcciones son?

a) 256
b) 4.096
c) 65.536
d) 16.777.216

**Pregunta 7.** Dos máquinas: `10.0.0.5/24` y `10.0.1.7/24`, en el mismo switch. ¿Se ven directamente?

a) Sí, están en el mismo cable
b) No: están en redes distintas y necesitan un router
c) Sí, si tienen el mismo gateway
d) Solo con IPv6

**Pregunta 8.** ¿Qué hace tu sistema cuando el destino NO está en su red?

a) Descarta el paquete
b) Lo manda al gateway
c) Hace broadcast
d) Lo manda igual por la placa

---

## Parte 1: El problema

**Pregunta 9.** ¿Cuál es la limitación de fondo de las estrategias de la clase 14 (thread/proceso por cliente)?

a) Son difíciles de programar
b) Consumen un recurso del sistema operativo por cada cliente
c) No funcionan en Linux
d) No soportan IPv6

**Pregunta 10.** ¿Por qué un servidor secuencial no puede atender dos clientes con un solo hilo?

a) Porque el socket no lo permite
b) Porque `recv()` bloquea hasta que lleguen datos por esa conexión
c) Porque falta memoria
d) Porque el kernel lo prohíbe

**Pregunta 11.** ¿Qué problema tiene un bucle con sockets no bloqueantes y sin multiplexor?

a) No funciona
b) Es busy-waiting: consume CPU al máximo preguntando constantemente
c) Pierde datos
d) Solo sirve para un cliente

**Pregunta 12.** ¿Qué le pide `select()` al sistema operativo?

a) Que cree un thread por conexión
b) Que lo despierte cuando alguno de estos descriptores esté listo
c) Que aumente el límite de descriptores
d) Que cierre las conexiones inactivas

**Pregunta 13.** ¿Qué es el problema C10K?

a) Un bug de Linux del año 2000
b) Cómo atender diez mil conexiones simultáneas en una máquina
c) Un límite de memoria
d) Una vulnerabilidad de TCP

---

## Parte 2: select

**Pregunta 14.** ¿Qué devuelve `select.select(lectura, escritura, error, timeout)`?

a) Un booleano
b) El primer socket listo
c) Tres listas con los descriptores que están listos
d) La cantidad de descriptores listos

**Pregunta 15.** ¿Por qué se vigila también el socket que escucha?

a) Por costumbre
b) Porque "listo para leer" en ese socket significa que hay una conexión esperando en `accept()`
c) Para detectar errores de red
d) No hace falta vigilarlo

**Pregunta 16.** `select()` reporta un socket como listo para leer. ¿Qué garantiza eso?

a) Que hay al menos 4096 bytes disponibles
b) Que el `recv()` no va a bloquear; puede haber 1 byte o un cierre
c) Que el cliente mandó un mensaje completo
d) Que la conexión sigue viva

**Pregunta 17.** ¿Qué pasa si no sacás de la lista un socket que se cerró?

a) Nada
b) `select()` lo reporta listo para siempre y el bucle gira infinitamente
c) El servidor se cae con una excepción
d) El socket se reabre solo

**Pregunta 18.** ¿Cuál es exactamente el límite de `select()`?

a) La cantidad de descriptores: máximo 1024
b) El **número** de cada descriptor: uno solo mayor a 1023 hace fallar la llamada
c) La cantidad de bytes por lectura
d) No tiene límite

**Pregunta 19.** Ese límite se llama:

a) `ULIMIT_N`
b) `FD_SETSIZE`
c) `MAX_CONN`
d) `SOMAXCONN`

**Pregunta 20.** ¿Por qué `select()` es O(n)?

a) Porque usa un algoritmo de ordenamiento
b) Porque pasa y recorre la lista completa de descriptores en cada llamada
c) Porque hace una syscall por descriptor
d) No es O(n)

---

## Parte 3: poll y epoll

**Pregunta 21.** ¿Qué arregla `poll()` respecto de `select()`?

a) El costo O(n)
b) El límite de FD_SETSIZE
c) Ambas cosas
d) Ninguna

**Pregunta 22.** ¿Qué diferencia incómoda tiene la API de `poll()`?

a) No soporta timeouts
b) Trabaja con números de descriptor, no con objetos socket, así que hay que mantener un diccionario
c) Solo funciona con UDP
d) Requiere root

**Pregunta 23.** ¿Qué significa `POLLIN`?

a) El socket se cerró
b) Hay datos para leer, o una conexión pendiente
c) Se puede escribir
d) Hubo un error

**Pregunta 24.** ¿Cuál es el cambio de modelo que introduce `epoll`?

a) Usa threads internamente
b) El kernel mantiene el conjunto de descriptores; solo se lo modifica cuando algo cambia
c) Es más rápido por estar escrito en C
d) Elimina la necesidad de sockets no bloqueantes

**Pregunta 25.** ¿Qué devuelve `epoll.poll()`?

a) Todos los descriptores registrados
b) Solo los que están listos
c) Un booleano
d) El primer descriptor listo

**Pregunta 26.** Con 10.000 conexiones de las cuales 3 tienen datos, ¿cuántos elementos recorre tu código con `epoll`?

a) 10.000
b) 3
c) 1
d) Depende del timeout

**Pregunta 27.** ¿En qué sistemas está disponible `epoll`?

a) Todos
b) Solo Linux
c) Solo BSD y macOS
d) Solo Windows

**Pregunta 28.** ¿Cuáles son los equivalentes en otros sistemas?

a) No existen
b) `kqueue` en BSD/macOS, IOCP en Windows
c) `select` en todos
d) `poll` en todos

---

## Parte 4: selectors y el event loop

**Pregunta 29.** ¿Por qué conviene usar `selectors` en vez de `epoll` directo?

a) Es más rápido
b) Elige la mejor implementación disponible en cada sistema, así el código es portable
c) Consume menos memoria
d) Es la única forma en Python

**Pregunta 30.** ¿Qué ventaja tiene el tercer argumento de `sel.register(socket, evento, dato)`?

a) Configura el timeout
b) Permite asociar datos al socket (típicamente el handler), evitando el diccionario manual
c) Define la prioridad
d) No sirve para nada

**Pregunta 31.** ¿Qué hay que hacer antes de cerrar un socket registrado?

a) Nada
b) Llamar a `sel.unregister(conn)`
c) Llamar a `sel.modify()`
d) Esperar el timeout

**Pregunta 32.** El bucle que despacha a un callback según qué socket está listo, ¿cómo se llama?

a) Thread pool
b) Event loop
c) Scheduler preemptivo
d) Round robin

**Pregunta 33.** ¿Qué relación tiene ese bucle con asyncio?

a) Ninguna
b) Es, en esencia, lo que asyncio hace por dentro
c) Asyncio usa threads en su lugar
d) Asyncio lo reemplazó por polling

---

## Parte 5: Escritura y límites

**Pregunta 34.** En un servidor con multiplexing, ¿por qué se usa `send()` y no `sendall()`?

a) Porque `sendall()` no existe para sockets no bloqueantes
b) Porque `sendall()` insiste hasta terminar, y eso bloquearía a los demás clientes
c) Porque `send()` es más rápido
d) Es indistinto

**Pregunta 35.** ¿Qué pasa si registrás `EVENT_WRITE` de forma permanente?

a) Nada
b) El bucle gira sin parar, porque un socket casi siempre está listo para escribir
c) El socket se cierra
d) Mejora el rendimiento

**Pregunta 36.** ¿Cuándo hay que registrar interés en escritura?

a) Siempre
b) Solo cuando hay datos pendientes de enviar para ese socket
c) Nunca
d) Solo al conectar

**Pregunta 37.** Tu handler hace un cálculo de 2 segundos de CPU. ¿Qué les pasa a los otros clientes?

a) Nada, siguen atendidos
b) Quedan congelados esos 2 segundos: hay un solo hilo
c) Se desconectan
d) Pasan a otro thread automáticamente

**Pregunta 38.** ¿Cuál es la regla de oro del modelo de event loop?

a) Usar siempre epoll
b) Nada lento puede correr en el hilo del bucle
c) Nunca usar timeouts
d) Un socket por cliente

**Pregunta 39.** Con 10 conexiones, ¿vale la pena `epoll` sobre `select`?

a) Sí, siempre es mejor
b) La diferencia es despreciable a esa escala; la ventaja aparece con miles
c) No, `epoll` es peor con pocas conexiones
d) Depende del sistema operativo

**Pregunta 40.** Si la mitad de las conexiones vigiladas tienen datos, ¿qué pasa con la ventaja de `epoll`?

a) Se agranda
b) Se achica mucho: la ventaja viene de que pocos estén listos
c) No cambia
d) `epoll` deja de funcionar

---

## Respuestas

<details>
<summary>Ver respuestas (intentá primero)</summary>

| # | Respuesta | Comentario |
|---|-----------|------------|
| 1 | b | El prefijo dice qué parte es red |
| 2 | c | 2^(32-24) = 256 |
| 3 | b | 256 menos red y broadcast |
| 4 | b | Dirección de red y de broadcast |
| 5 | b | Más chico el número, más grande la red |
| 6 | c | 2^(32-16) = 65.536 |
| 7 | b | Mismo cable, redes distintas |
| 8 | b | Va al gateway |
| 9 | b | Un thread o proceso por cliente no escala |
| 10 | b | `recv()` bloquea en esa conexión |
| 11 | b | Busy-waiting quema un core sin hacer nada |
| 12 | b | Dormir hasta que alguno esté listo |
| 13 | b | El texto de Dan Kegel, 1999 |
| 14 | c | Tres listas: lectura, escritura, error |
| 15 | b | Disponibilidad aplicada a `accept()` |
| 16 | b | Solo garantiza que no va a bloquear |
| 17 | b | El bug del bucle infinito |
| 18 | b | Es el valor del fd, no la cantidad |
| 19 | b | `FD_SETSIZE`, 1024 |
| 20 | b | Copia y recorre todo en cada llamada |
| 21 | b | Saca el límite, no el O(n) |
| 22 | b | Hay que mapear fd a socket a mano |
| 23 | b | Datos o conexión pendiente |
| 24 | b | El kernel mantiene el conjunto |
| 25 | b | Solo los listos |
| 26 | b | 3, no 10.000: ese es el punto |
| 27 | b | Específico de Linux |
| 28 | b | kqueue e IOCP |
| 29 | b | Portabilidad |
| 30 | b | Evita el diccionario manual |
| 31 | b | `unregister()` antes de `close()` |
| 32 | b | Event loop |
| 33 | b | Es lo que asyncio hace por dentro |
| 34 | b | `sendall()` bloquearía a todos |
| 35 | b | El bucle gira sin parar |
| 36 | b | Solo con datos pendientes |
| 37 | b | Un solo hilo: se congelan |
| 38 | b | Nada lento en el bucle |
| 39 | b | Verificado: con 10 conexiones son equivalentes |
| 40 | b | Verificado: con 1000 de 2000 activos casi empatan |

</details>

---

## Resultado de la autoevaluación

| Puntaje | Diagnóstico |
|---------|-------------|
| 36-40 correctas | Excelente. Avanzá a la clase 17 (HTTP + FastAPI) |
| 29-35 | Buen nivel. Repasá los temas donde fallaste |
| 20-28 | Nivel intermedio. Rehacé el ejercicio 3 (comparar) y el 7 |
| < 20 | Repasá el contenido completo. Consultá con el docente antes de la próxima clase |

> Las preguntas 16, 18, 32, 37 y 38 son las que más importan para lo que viene: la 32 y la 38 son literalmente las que van a explicar el comportamiento de asyncio en las clases 18-20.

---

*Computación II - 2026 - Clase 16*
