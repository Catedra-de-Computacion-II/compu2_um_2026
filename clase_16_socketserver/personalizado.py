#!/usr/bin/env python3
"""Los ganchos del ciclo de vida: verify_request, handle_error, IPv6.

Imprime cada paso a medida que ocurre, para que se vea el orden real:
server_bind -> server_activate -> get_request -> verify_request ->
process_request -> setup -> handle -> finish -> shutdown_request

Uso:
    python3 personalizado.py [puerto]
    python3 personalizado.py --v6 [puerto]      # IPv6 (dual-stack)
    python3 personalizado.py --bloquear [puerto]  # rechaza localhost
"""
import socket
import socketserver
import sys


class Handler(socketserver.StreamRequestHandler):

    def setup(self):
        print(f'    setup()   {self.client_address}')
        super().setup()

    def handle(self):
        print(f'    handle()  {self.client_address}')
        datos = self.rfile.readline()
        if datos.strip() == b'CRASH':
            # A propósito: demuestra que handle_error atrapa la excepción
            # y el servidor sigue sirviendo.
            raise RuntimeError('el cliente pidió que explote')
        self.wfile.write(b'OK: ' + datos)

    def finish(self):
        print(f'    finish()  {self.client_address}')
        super().finish()


class Servidor(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True
    bloquear_local = False

    def server_bind(self):
        print('  server_bind()')
        super().server_bind()

    def server_activate(self):
        print('  server_activate()')
        super().server_activate()

    def verify_request(self, request, client_address):
        """Gancho para rechazar ANTES de crear el handler.
        Devolver False cierra la conexión sin llamar a handle()."""
        permitido = not (self.bloquear_local and
                         client_address[0] in ('127.0.0.1', '::1'))
        print(f'  verify_request({client_address[0]}) -> {permitido}')
        return permitido

    def handle_error(self, request, client_address):
        """Si handle() lanza, el servidor NO se cae: loguea y sigue."""
        import traceback
        print(f'  handle_error({client_address}): '
              f'{traceback.format_exc().strip().splitlines()[-1]}')
        print('  (el servidor sigue atendiendo)')


class ServidorV6(Servidor):
    address_family = socket.AF_INET6      # basta cambiar el atributo

    def server_bind(self):
        # Dual-stack: aceptar también IPv4 (clase 15). Explícito porque el
        # default varía entre sistemas operativos.
        self.socket.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
        super().server_bind()


if __name__ == '__main__':
    usar_v6 = '--v6' in sys.argv
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    puerto = int(args[0]) if args else 8080

    Clase = ServidorV6 if usar_v6 else Servidor
    Clase.bloquear_local = '--bloquear' in sys.argv
    direccion = ('::', puerto) if usar_v6 else ('0.0.0.0', puerto)

    print(f'Construyendo {Clase.__name__} en {direccion}')
    with Clase(direccion, Handler) as srv:
        print(f'Listo. Mandá "CRASH" para ver handle_error.')
        try:
            srv.serve_forever()
        except KeyboardInterrupt:
            print('\nServidor detenido')
