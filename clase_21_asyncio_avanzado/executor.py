#!/usr/bin/env python3
"""Qué le pasa al event loop cuando una corrutina se pone a calcular.

Mide el "atraso del loop": una tarea que debería despertarse cada 50 ms
y cuánto tarda realmente. Si el loop está bloqueado, se nota ahí.

Es la medición que el TP2 pide hacer.

Uso:
    python3 executor.py              # las tres formas
    python3 executor.py --paralelo   # threads contra procesos, 4 tareas
"""
import asyncio
import hashlib
import sys
import time
from concurrent.futures import ProcessPoolExecutor

VUELTAS = 3_000_000          # ~5 segundos de CPU
LATIDO = 0.05                # cada cuánto debería despertarse el medidor


def hashear(etiqueta=''):
    """Trabajo CPU-bound puro: no cede el control a nadie."""
    h = b'x'
    for _ in range(VUELTAS):
        h = hashlib.sha256(h).digest()
    return h.hex()[:8]


async def medidor(muestras, parar):
    """Debería despertarse cada LATIDO. Si el loop está bloqueado, se atrasa."""
    while not parar.is_set():
        t0 = time.perf_counter()
        await asyncio.sleep(LATIDO)
        muestras.append((time.perf_counter() - t0 - LATIDO) * 1000)


async def medir(etiqueta, trabajo):
    muestras = []
    parar = asyncio.Event()
    tarea = asyncio.create_task(medidor(muestras, parar))
    await asyncio.sleep(0.2)                   # que el medidor arranque

    t0 = time.perf_counter()
    await trabajo()
    duracion = time.perf_counter() - t0

    parar.set()
    await asyncio.sleep(0.1)
    tarea.cancel()
    try:
        await tarea
    except asyncio.CancelledError:
        pass

    peor = max(muestras) if muestras else 0
    print(f'  {etiqueta:<32} {duracion:5.2f}s  |  peor atraso: {peor:8.1f} ms')
    return peor


async def directo():
    hashear()                                   # dentro del loop: lo bloquea


async def con_proceso(pool):
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(pool, hashear)   # en otro proceso


async def con_thread():
    await asyncio.to_thread(hashear)            # en otro thread


async def tres_formas():
    print('Un cálculo de ~5s, y cuánto se atrasa el event loop mientras tanto:\n')
    await medir('sin executor', directo)
    with ProcessPoolExecutor(max_workers=2) as pool:
        await medir('con ProcessPoolExecutor', lambda: con_proceso(pool))
    await medir('con asyncio.to_thread', con_thread)

    print('\n  Sin executor el loop queda congelado TODO el cálculo: ningún')
    print('  pedido se atiende, ningún timeout se dispara, nada avanza.')
    print('  Con executor el trabajo tarda lo mismo pero no bloquea a nadie.')
    print('\n  Esta es la medición 2 que pide el TP2.')


async def paralelo():
    """Con UNA tarea threads y procesos empatan. Con varias, aparece el GIL."""
    N = 4
    print(f'{N} tareas CPU-bound simultáneas:\n')

    t0 = time.perf_counter()
    await asyncio.gather(*(asyncio.to_thread(hashear) for _ in range(N)))
    con_threads = time.perf_counter() - t0
    print(f'  asyncio.to_thread (threads)      {con_threads:5.2f}s')

    with ProcessPoolExecutor(max_workers=N) as pool:
        loop = asyncio.get_running_loop()
        t0 = time.perf_counter()
        await asyncio.gather(*(loop.run_in_executor(pool, hashear)
                               for _ in range(N)))
        con_procesos = time.perf_counter() - t0
    print(f'  ProcessPoolExecutor (procesos)   {con_procesos:5.2f}s')

    print(f'\n  Diferencia: {con_threads / con_procesos:.1f}x')
    print('  Es el GIL (clase 10): los threads se turnan para ejecutar bytecode,')
    print('  los procesos tienen su propio intérprete y corren de verdad en paralelo.')
    print('\n  Para CPU-bound: procesos. Para I/O bloqueante: threads.')


if __name__ == '__main__':
    asyncio.run(paralelo() if '--paralelo' in sys.argv else tres_formas())
