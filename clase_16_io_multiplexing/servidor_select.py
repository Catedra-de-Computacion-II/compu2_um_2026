#!/usr/bin/env python3
"""Servidor eco con select(): un solo hilo, muchos clientes.

Compará con los cuatro servidores de la clase 14: acá no hay threads,
procesos, locks ni zombies. Un proceso, un hilo, N clientes.

Uso:
    python3 servidor_select.py [puerto]

Probalo con varios clientes a la vez:
    nc localhost 8080        (en varias terminales)
"""
import select
import socket
import sys

PUERTO = int(sys.argv[1]) if len(sys.argv) > 1 else 8080


def main():
    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    servidor.bind(('0.0.0.0', PUERTO))
    servidor.listen(128)
    print(f'Escuchando en 0.0.0.0:{PUERTO} (un solo hilo)')

    # El socket que escucha se vigila igual que los demás: "listo para
    # leer" significa que hay una conexión esperando en accept().
    vigilados = [servidor]
    direcciones = {}

    try:
        while True:
            # Bloquea acá hasta que ALGUNO esté listo. Sin busy-waiting:
            # el proceso duerme y no consume CPU mientras espera.
            listos, _, _ = select.select(vigilados, [], [])

            for sock in listos:
                if sock is servidor:
                    conn, direccion = servidor.accept()
                    conn.setblocking(False)
                    vigilados.append(conn)
                    direcciones[conn] = direccion
                    print(f'+ cliente {direccion}  (total: {len(vigilados) - 1})')
                else:
                    datos = sock.recv(4096)
                    if datos:
                        sock.sendall(datos)
                    else:
                        # recv() vacío = cerró. Sacarlo de la lista es
                        # obligatorio: si no, select() lo reportaría listo
                        # para siempre y giraríamos en un bucle infinito.
                        vigilados.remove(sock)
                        d = direcciones.pop(sock, '?')
                        sock.close()
                        print(f'- cliente {d}  (total: {len(vigilados) - 1})')
    except KeyboardInterrupt:
        print('\nServidor detenido')
    finally:
        for s in vigilados:
            s.close()


if __name__ == '__main__':
    main()
