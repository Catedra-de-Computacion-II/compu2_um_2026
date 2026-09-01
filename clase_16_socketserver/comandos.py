#!/usr/bin/env python3
"""Servidor de comandos con estado compartido entre handlers.

Muestra el problema que aparece apenas el servidor deja de ser un eco:
como cada conexión crea un handler NUEVO, el estado común vive en el
servidor, y con ThreadingTCPServer eso significa acceso concurrente.
De ahí el Lock: es la clase 11 otra vez, escondida detrás del mixin.

Comandos: TIME, ECHO <texto>, QUIEN, CONTADOR, AYUDA, QUIT

Uso:
    python3 comandos.py [puerto]
    nc localhost 8080
"""
import socketserver
import sys
import threading
import time


class Handler(socketserver.StreamRequestHandler):

    def setup(self):
        """Se llama ANTES de handle(). Acá se abren rfile/wfile."""
        super().setup()               # imprescindible: crea rfile/wfile
        with self.server.lock:
            self.server.conexiones += 1
            self.server.activos.add(self.client_address)

    def finish(self):
        """Se llama DESPUÉS de handle(), incluso si hubo excepción."""
        with self.server.lock:
            self.server.activos.discard(self.client_address)
        super().finish()

    def responder(self, texto):
        self.wfile.write((texto + '\n').encode())

    def handle(self):
        self.responder('Servidor de comandos. Escribí AYUDA.')
        for linea in self.rfile:                    # framing por líneas
            partes = linea.decode('utf-8', 'replace').strip().split(maxsplit=1)
            if not partes:
                continue
            cmd, resto = partes[0].upper(), (partes[1] if len(partes) > 1 else '')

            if cmd == 'TIME':
                self.responder(time.strftime('%Y-%m-%d %H:%M:%S'))
            elif cmd == 'ECHO':
                self.responder(resto)
            elif cmd == 'QUIEN':
                with self.server.lock:              # lectura también protegida
                    activos = sorted(f'{h}:{p}' for h, p in self.server.activos)
                self.responder(f'{len(activos)} conectados: ' + ', '.join(activos))
            elif cmd == 'CONTADOR':
                with self.server.lock:
                    n = self.server.conexiones
                self.responder(f'Conexiones totales desde el arranque: {n}')
            elif cmd == 'AYUDA':
                self.responder('TIME | ECHO <texto> | QUIEN | CONTADOR | QUIT')
            elif cmd == 'QUIT':
                self.responder('Chau')
                return                              # cierra la conexión
            else:
                self.responder(f'Comando desconocido: {cmd}')

    def handle_error(self, *args):
        """Si handle() explota, el servidor NO se cae."""
        print(f'Error atendiendo a {self.client_address}')


class Servidor(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # El estado compartido vive acá, no en el handler: cada conexión
        # crea un handler nuevo y su estado moriría con ella.
        self.conexiones = 0
        self.activos = set()
        # Con ThreadingMixIn los handlers corren en threads distintos sobre
        # este mismo objeto. Sin lock, hay race condition (clase 11).
        self.lock = threading.Lock()


if __name__ == '__main__':
    puerto = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    with Servidor(('0.0.0.0', puerto), Handler) as srv:
        print(f'Escuchando en 0.0.0.0:{puerto}')
        print('Probá: nc localhost', puerto)
        try:
            srv.serve_forever()
        except KeyboardInterrupt:
            print('\nServidor detenido')
