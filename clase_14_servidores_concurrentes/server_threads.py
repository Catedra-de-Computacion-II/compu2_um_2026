#!/usr/bin/env python3
"""Servidor eco: un thread por cliente.

El cambio respecto del secuencial son tres líneas: el bucle principal
delega y vuelve inmediatamente a accept().

Uso:
    python3 server_threads.py [puerto] [--lento SEGUNDOS]
"""
import socket
import sys
import threading
import time

HOST = '0.0.0.0'
PUERTO = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 8080
LENTO = float(sys.argv[sys.argv.index('--lento') + 1]) if '--lento' in sys.argv else 0.0

# Estado compartido entre threads: necesita lock (clase 11).
clientes_activos = 0
pico_simultaneos = 0
lock = threading.Lock()


def atender(conn, direccion):
    """Corre en su propio thread, uno por cliente."""
    global clientes_activos, pico_simultaneos
    with lock:
        clientes_activos += 1
        pico_simultaneos = max(pico_simultaneos, clientes_activos)
    try:
        if LENTO:
            time.sleep(LENTO)
        with conn:
            while True:
                datos = conn.recv(4096)
                if not datos:
                    break
                conn.sendall(datos)
    except (ConnectionResetError, BrokenPipeError):
        pass
    finally:
        with lock:
            clientes_activos -= 1


def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as servidor:
        servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        servidor.bind((HOST, PUERTO))
        servidor.listen(128)
        print(f'[threads] escuchando en {HOST}:{PUERTO}'
              f'{f" (lento: {LENTO}s por cliente)" if LENTO else ""}')

        while True:
            conn, direccion = servidor.accept()
            # daemon=True: los threads no impiden que el programa termine.
            hilo = threading.Thread(target=atender, args=(conn, direccion),
                                    daemon=True)
            hilo.start()
            # El bucle vuelve INMEDIATAMENTE a accept()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print(f'\nServidor detenido. Pico de clientes simultáneos: {pico_simultaneos}')
