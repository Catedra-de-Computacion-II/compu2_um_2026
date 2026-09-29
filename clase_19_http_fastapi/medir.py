#!/usr/bin/env python3
"""Tres formas de escribir un endpoint lento, y cuál arruina el servidor.

Levanta una API con tres endpoints que tardan lo mismo pero están
escritos distinto, y les manda pedidos concurrentes para medir.

El resultado es contraintuitivo: un def común anda mejor que un
async def mal escrito.

Uso:
    pip install fastapi uvicorn httpx
    python3 medir.py
"""
import asyncio
import multiprocessing
import time

from fastapi import FastAPI

PUERTO = 8001
PEDIDOS = 3
DEMORA = 1.0

app = FastAPI()


@app.get('/async-bien')
async def async_bien():
    """Corrutina que CEDE el control: el loop atiende a otros mientras."""
    await asyncio.sleep(DEMORA)
    return {'ok': True}


@app.get('/async-mal')
async def async_mal():
    """Corrutina que NO cede: bloquea el event loop y con él a todos."""
    time.sleep(DEMORA)                    # el bug de la clase 18
    return {'ok': True}


@app.get('/sync')
def sincronico():
    """def común: FastAPI lo manda a un threadpool, fuera del loop."""
    time.sleep(DEMORA)
    return {'ok': True}


def levantar():
    import uvicorn
    uvicorn.run(app, host='127.0.0.1', port=PUERTO, log_level='error')


async def medir(ruta):
    import httpx
    async with httpx.AsyncClient(timeout=30) as cliente:
        t0 = time.perf_counter()
        await asyncio.gather(*(
            cliente.get(f'http://127.0.0.1:{PUERTO}/{ruta}')
            for _ in range(PEDIDOS)
        ))
        return time.perf_counter() - t0


async def correr_mediciones():
    print(f'{PEDIDOS} pedidos concurrentes a endpoints que tardan {DEMORA}s:\n')
    resultados = {}
    for ruta in ('async-bien', 'async-mal', 'sync'):
        resultados[ruta] = await medir(ruta)
        print(f'  /{ruta:<12} {resultados[ruta]:5.2f}s')

    print(f'\n  /async-bien  se solapan: el await cede el control.')
    print(f'  /async-mal   NO se solapan: time.sleep bloquea el event loop,')
    print(f'               y como es uno solo, congela todos los pedidos.')
    print(f'  /sync        se solapan igual que el primero: FastAPI detecta')
    print(f'               que no es corrutina y lo manda a un threadpool.')
    print(f'\n  Conclusión: un def común es MEJOR que un async def mal escrito.')
    print(f'  Si tu función bloquea y no hay alternativa async, usá def.')


def main():
    servidor = multiprocessing.Process(target=levantar, daemon=True)
    servidor.start()
    time.sleep(3)                          # esperar a que levante
    try:
        asyncio.run(correr_mediciones())
    finally:
        servidor.terminate()
        servidor.join(timeout=5)


if __name__ == '__main__':
    main()
