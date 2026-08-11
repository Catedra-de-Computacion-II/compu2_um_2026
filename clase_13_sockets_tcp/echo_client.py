#!/usr/bin/env python3
"""Cliente del servidor eco, con demostración de lecturas parciales.

Uso:
    python3 echo_client.py                   # envía un mensaje y lo lee
    python3 echo_client.py --parcial         # lee de a 4 bytes
    python3 echo_client.py --tres            # tres sendall(): ver el framing

Requiere echo_server.py corriendo en otra terminal.
"""
import socket
import sys
import time

HOST, PUERTO = 'localhost', 8080


def simple():
    """Un envío, una lectura."""
    with socket.create_connection((HOST, PUERTO), timeout=5) as s:
        s.sendall(b'hola mundo\n')
        respuesta = s.recv(4096)
        print(f'Recibido: {respuesta!r}')


def parcial():
    """Lee de a 4 bytes para hacer visible que recv() devuelve lo que hay."""
    mensaje = b'un mensaje bastante mas largo que cuatro bytes\n'
    with socket.create_connection((HOST, PUERTO), timeout=5) as s:
        s.sendall(mensaje)
        s.shutdown(socket.SHUT_WR)      # "no mando más"; el server verá b''
        recibido = b''
        while True:
            pedazo = s.recv(4)          # tope de 4 bytes a propósito
            if not pedazo:
                break
            print(f'  recv(4) -> {pedazo!r}')
            recibido += pedazo
        print(f'Total: {len(recibido)} bytes de {len(mensaje)} enviados')


def tres():
    """Tres sendall() separados: el servidor casi nunca ve tres recv()."""
    with socket.create_connection((HOST, PUERTO), timeout=5) as s:
        for msg in (b'HOLA', b'COMO', b'ESTAS'):
            s.sendall(msg)
        time.sleep(0.5)                 # dar tiempo al eco
        print(f'Eco recibido: {s.recv(4096)!r}')
        print('Mirá la salida del servidor: ¿cuántos recv() hizo?')


if __name__ == '__main__':
    modo = sys.argv[1] if len(sys.argv) > 1 else ''
    try:
        {'--parcial': parcial, '--tres': tres}.get(modo, simple)()
    except ConnectionRefusedError:
        print(f'No hay nadie escuchando en {HOST}:{PUERTO}.')
        print('Levantá el servidor con: python3 echo_server.py')
