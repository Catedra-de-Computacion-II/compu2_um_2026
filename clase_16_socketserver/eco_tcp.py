#!/usr/bin/env python3
"""Servidor eco TCP con socketserver: 12 líneas para lo que en la clase 14
nos llevó 60.

Compará con server_threads.py de la clase 14: acá no hay bucle de accept,
ni manejo explícito de threads, ni setsockopt, ni cierre de conexiones.

Uso:
    python3 eco_tcp.py [puerto]
    python3 eco_tcp.py --fork [puerto]     # un proceso por cliente

Probalo con:  nc localhost 8080
"""
import os
import socketserver
import sys
import threading


class EchoHandler(socketserver.StreamRequestHandler):
    """Una instancia NUEVA por cada conexión."""

    def handle(self):
        quien = f'{self.client_address[0]}:{self.client_address[1]}'
        # Con fork, os.getpid() cambia; con threads, cambia el nombre del hilo.
        contexto = f'pid={os.getpid()} hilo={threading.current_thread().name}'
        print(f'+ {quien}  ({contexto})')

        # rfile/wfile son objetos tipo archivo sobre el socket: el framing
        # por líneas viene gratis, que es lo que en la clase 13 nos costó
        # implementar a mano con un buffer.
        for linea in self.rfile:
            self.wfile.write(linea)

        print(f'- {quien} cerró')


class ServidorThreads(socketserver.ThreadingTCPServer):
    allow_reuse_address = True      # el SO_REUSEADDR de la clase 13
    daemon_threads = True           # sin esto, Ctrl+C espera a los clientes


class ServidorFork(socketserver.ForkingTCPServer):
    allow_reuse_address = True
    max_children = 40               # ForkingMixIn cosecha los hijos solo


if __name__ == '__main__':
    usar_fork = '--fork' in sys.argv
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    puerto = int(args[0]) if args else 8080

    Servidor = ServidorFork if usar_fork else ServidorThreads
    modo = 'un proceso por cliente' if usar_fork else 'un thread por cliente'

    with Servidor(('0.0.0.0', puerto), EchoHandler) as srv:
        print(f'Escuchando en 0.0.0.0:{puerto} — {modo}')
        print(f'MRO: {" -> ".join(c.__name__ for c in Servidor.__mro__[:4])}')
        try:
            srv.serve_forever()
        except KeyboardInterrupt:
            print('\nServidor detenido')
