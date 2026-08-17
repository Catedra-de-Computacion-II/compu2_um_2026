#!/usr/bin/env python3
"""Servidor eco: un proceso por cliente, con fork().

El patrón clásico de Unix. Presta atención a los tres cierres de
descriptores y a la cosecha de zombies: son las tres cosas que casi
todos olvidan, y las tres producen bugs difíciles de diagnosticar.

Uso:
    python3 server_fork.py [puerto] [--lento SEGUNDOS]
"""
import os
import signal
import socket
import sys
import time

HOST = '0.0.0.0'
PUERTO = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 8080
LENTO = float(sys.argv[sys.argv.index('--lento') + 1]) if '--lento' in sys.argv else 0.0


def cosechar(signum, frame):
    """Recoge hijos terminados sin bloquear.

    El bucle es necesario: varias señales SIGCHLD pueden colapsar en una
    sola, así que un handler que recoge un único hijo deja zombies.
    """
    while True:
        try:
            pid, _status = os.waitpid(-1, os.WNOHANG)
            if pid == 0:
                break
        except ChildProcessError:
            break


def atender(conn):
    if LENTO:
        time.sleep(LENTO)
    while True:
        datos = conn.recv(4096)
        if not datos:
            break
        conn.sendall(datos)


def main():
    # Alternativa más simple: signal.signal(SIGCHLD, SIG_IGN) delega la
    # cosecha al kernel. Acá usamos el handler explícito para verlo.
    signal.signal(signal.SIGCHLD, cosechar)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as servidor:
        servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        servidor.bind((HOST, PUERTO))
        servidor.listen(128)
        print(f'[fork] PADRE pid={os.getpid()} escuchando en {HOST}:{PUERTO}'
              f'{f" (lento: {LENTO}s por cliente)" if LENTO else ""}')

        while True:
            try:
                conn, direccion = servidor.accept()
            except InterruptedError:
                # accept() puede ser interrumpido por SIGCHLD; reintentar.
                continue

            pid = os.fork()

            if pid == 0:
                # ---- HIJO ----
                servidor.close()     # (2) no necesita el socket que escucha
                try:
                    atender(conn)
                except (ConnectionResetError, BrokenPipeError):
                    pass
                finally:
                    conn.close()
                    os._exit(0)      # salir sin correr cleanup del padre
            else:
                # ---- PADRE ----
                # (1) CRÍTICO: si el padre no cierra su copia, la conexión
                # nunca se cierra del todo y se filtran descriptores.
                conn.close()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('\nServidor detenido')
