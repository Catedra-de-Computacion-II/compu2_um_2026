#!/usr/bin/env python3
"""Productor-consumidor con asyncio.Queue: la arquitectura del TP2.

Muestra el reparto entre workers, el backpressure de maxsize, y las dos
formas de apagar workers (cancelación y centinela).

Uso:
    python3 cola.py                # reparto básico
    python3 cola.py --centinela    # apagado ordenado
    python3 cola.py --presion      # qué hace maxsize con un productor rápido
"""
import asyncio
import sys
import time

TAREAS = 12
WORKERS = 3
DEMORA = 0.05

CENTINELA = object()          # marca de "no hay más trabajo"


async def procesar(tarea):
    await asyncio.sleep(DEMORA)
    return f'{tarea} ok'


async def worker(cola, wid, hechas):
    """Bucle infinito: toma de la cola hasta que lo cancelen."""
    while True:
        tarea = await cola.get()
        try:
            await procesar(tarea)
            hechas.append((wid, tarea))
        finally:
            cola.task_done()      # SIEMPRE, o join() espera para siempre


async def worker_con_centinela(cola, wid, hechas):
    """Igual, pero sale solo al recibir el centinela."""
    while True:
        item = await cola.get()
        if item is CENTINELA:
            cola.task_done()
            print(f'  worker {wid} se retira ordenadamente')
            return
        try:
            await procesar(item)
            hechas.append((wid, item))
        finally:
            cola.task_done()


async def reparto():
    print(f'=== {TAREAS} tareas de {DEMORA}s repartidas entre {WORKERS} workers ===\n')
    cola = asyncio.Queue(maxsize=5)
    hechas = []
    workers = [asyncio.create_task(worker(cola, i, hechas)) for i in range(WORKERS)]

    t0 = time.perf_counter()
    for i in range(TAREAS):
        await cola.put(f'tarea-{i}')
    await cola.join()                     # esperar a que TODAS estén hechas
    dur = time.perf_counter() - t0

    for w in workers:
        w.cancel()
    await asyncio.gather(*workers, return_exceptions=True)

    reparto_por_worker = {}
    for wid, _ in hechas:
        reparto_por_worker[wid] = reparto_por_worker.get(wid, 0) + 1

    print(f'  completadas: {len(hechas)}/{TAREAS} en {dur:.2f}s')
    print(f'  secuencial habría sido: {TAREAS * DEMORA:.2f}s')
    print(f'  reparto por worker: {dict(sorted(reparto_por_worker.items()))}')


async def con_centinela():
    print(f'=== Apagado ordenado con centinela ===\n')
    cola = asyncio.Queue()
    hechas = []
    workers = [asyncio.create_task(worker_con_centinela(cola, i, hechas))
               for i in range(WORKERS)]

    for i in range(6):
        await cola.put(f'tarea-{i}')
    # Un centinela POR worker: cada uno consume el suyo y sale
    for _ in range(WORKERS):
        await cola.put(CENTINELA)

    await asyncio.gather(*workers)        # terminan solos, sin cancelar
    print(f'\n  {len(hechas)} tareas completadas antes de salir')
    print('  Ninguna quedó a medias: es lo que el TP2 pide para SIGTERM.')


async def presion():
    print('=== Backpressure: qué hace maxsize ===\n')
    for limite in (2, 100):
        cola = asyncio.Queue(maxsize=limite)
        consumidas = []

        async def consumidor_lento():
            while True:
                item = await cola.get()
                await asyncio.sleep(0.05)      # consume lento a propósito
                consumidas.append(item)
                cola.task_done()

        c = asyncio.create_task(consumidor_lento())
        t0 = time.perf_counter()
        for i in range(10):
            await cola.put(i)                  # se frena si está llena
        tiempo_productor = time.perf_counter() - t0
        await cola.join()
        c.cancel()

        print(f'  maxsize={limite:<4} el productor tardó {tiempo_productor:.2f}s '
              f'en encolar 10 items')
    print('\n  Con maxsize chico, el productor ESPERA: la cola no crece sin control.')
    print('  Con maxsize grande, encola todo de golpe y la memoria sube.')


if __name__ == '__main__':
    if '--centinela' in sys.argv:
        asyncio.run(con_centinela())
    elif '--presion' in sys.argv:
        asyncio.run(presion())
    else:
        asyncio.run(reparto())
