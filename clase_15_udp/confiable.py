#!/usr/bin/env python3
"""Confiabilidad mínima sobre UDP: retransmisión + números de secuencia.

Muestra lo que TCP daba gratis y acá hay que escribir: reintentar cuando
se pierde, y numerar para poder descartar duplicados y respuestas viejas.

Corre cliente y servidor internamente, con pérdidas simuladas, para que
se vea funcionando sin necesidad de dos terminales.

Uso:
    python3 confiable.py            # 30% de pérdida
    python3 confiable.py 0.6        # red muy mala
"""
import random
import socket
import struct
import sys
import threading

PUERTO = 8098


# ---------------------------------------------------------------
# Protocolo: [4 bytes de secuencia][payload]
# El '!' es orden de bytes de red, igual que en el framing de la clase 13.
# Acá no delimita: numera.
# ---------------------------------------------------------------

def empaquetar(seq, payload):
    return struct.pack('!I', seq) + payload


def desempaquetar(datos):
    (seq,) = struct.unpack('!I', datos[:4])
    return seq, datos[4:]


def enviar_con_perdidas(sock, datos, destino, prob):
    """Simula la red: a veces no manda y no avisa."""
    if random.random() < prob:
        return
    sock.sendto(datos, destino)


# ---------------------------------------------------------------
# Servidor: deduplica por número de secuencia
# ---------------------------------------------------------------

def servidor(prob, listo, fin):
    vistos = {}            # seq -> respuesta ya calculada
    procesados = []        # cuántas veces se ejecutó el "trabajo" real

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(('localhost', PUERTO))
        listo.set()
        s.settimeout(0.5)
        while not fin.is_set():
            try:
                datos, origen = s.recvfrom(65535)
            except TimeoutError:
                continue
            seq, payload = desempaquetar(datos)

            if seq in vistos:
                # Duplicado: el cliente reintentó porque se perdió MI respuesta.
                # Reenviar la misma respuesta SIN volver a hacer el trabajo.
                respuesta = vistos[seq]
            else:
                procesados.append(seq)              # el trabajo real, una vez
                respuesta = payload.upper()
                vistos[seq] = respuesta

            enviar_con_perdidas(s, empaquetar(seq, respuesta), origen, prob)

    servidor.procesados = procesados


# ---------------------------------------------------------------
# Cliente: retransmite hasta obtener la respuesta correcta
# ---------------------------------------------------------------

def pedir(sock, seq, payload, destino, prob, intentos=8, timeout=0.3):
    """Manda y reintenta. Ignora respuestas cuyo seq no coincida.

    Ese filtro importa: una respuesta demorada de un pedido anterior puede
    llegar tarde, y sin el chequeo la tomaríamos como respuesta a este.
    """
    sock.settimeout(timeout)
    for intento in range(1, intentos + 1):
        enviar_con_perdidas(sock, empaquetar(seq, payload), destino, prob)
        try:
            datos, _ = sock.recvfrom(65535)
        except TimeoutError:
            continue
        seq_resp, respuesta = desempaquetar(datos)
        if seq_resp == seq:
            return respuesta, intento
        # Respuesta vieja: la descartamos y seguimos esperando la nuestra.
    return None, intentos


def main():
    prob = float(sys.argv[1]) if len(sys.argv) > 1 else 0.3
    mensajes = [b'hola', b'que', b'tal', b'todo', b'bien']

    listo, fin = threading.Event(), threading.Event()
    hilo = threading.Thread(target=servidor, args=(prob, listo, fin))
    hilo.start()
    listo.wait()

    print(f'Pérdida simulada: {prob:.0%} en cada dirección\n')
    total_intentos = 0
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        for seq, msg in enumerate(mensajes):
            respuesta, intentos = pedir(s, seq, msg, ('localhost', PUERTO), prob)
            total_intentos += intentos
            estado = respuesta.decode() if respuesta else 'SIN RESPUESTA'
            print(f'  seq={seq}  {msg.decode():<5} -> {estado:<5} '
                  f'({intentos} intento{"s" if intentos > 1 else ""})')

    fin.set(); hilo.join()

    procesados = getattr(servidor, 'procesados', [])
    print(f'\nMensajes enviados por la app:      {len(mensajes)}')
    print(f'Envíos reales (con reintentos):    {total_intentos}')
    print(f'Veces que el servidor hizo trabajo: {len(procesados)}')
    print(f'\nSin deduplicación, el servidor habría procesado {total_intentos}')
    print('pedidos en vez de', len(procesados), '- por eso hacen falta los números de secuencia.')


if __name__ == '__main__':
    main()
