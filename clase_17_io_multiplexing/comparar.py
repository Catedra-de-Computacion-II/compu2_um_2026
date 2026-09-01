#!/usr/bin/env python3
"""Compara select, poll y epoll con cantidades crecientes de conexiones.

Mide el costo de UNA llamada al multiplexor con N descriptores vigilados,
de los cuales solo unos pocos tienen datos. Es el escenario real de un
servidor: miles de conexiones abiertas, un puñado activas en cada momento.

Los números explican por qué existe epoll.

Uso:
    python3 comparar.py                # 100, 500, 1000, 2000, 5000
    python3 comparar.py 200 4000       # cantidades a medida
"""
import select
import socket
import sys
import time

REPETICIONES = 200          # llamadas al multiplexor por medición
ACTIVOS = 3                 # cuántos sockets tienen datos listos


def crear_pares(n):
    """Crea n pares de sockets conectados. Devuelve (lectores, escritores)."""
    lectores, escritores = [], []
    for _ in range(n):
        a, b = socket.socketpair()
        lectores.append(a)
        escritores.append(b)
    return lectores, escritores


def medir_select(lectores):
    try:
        t0 = time.perf_counter()
        for _ in range(REPETICIONES):
            select.select(lectores, [], [], 0)
        return (time.perf_counter() - t0) / REPETICIONES * 1e6
    except (ValueError, OSError) as e:
        # FD_SETSIZE: el límite es el NÚMERO del fd, no la cantidad
        return f'falla ({type(e).__name__})'


def medir_poll(lectores):
    p = select.poll()
    for s in lectores:
        p.register(s, select.POLLIN)
    t0 = time.perf_counter()
    for _ in range(REPETICIONES):
        p.poll(0)
    return (time.perf_counter() - t0) / REPETICIONES * 1e6


def medir_epoll(lectores):
    if not hasattr(select, 'epoll'):
        return 'no disponible'
    ep = select.epoll()
    for s in lectores:
        ep.register(s.fileno(), select.EPOLLIN)
    t0 = time.perf_counter()
    for _ in range(REPETICIONES):
        ep.poll(0)
    resultado = (time.perf_counter() - t0) / REPETICIONES * 1e6
    ep.close()
    return resultado


def fmt(v):
    return f'{v:>9.1f}' if isinstance(v, float) else f'{v:>9}'


def main():
    cantidades = [int(a) for a in sys.argv[1:]] or [100, 500, 1000, 2000, 5000]

    print(f'Costo de una llamada al multiplexor, en microsegundos.')
    print(f'{ACTIVOS} sockets con datos listos, el resto ociosos. '
          f'Promedio de {REPETICIONES} llamadas.\n')
    print(f"{'conexiones':>11} {'select':>10} {'poll':>10} {'epoll':>10}")
    print('-' * 45)

    for n in cantidades:
        lectores, escritores = crear_pares(n)
        try:
            # Solo unos pocos tienen datos: es el caso real de un servidor
            for w in escritores[:ACTIVOS]:
                w.send(b'x')

            fila = (medir_select(lectores), medir_poll(lectores),
                    medir_epoll(lectores))
            print(f'{n:>11} {fmt(fila[0])} {fmt(fila[1])} {fmt(fila[2])}')
        finally:
            for s in lectores + escritores:
                s.close()

    print('\nQué mirar:')
    print('  - select y poll crecen con el TOTAL de conexiones: son O(n).')
    print('  - epoll se mantiene plano: solo devuelve los listos, O(listos).')
    print('  - select falla cuando algún fd supera 1023 (FD_SETSIZE), aunque')
    print('    la cantidad vigilada sea chica.')
    print('\nEse salto de O(n) a O(listos) es lo que resolvió el problema C10K.')


if __name__ == '__main__':
    main()
