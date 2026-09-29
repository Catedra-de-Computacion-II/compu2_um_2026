#!/usr/bin/env python3
"""HTTP sin frameworks: hablarlo a mano y servirlo con la stdlib.

Primero muestra que http.server ES socketserver (clase 16) con un handler
que entiende HTTP. Después levanta un servidor y le habla por socket
pelado, para ver el protocolo tal como viaja.

Uso:
    python3 crudo.py            # la demostración completa
    python3 crudo.py servidor   # solo el servidor, para probarlo con nc
"""
import http.server
import json
import socket
import socketserver
import sys
import threading
import time

PUERTO = 8080


def mostrar_jerarquia():
    """http.server no inventa nada: es socketserver con HTTP encima."""
    print('=' * 66)
    print('1. De qué está hecho http.server')
    print('=' * 66)
    for clase in (http.server.HTTPServer,
                  http.server.ThreadingHTTPServer,
                  http.server.BaseHTTPRequestHandler):
        bases = ', '.join(b.__name__ for b in clase.__bases__)
        print(f'  {clase.__name__:<24} -> {bases}')
    print('\n  Todo viene de la clase 16: TCPServer, ThreadingMixIn y')
    print('  StreamRequestHandler (el que trae rfile/wfile con framing).')


class Handler(http.server.BaseHTTPRequestHandler):
    """El framework llama a do_GET o do_POST según el método del pedido."""

    def _responder(self, codigo, datos):
        cuerpo = json.dumps(datos).encode()
        self.send_response(codigo)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(cuerpo)))   # framing
        self.end_headers()
        self.wfile.write(cuerpo)

    def do_GET(self):
        self._responder(200, {'metodo': 'GET', 'ruta': self.path})

    def do_POST(self):
        # Hay que leer EXACTAMENTE Content-Length bytes: después de eso
        # empieza el pedido siguiente en la misma conexión (keep-alive).
        n = int(self.headers.get('Content-Length', 0))
        cuerpo = self.rfile.read(n)
        self._responder(201, {'metodo': 'POST', 'recibido': cuerpo.decode()})

    def log_message(self, formato, *args):
        pass                      # silenciar el log por defecto


def hablar_http_a_mano(puerto):
    """Un pedido HTTP escrito byte por byte sobre un socket."""
    print('\n' + '=' * 66)
    print('2. Un pedido HTTP escrito a mano')
    print('=' * 66)

    pedido = (
        b'GET /tareas/42 HTTP/1.1\r\n'
        b'Host: localhost\r\n'
        b'Accept: application/json\r\n'
        b'Connection: close\r\n'
        b'\r\n'                      # línea vacía: acá terminan los headers
    )
    print('  --- lo que mandamos ---')
    print('  ' + pedido.decode().replace('\r\n', '\\r\\n\n  ').rstrip())

    with socket.create_connection(('localhost', puerto), timeout=5) as s:
        s.sendall(pedido)
        respuesta = b''
        while True:
            pedazo = s.recv(4096)
            if not pedazo:
                break
            respuesta += pedazo

    print('\n  --- lo que volvió ---')
    cabeza, _, cuerpo = respuesta.partition(b'\r\n\r\n')
    for linea in cabeza.decode().splitlines():
        print(f'  {linea}')
    print(f'  (línea vacía)')
    print(f'  {cuerpo.decode()}')
    print('\n  Ojo con la primera línea: pedimos HTTP/1.1 y respondió 1.0.')
    print('  BaseHTTPRequestHandler usa 1.0 por defecto; se cambia con')
    print('  protocol_version = "HTTP/1.1" (y entonces keep-alive funciona).')
    print('\n  Tres partes: línea de estado, headers, cuerpo.')
    print('  Los headers terminan en una línea vacía: framing por delimitador.')
    print('  El cuerpo se mide con Content-Length: framing por longitud.')
    print('  Son los dos métodos de la clase 13.')


def main():
    if len(sys.argv) > 1 and sys.argv[1] == 'servidor':
        with http.server.ThreadingHTTPServer(('', PUERTO), Handler) as srv:
            print(f'Escuchando en http://localhost:{PUERTO}')
            print('Probá:  curl localhost:8080/hola')
            print('        printf "GET / HTTP/1.1\\r\\nHost: x\\r\\n\\r\\n" | nc localhost 8080')
            srv.serve_forever()
        return

    mostrar_jerarquia()

    servidor = http.server.ThreadingHTTPServer(('', PUERTO), Handler)
    hilo = threading.Thread(target=servidor.serve_forever, daemon=True)
    hilo.start()
    time.sleep(0.3)
    try:
        hablar_http_a_mano(PUERTO)
    finally:
        servidor.shutdown()
        servidor.server_close()


if __name__ == '__main__':
    main()
