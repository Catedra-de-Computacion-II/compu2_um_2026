#!/usr/bin/env python3
"""Servidor y cliente eco UDP en un solo archivo.

Muestra lo mínimo de UDP: sin listen(), sin accept(), un solo socket
atendiendo a todos los clientes, y recvfrom() devolviendo el origen.

Uso:
    python3 echo_udp.py servidor [puerto]
    python3 echo_udp.py cliente  [puerto] [mensaje]
    python3 echo_udp.py tres     [puerto]      # tres sendto(): ver los límites

Probá también con netcat:
    nc -u localhost 8080
"""
import socket
import sys

PUERTO = 8080


def servidor(puerto):
    """Un socket, todos los clientes. No hay accept() porque no hay conexión."""
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(('0.0.0.0', puerto))
        print(f'Escuchando UDP en 0.0.0.0:{puerto} (Ctrl+C para salir)')
        n = 0
        while True:
            # 65535 = el datagrama más grande posible. Con un buffer chico,
            # lo que no entra se DESCARTA (no queda para el próximo recvfrom).
            datos, origen = s.recvfrom(65535)
            n += 1
            print(f'  [{n}] recvfrom {len(datos):>5} bytes de '
                  f'{origen[0]}:{origen[1]}: {datos[:60]!r}')
            s.sendto(datos, origen)          # responder al remitente


def cliente(puerto, mensaje):
    """Sin connect(): sendto() lleva el destino en cada llamada."""
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        # Sin timeout, un recvfrom() contra un servidor caído espera para
        # siempre: en UDP no hay cierre de conexión que detectar.
        s.settimeout(2.0)
        s.sendto(mensaje, ('localhost', puerto))
        print(f'puerto efímero asignado: {s.getsockname()[1]}')
        try:
            respuesta, origen = s.recvfrom(65535)
            print(f'eco de {origen}: {respuesta!r}')
        except TimeoutError:
            print('Sin respuesta en 2s. ¿Está corriendo el servidor?')


def tres(puerto):
    """Tres sendto() -> tres recvfrom(). UDP preserva los límites."""
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.settimeout(2.0)
        for msg in (b'HOLA', b'COMO', b'ESTAS'):
            s.sendto(msg, ('localhost', puerto))
        recibidos = []
        try:
            for _ in range(3):
                datos, _ = s.recvfrom(65535)
                recibidos.append(datos)
        except TimeoutError:
            pass
        print(f'enviados:  [b\'HOLA\', b\'COMO\', b\'ESTAS\']')
        print(f'recibidos: {recibidos}')
        print('Compará con TCP (clase 13), donde los tres llegaban fusionados.')


if __name__ == '__main__':
    modo = sys.argv[1] if len(sys.argv) > 1 else 'servidor'
    puerto = int(sys.argv[2]) if len(sys.argv) > 2 else PUERTO
    try:
        if modo == 'servidor':
            servidor(puerto)
        elif modo == 'tres':
            tres(puerto)
        else:
            msg = sys.argv[3].encode() if len(sys.argv) > 3 else b'hola mundo'
            cliente(puerto, msg)
    except KeyboardInterrupt:
        print('\nCortado')
