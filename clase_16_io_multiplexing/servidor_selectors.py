#!/usr/bin/env python3
"""Servidor eco con selectors: portable y con escritura no bloqueante.

Esta es la forma correcta de hacerlo en Python: selectors elige epoll en
Linux, kqueue en BSD/macOS, y select donde no haya nada mejor.

El bucle del final es un event loop: despacha a un callback sin saber qué
hace cada socket. Es, en esencia, lo que hace asyncio por dentro.

Uso:
    python3 servidor_selectors.py [puerto]
"""
import selectors
import socket
import sys

PUERTO = int(sys.argv[1]) if len(sys.argv) > 1 else 8080

sel = selectors.DefaultSelector()
pendiente = {}          # socket -> bytes que faltan enviar


def aceptar(servidor):
    """El socket que escucha está listo: hay una conexión esperando."""
    conn, direccion = servidor.accept()
    conn.setblocking(False)
    # El tercer argumento es dato libre: guardamos quién atiende este socket.
    sel.register(conn, selectors.EVENT_READ, atender)
    print(f'+ cliente {direccion}')


def cerrar(conn):
    """Siempre unregister ANTES de close: un fd cerrado y aún registrado
    deja al selector en estado indefinido."""
    sel.unregister(conn)
    pendiente.pop(conn, None)
    conn.close()


def atender(conn):
    """Hay datos para leer (o el cliente cerró)."""
    try:
        datos = conn.recv(4096)
    except ConnectionResetError:
        cerrar(conn)
        print('- cliente (reset)')
        return

    if not datos:
        cerrar(conn)
        print('- cliente (cerró)')
        return

    pendiente[conn] = pendiente.get(conn, b'') + datos
    # Ahora me interesa saber cuándo puedo escribir sin bloquear.
    sel.modify(conn, selectors.EVENT_READ | selectors.EVENT_WRITE, atender_rw)


def atender_rw(conn, escribible=False):
    """Handler que sirve para lectura y escritura."""
    if escribible:
        escribir(conn)
    else:
        atender(conn)


def escribir(conn):
    """Se puede escribir sin bloquear: mandar lo que entre."""
    buf = pendiente.get(conn, b'')
    if buf:
        try:
            # send(), NO sendall(): sendall insiste hasta terminar y eso
            # bloquearía a los demás clientes. Mandamos lo que entre ahora
            # y volvemos cuando el selector avise que se puede seguir.
            n = conn.send(buf)
        except (BrokenPipeError, ConnectionResetError):
            cerrar(conn)
            return
        pendiente[conn] = buf[n:]

    if not pendiente.get(conn):
        # Ya no queda nada pendiente: dejar de vigilar escritura.
        # Si lo dejáramos registrado, el bucle giraría sin parar, porque
        # un socket casi siempre está listo para escribir.
        sel.modify(conn, selectors.EVENT_READ, atender)


def main():
    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    servidor.bind(('0.0.0.0', PUERTO))
    servidor.listen(128)
    servidor.setblocking(False)
    sel.register(servidor, selectors.EVENT_READ, aceptar)

    print(f'Escuchando en 0.0.0.0:{PUERTO}')
    print(f'Implementación elegida: {type(sel).__name__}')

    try:
        while True:
            # El event loop: despacha al handler registrado con cada socket.
            for clave, mascara in sel.select():
                callback = clave.data
                if callback is atender_rw:
                    callback(clave.fileobj, bool(mascara & selectors.EVENT_WRITE))
                else:
                    callback(clave.fileobj)
    except KeyboardInterrupt:
        print('\nServidor detenido')
    finally:
        sel.close()


if __name__ == '__main__':
    main()
