#!/usr/bin/env python3
"""Mide un servidor eco lanzando N clientes simultáneos.

Los números dependen de tu máquina; lo que importa es comparar las
cuatro estrategias entre sí, sobre todo con servidores lentos.

Uso:
    # Terminal 1
    python3 server_secuencial.py --lento 1

    # Terminal 2
    python3 benchmark.py --clientes 20

Compará después contra server_threads.py, server_fork.py y server_pool.py
levantados con el mismo --lento.
"""
import argparse
import socket
import statistics
import time
from concurrent.futures import ThreadPoolExecutor


def un_cliente(host, puerto, mensaje, timeout):
    """Conecta, manda, espera el eco. Devuelve (ok, segundos, error)."""
    inicio = time.perf_counter()
    try:
        with socket.create_connection((host, puerto), timeout=timeout) as s:
            s.sendall(mensaje)
            recibido = b''
            while len(recibido) < len(mensaje):
                pedazo = s.recv(4096)
                if not pedazo:
                    break
                recibido += pedazo
        ok = recibido == mensaje
        return ok, time.perf_counter() - inicio, None if ok else 'eco incompleto'
    except Exception as e:
        return False, time.perf_counter() - inicio, type(e).__name__


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--host', default='localhost')
    ap.add_argument('--puerto', type=int, default=8080)
    ap.add_argument('--clientes', type=int, default=50)
    ap.add_argument('--timeout', type=float, default=30.0)
    args = ap.parse_args()

    mensaje = b'x' * 256
    print(f'Lanzando {args.clientes} clientes simultáneos '
          f'contra {args.host}:{args.puerto}\n')

    inicio = time.perf_counter()
    # Todos los clientes arrancan a la vez: es lo que estresa al servidor.
    with ThreadPoolExecutor(max_workers=args.clientes) as pool:
        resultados = list(pool.map(
            lambda _: un_cliente(args.host, args.puerto, mensaje, args.timeout),
            range(args.clientes)))
    total = time.perf_counter() - inicio

    ok = [r for r in resultados if r[0]]
    fallidos = [r for r in resultados if not r[0]]
    latencias = sorted(r[1] for r in ok)

    print(f'{"Completados:":<22} {len(ok)}/{args.clientes}')
    print(f'{"Tiempo total:":<22} {total:.2f}s')
    if latencias:
        print(f'{"Latencia mínima:":<22} {latencias[0]:.3f}s')
        print(f'{"Latencia mediana:":<22} {statistics.median(latencias):.3f}s')
        print(f'{"Latencia máxima:":<22} {latencias[-1]:.3f}s')
        print(f'{"Throughput:":<22} {len(ok) / total:.1f} clientes/s')
    if fallidos:
        from collections import Counter
        print(f'\nFallidos: {len(fallidos)}')
        for motivo, n in Counter(r[2] for r in fallidos).items():
            print(f'  {motivo}: {n}')

    # La firma de un servidor secuencial: latencias escalonadas.
    if len(latencias) >= 4:
        salto = latencias[-1] - latencias[0]
        if salto > 0.5 * latencias[-1]:
            print(f'\nNota: la latencia va de {latencias[0]:.2f}s a '
                  f'{latencias[-1]:.2f}s — los clientes fueron atendidos '
                  f'en serie, no en paralelo.')


if __name__ == '__main__':
    main()
