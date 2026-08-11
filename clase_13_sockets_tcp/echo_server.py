#!/usr/bin/env python3
"""Servidor eco TCP secuencial.

Atiende UN cliente a la vez: mientras conversa con uno, los demás esperan
en la cola de listen(). Esa limitación es deliberada y es el punto de
partida de la clase 14.

Uso:
    python3 echo_server.py [puerto]

Probalo con echo_client.py, o con:
    nc localhost 8080
"""
import socket
import sys

HOST = '0.0.0.0'
PUERTO = int(sys.argv[1]) if len(sys.argv) > 1 else 8080


def atender(conn, direccion):
    """Devuelve todo lo que el cliente mande, hasta que cierre."""
    total = 0
    while True:
        datos = conn.recv(4096)
        if not datos:
            # recv() vacío = el otro lado cerró. Sin este chequeo,
            # el bucle giraría infinitamente consumiendo CPU.
            break
        total += len(datos)
        print(f'  [{direccion[0]}:{direccion[1]}] recv {len(datos)} bytes: {datos!r}')
        conn.sendall(datos)
    print(f'  [{direccion[0]}:{direccion[1]}] cerró tras {total} bytes')


def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as servidor:
        # Antes del bind: permite reusar el puerto aunque haya
        # conexiones en TIME_WAIT de una ejecución anterior.
        servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        servidor.bind((HOST, PUERTO))
        servidor.listen(5)
        print(f'Escuchando en {HOST}:{PUERTO} (Ctrl+C para salir)')

        while True:
            # accept() devuelve un socket NUEVO. `servidor` sigue escuchando
            # y nunca transmite datos de aplicación.
            conn, direccion = servidor.accept()
            print(f'Conexión desde {direccion}')
            try:
                with conn:
                    atender(conn, direccion)
            except (ConnectionResetError, BrokenPipeError) as e:
                # Un cliente que corta mal no debe tumbar el servidor.
                print(f'  [{direccion}] desconexión abrupta: {e}')


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('\nServidor detenido')
