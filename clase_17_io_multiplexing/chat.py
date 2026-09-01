#!/usr/bin/env python3
"""Chat multiusuario con selectors: lo que un servidor eco no muestra.

Acá aparece algo que el eco no tiene: para retransmitir un mensaje hay que
escribir en sockets DISTINTOS del que lo recibió. Con threads eso exigiría
un lock sobre la lista de clientes; en un event loop de un solo hilo, no.

Uso:
    python3 chat.py [puerto]

Y desde varias terminales:
    nc localhost 8080
"""
import selectors
import socket
import sys

PUERTO = int(sys.argv[1]) if len(sys.argv) > 1 else 8080

sel = selectors.DefaultSelector()
clientes = {}           # socket -> apodo
salida = {}             # socket -> bytes pendientes de enviar


def difundir(mensaje: bytes, excepto=None):
    """Encola un mensaje para todos los clientes menos uno.

    No escribe directo: encola. Escribir acá podría bloquear si el buffer
    de algún cliente lento está lleno, y eso congelaría a todos los demás.
    """
    for conn in clientes:
        if conn is excepto:
            continue
        salida[conn] = salida.get(conn, b'') + mensaje
        sel.modify(conn, selectors.EVENT_READ | selectors.EVENT_WRITE, manejar)


def aceptar(servidor, _mascara):
    conn, direccion = servidor.accept()
    conn.setblocking(False)
    apodo = f'{direccion[0]}:{direccion[1]}'
    clientes[conn] = apodo
    sel.register(conn, selectors.EVENT_READ, manejar)
    print(f'+ {apodo}  ({len(clientes)} conectados)')
    salida[conn] = b'Bienvenido al chat. Escribi y presiona Enter.\n'
    sel.modify(conn, selectors.EVENT_READ | selectors.EVENT_WRITE, manejar)
    difundir(f'* se conecto {apodo}\n'.encode(), excepto=conn)


def desconectar(conn):
    apodo = clientes.pop(conn, '?')
    salida.pop(conn, None)
    sel.unregister(conn)            # SIEMPRE antes de close()
    conn.close()
    print(f'- {apodo}  ({len(clientes)} conectados)')
    difundir(f'* se fue {apodo}\n'.encode())


def manejar(conn, mascara):
    """Un solo handler para lectura y escritura."""
    if mascara & selectors.EVENT_READ:
        try:
            datos = conn.recv(4096)
        except ConnectionResetError:
            desconectar(conn)
            return
        if not datos:
            desconectar(conn)
            return
        apodo = clientes.get(conn, '?')
        texto = datos.decode('utf-8', errors='replace').rstrip('\r\n')
        if texto:
            print(f'  <{apodo}> {texto}')
            difundir(f'<{apodo}> {texto}\n'.encode(), excepto=conn)

    if mascara & selectors.EVENT_WRITE:
        buf = salida.get(conn, b'')
        if buf:
            try:
                # send() y no sendall(): mandamos lo que entre y volvemos
                # cuando el selector avise. sendall() bloquearía a todos.
                n = conn.send(buf)
            except (BrokenPipeError, ConnectionResetError):
                desconectar(conn)
                return
            salida[conn] = buf[n:]
        if not salida.get(conn) and conn in clientes:
            # Nada pendiente: dejar de vigilar escritura, o el bucle giraría.
            sel.modify(conn, selectors.EVENT_READ, manejar)


def main():
    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    servidor.bind(('0.0.0.0', PUERTO))
    servidor.listen(128)
    servidor.setblocking(False)
    sel.register(servidor, selectors.EVENT_READ, aceptar)

    print(f'Chat escuchando en 0.0.0.0:{PUERTO} ({type(sel).__name__})')
    print('Conectate con: nc localhost', PUERTO)

    try:
        while True:
            for clave, mascara in sel.select():
                clave.data(clave.fileobj, mascara)
    except KeyboardInterrupt:
        print('\nChat detenido')
    finally:
        sel.close()


if __name__ == '__main__':
    main()
