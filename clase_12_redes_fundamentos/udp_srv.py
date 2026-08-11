#!/usr/bin/env python3
"""Receptor UDP para el ejercicio 6 parte C.

Muestra que UDP preserva los límites de los datagramas: cada sendto()
del cliente produce exactamente un recvfrom() acá.

Uso:
    python3 udp_srv.py

Y desde otra terminal:
    python3 -c "
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    for msg in [b'HOLA', b'COMO', b'ESTAS']:
        s.sendto(msg, ('localhost', 8080))
    "

Salida esperada: tres líneas, una por datagrama. Compará con el
comportamiento de TCP en la parte A, donde los tres envíos se fusionan.
"""
import socket

HOST, PUERTO = 'localhost', 8080

# SOCK_DGRAM = UDP. No hay listen() ni accept(): sin conexión que aceptar.
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.bind((HOST, PUERTO))
s.settimeout(5)

print(f"Esperando datagramas en {HOST}:{PUERTO} (timeout 5s)...")
try:
    while True:
        datos, origen = s.recvfrom(4096)
        print(f"recv: {datos!r} de {origen}")
except socket.timeout:
    print("(timeout, fin)")
finally:
    s.close()
