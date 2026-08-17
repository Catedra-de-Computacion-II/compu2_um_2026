#!/usr/bin/env python3
"""Servidor eco secuencial: la línea de base contra la que comparar.

Atiende UN cliente a la vez. Es el servidor de la clase 13, incluido acá
para poder medirlo con benchmark.py junto a las otras estrategias.

Uso:
    python3 server_secuencial.py [puerto] [--lento SEGUNDOS]

    --lento simula trabajo por cliente; con él la limitación se vuelve
    imposible de ignorar.
"""
import socket
import sys
import time

HOST = '0.0.0.0'
PUERTO = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 8080
LENTO = float(sys.argv[sys.argv.index('--lento') + 1]) if '--lento' in sys.argv else 0.0


def atender(conn, direccion):
    if LENTO:
        time.sleep(LENTO)          # simula trabajo pesado
    while True:
        datos = conn.recv(4096)
        if not datos:
            break
        conn.sendall(datos)


def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as servidor:
        servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        servidor.bind((HOST, PUERTO))
        servidor.listen(128)
        print(f'[secuencial] escuchando en {HOST}:{PUERTO}'
              f'{f" (lento: {LENTO}s por cliente)" if LENTO else ""}')

        while True:
            conn, direccion = servidor.accept()
            # Todo el trabajo ocurre acá: el bucle no vuelve a accept()
            # hasta que este cliente termina. Los demás esperan en la cola.
            try:
                with conn:
                    atender(conn, direccion)
            except (ConnectionResetError, BrokenPipeError):
                pass


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('\nServidor detenido')
