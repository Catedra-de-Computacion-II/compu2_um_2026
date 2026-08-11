#!/usr/bin/env python3
"""Las dos estrategias de framing sobre TCP, comparadas.

Ejecuta ambas contra un servidor interno y muestra que los mensajes
se recuperan intactos aunque TCP los haya fusionado o partido.

Uso:
    python3 framing.py
"""
import socket
import struct
import threading


# --------------------------------------------------------------------
# Estrategia 1: delimitador (\n)
# --------------------------------------------------------------------

def recibir_lineas(sock):
    """Generador de líneas completas. El buffer es imprescindible:
    un recv() puede traer media línea, o tres líneas y media."""
    buffer = b''
    while True:
        pedazo = sock.recv(4096)
        if not pedazo:
            if buffer:
                print(f'  (descartado incompleto: {buffer!r})')
            return
        buffer += pedazo
        # Puede haber MÁS DE UNA línea completa en el buffer.
        while b'\n' in buffer:
            linea, buffer = buffer.split(b'\n', 1)
            yield linea


def enviar_linea(sock, texto: bytes):
    sock.sendall(texto + b'\n')


# --------------------------------------------------------------------
# Estrategia 2: prefijo de longitud
# --------------------------------------------------------------------

def recibir_exacto(sock, n):
    """Lee EXACTAMENTE n bytes, o None si cerraron antes.

    Sin este bucle el protocolo se desincroniza para siempre: recv(4)
    puede devolver 2 bytes y el resto se interpretaría como cabecera.
    """
    datos = b''
    while len(datos) < n:
        pedazo = sock.recv(n - len(datos))
        if not pedazo:
            return None
        datos += pedazo
    return datos


def enviar_mensaje(sock, payload: bytes):
    """Longitud en 4 bytes big-endian ('!' = orden de red) + contenido."""
    sock.sendall(struct.pack('!I', len(payload)) + payload)


def recibir_mensaje(sock):
    cabecera = recibir_exacto(sock, 4)
    if cabecera is None:
        return None
    (longitud,) = struct.unpack('!I', cabecera)
    return recibir_exacto(sock, longitud)


# --------------------------------------------------------------------
# Demostración
# --------------------------------------------------------------------

MENSAJES = [b'HOLA', b'COMO', b'ESTAS', b'un mensaje bastante mas largo']


def servidor(puerto, modo, resultados):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as srv:
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind(('localhost', puerto))
        srv.listen(1)
        conn, _ = srv.accept()
        with conn:
            if modo == 'lineas':
                resultados.extend(recibir_lineas(conn))
            else:
                while (msg := recibir_mensaje(conn)) is not None:
                    resultados.append(msg)


def probar(modo, puerto):
    print(f'--- Framing por {modo} ---')
    recibidos = []
    hilo = threading.Thread(target=servidor, args=(puerto, modo, recibidos))
    hilo.start()

    # Envío todo de corrido: TCP con toda probabilidad lo fusiona.
    with socket.create_connection(('localhost', puerto), timeout=5) as s:
        for m in MENSAJES:
            if modo == 'lineas':
                enviar_linea(s, m)
            else:
                enviar_mensaje(s, m)
    hilo.join()

    print(f'  Enviados:  {MENSAJES}')
    print(f'  Recibidos: {recibidos}')
    print(f'  {"OK: mensajes intactos" if recibidos == MENSAJES else "ERROR"}\n')


if __name__ == '__main__':
    probar('lineas', 8091)
    probar('longitud', 8092)
    print('En ambos casos TCP entregó un flujo continuo;')
    print('el framing es lo que reconstruyó los límites.')
