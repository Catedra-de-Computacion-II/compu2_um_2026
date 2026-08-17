#!/usr/bin/env python3
"""Servidor eco con pool de threads acotado.

El consumo de recursos tiene techo, pero con conexiones persistentes
cada cliente ocupa un worker durante toda su sesión: el cliente
MAX_WORKERS+1 espera sin ser rechazado. Probalo con --lento y más
clientes que workers para verlo.

Uso:
    python3 server_pool.py [puerto] [--workers N] [--lento SEGUNDOS]
"""
import socket
import sys
import time
from concurrent.futures import ThreadPoolExecutor

HOST = '0.0.0.0'
PUERTO = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 8080
LENTO = float(sys.argv[sys.argv.index('--lento') + 1]) if '--lento' in sys.argv else 0.0
MAX_WORKERS = int(sys.argv[sys.argv.index('--workers') + 1]) if '--workers' in sys.argv else 20


def atender(conn, direccion):
    if LENTO:
        time.sleep(LENTO)
    with conn:
        while True:
            datos = conn.recv(4096)
            if not datos:
                break
            conn.sendall(datos)


def atender_seguro(conn, direccion):
    """pool.submit() se traga las excepciones dentro del Future.

    Sin este wrapper, un error en atender() desaparece sin dejar rastro.
    """
    try:
        atender(conn, direccion)
    except (ConnectionResetError, BrokenPipeError):
        pass
    except Exception as e:
        print(f'[{direccion}] error: {e!r}')


def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as servidor:
        servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        servidor.bind((HOST, PUERTO))
        servidor.listen(128)
        print(f'[pool] escuchando en {HOST}:{PUERTO} con {MAX_WORKERS} workers'
              f'{f" (lento: {LENTO}s por cliente)" if LENTO else ""}')

        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
            while True:
                conn, direccion = servidor.accept()
                pool.submit(atender_seguro, conn, direccion)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('\nServidor detenido')
