#!/usr/bin/env python3
"""Cuántos clientes simultáneos aguanta un servidor asyncio.

La clase 14 midió threads, procesos y pools, y todos tenían un techo.
Acá el mismo experimento con corrutinas: el contraste es el argumento
de la clase.

Uso:
    python3 escala.py              # 100, 500, 1000
    python3 escala.py 2000 5000    # a medida
"""
import asyncio
import sys
import threading
import time

PUERTO = 8090


async def manejar(reader, writer):
    datos = await reader.readline()
    writer.write(datos)
    await writer.drain()
    writer.close()
    await writer.wait_closed()


async def un_cliente(i):
    try:
        reader, writer = await asyncio.open_connection('127.0.0.1', PUERTO)
        writer.write(f'cliente-{i}\n'.encode())
        await writer.drain()
        respuesta = await reader.readline()
        writer.close()
        await writer.wait_closed()
        return respuesta == f'cliente-{i}\n'.encode()
    except OSError:
        return False


async def probar(cantidad):
    t0 = time.perf_counter()
    resultados = await asyncio.gather(*(un_cliente(i) for i in range(cantidad)))
    tiempo = time.perf_counter() - t0
    return sum(resultados), tiempo


async def main(cantidades):
    servidor = await asyncio.start_server(
        manejar, '127.0.0.1', PUERTO, backlog=2048)

    print(f'{"clientes":>10} {"ok":>8} {"tiempo":>9} {"threads":>9}')
    print('-' * 40)

    async with servidor:
        for n in cantidades:
            ok, tiempo = await probar(n)
            print(f'{n:>10} {ok:>8} {tiempo:>8.2f}s {threading.active_count():>9}')
            await asyncio.sleep(0.3)         # dar tiempo a cerrar sockets

    print('\n  Un solo hilo atendiendo todos.')
    print('  En la clase 14, cada cliente era un thread: 4 MB de stack cada uno')
    print('  más el costo de que el kernel reparta tiempo entre todos.')
    print('  Acá cada cliente es una Task: unos cientos de bytes.')
    print('\n  Eso es la respuesta al problema C10K.')


if __name__ == '__main__':
    cantidades = [int(a) for a in sys.argv[1:]] or [100, 500, 1000]
    asyncio.run(main(cantidades))
