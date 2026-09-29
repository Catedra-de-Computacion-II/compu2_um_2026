#!/usr/bin/env python3
"""El servidor eco de la clase 13, en versión asíncrona.

Misma estructura que server_threads.py de la clase 14 —una función que
atiende a un cliente— pero cada conexión es una Task en vez de un thread.

Uso:
    python3 eco_async.py                  # servidor
    python3 eco_async.py cliente          # un cliente de prueba
    python3 eco_async.py --lento 2        # tarda 2s por mensaje

Probalo con:  nc localhost 8080
"""
import asyncio
import signal
import sys
import threading

PUERTO = 8080
conectados = 0          # sin Lock: ver el comentario en manejar()


async def manejar(reader, writer, demora=0.0):
    """Una corrutina por cliente. El equivalente de handle() en la clase 16."""
    global conectados
    # Sección crítica SIN await adentro: es atómica por construcción,
    # porque el cambio de contexto solo ocurre en un await.
    conectados += 1
    direccion = writer.get_extra_info('peername')
    print(f'+ {direccion}  (conectados: {conectados}, '
          f'threads: {threading.active_count()})')

    try:
        while True:
            datos = await reader.readline()      # framing por líneas, gratis
            if not datos:                        # b'' = el cliente cerró
                break
            if demora:
                await asyncio.sleep(demora)      # cede: otros siguen atendidos
            writer.write(b'ECO: ' + datos)
            await writer.drain()                 # control de flujo
    except asyncio.CancelledError:
        print(f'  {direccion} cancelada')
        raise                                    # SIEMPRE relanzarla
    except ConnectionResetError:
        pass                                     # el cliente cortó mal
    finally:
        conectados -= 1
        print(f'- {direccion}  (conectados: {conectados})')
        writer.close()
        await writer.wait_closed()               # esperar el cierre real


async def servidor(demora=0.0):
    async def handler(r, w):
        await manejar(r, w, demora)

    srv = await asyncio.start_server(handler, '0.0.0.0', PUERTO)
    direccion = srv.sockets[0].getsockname()
    print(f'Escuchando en {direccion} — un solo hilo, una Task por cliente')

    # Cierre ordenado: el loop maneja la señal entre tareas, en un momento
    # seguro. Es el self-pipe de la clase 6, hecho biblioteca.
    cerrar = asyncio.Event()
    loop = asyncio.get_running_loop()
    for s in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(s, cerrar.set)

    async with srv:
        await cerrar.wait()
        print('\nCerrando: no se aceptan conexiones nuevas')


async def cliente():
    reader, writer = await asyncio.open_connection('localhost', PUERTO)
    writer.write(b'hola mundo\n')
    await writer.drain()                         # write no lleva await; drain sí
    print('recibido:', await reader.readline())
    writer.close()
    await writer.wait_closed()


if __name__ == '__main__':
    if 'cliente' in sys.argv:
        asyncio.run(cliente())
    else:
        demora = 0.0
        if '--lento' in sys.argv:
            demora = float(sys.argv[sys.argv.index('--lento') + 1])
        try:
            asyncio.run(servidor(demora))
        except KeyboardInterrupt:
            pass
