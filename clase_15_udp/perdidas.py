#!/usr/bin/env python3
"""Simulador de red con pérdidas, para ver UDP comportarse como en la realidad.

En localhost no se pierde nada, así que sin esto la clase de UDP parece
teórica. Acá el envío miente: dice que mandó y no manda, que es exactamente
lo que se ve desde el programa cuando la red descarta un paquete.

Para pérdidas REALES (mejor, si podés usar sudo):
    sudo tc qdisc add dev lo root netem loss 30%
    sudo tc qdisc del dev lo root          # acordate de sacarlo

Uso:
    python3 perdidas.py            # demo: 200 datagramas con 30% de pérdida
    python3 perdidas.py 0.5        # con la probabilidad que quieras
"""
import random
import socket
import sys
import threading


def sendto_con_perdidas(sock, datos, destino, prob_perdida=0.3):
    """sendto() que descarta datagramas al azar.

    Devuelve len(datos) igual que el sendto() real: el emisor NO puede
    distinguir un envío exitoso de uno perdido. Esa es la característica
    central de UDP y la razón por la que hace falta un timeout del otro lado.
    """
    if random.random() < prob_perdida:
        return len(datos)                    # miente
    return sock.sendto(datos, destino)


def receptor(puerto, total, recibidos, listo):
    """Cuenta cuántos datagramas llegan realmente."""
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(('localhost', puerto))
        listo.set()
        s.settimeout(2.0)
        while True:
            try:
                datos, _ = s.recvfrom(65535)
            except TimeoutError:
                return
            recibidos.append(int(datos.split(b'#')[1]))


def main():
    prob = float(sys.argv[1]) if len(sys.argv) > 1 else 0.3
    puerto, total = 8099, 200

    recibidos = []
    listo = threading.Event()
    hilo = threading.Thread(target=receptor, args=(puerto, total, recibidos, listo))
    hilo.start()
    listo.wait()

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        for i in range(total):
            sendto_con_perdidas(s, b'dato#%d' % i, ('localhost', puerto), prob)
    hilo.join()

    perdidos = total - len(recibidos)
    print(f'Enviados:  {total}')
    print(f'Recibidos: {len(recibidos)}')
    print(f'Perdidos:  {perdidos} ({perdidos / total:.0%}, configurado {prob:.0%})')

    # Los que faltan: la aplicación no tiene forma de enterarse por sí sola.
    faltantes = sorted(set(range(total)) - set(recibidos))
    print(f'\nPrimeros faltantes: {faltantes[:12]}')
    print('El emisor no recibió ningún error: para él, los 200 se enviaron bien.')

    # Además de perderse, pueden llegar desordenados: verificarlo.
    desordenados = sum(1 for a, b in zip(recibidos, recibidos[1:]) if b < a)
    print(f'Saltos hacia atrás en el orden de llegada: {desordenados}')


if __name__ == '__main__':
    main()
