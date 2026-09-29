#!/usr/bin/env python3
"""Clientes concurrentes: gather, semáforo, timeout y cancelación.

Simula descargas con asyncio.sleep para no depender de la red. La
versión con httpx real está comentada al final.

Uso:
    python3 descargas.py
"""
import asyncio
import random
import time

TAREAS = 12
LIMITE = 4


async def bajar(nombre, demora):
    """Simula una descarga. En la vida real sería un await cliente.get(url)."""
    await asyncio.sleep(demora)
    return f'{nombre} ({demora:.1f}s)'


async def secuencial(trabajos):
    return [await bajar(n, d) for n, d in trabajos]


async def concurrente(trabajos):
    return await asyncio.gather(*(bajar(n, d) for n, d in trabajos))


async def con_limite(trabajos, limite):
    """Semáforo: como mucho `limite` corriendo a la vez (clase 11)."""
    sem = asyncio.Semaphore(limite)

    async def acotada(nombre, demora):
        async with sem:                       # async with, no with
            return await bajar(nombre, demora)

    return await asyncio.gather(*(acotada(n, d) for n, d in trabajos))


async def con_timeout(trabajos, limite_seg):
    """Lo que tarda de más se cancela, no se espera."""
    async def intentar(nombre, demora):
        try:
            async with asyncio.timeout(limite_seg):
                return await bajar(nombre, demora)
        except TimeoutError:
            return f'{nombre} TIMEOUT'        # el timeout CANCELA la tarea
    return await asyncio.gather(*(intentar(n, d) for n, d in trabajos))


async def demostrar_cancelacion():
    """cancel() inyecta CancelledError en el próximo await."""
    print('\n=== Cancelación ===')

    async def larga():
        try:
            await asyncio.sleep(10)
        except asyncio.CancelledError:
            print('  la tarea recibió CancelledError en su await')
            raise                             # SIEMPRE relanzarla
        finally:
            print('  finally: limpieza hecha')

    tarea = asyncio.create_task(larga())
    await asyncio.sleep(0.2)
    tarea.cancel()
    try:
        await tarea
    except asyncio.CancelledError:
        print('  quien la canceló también la ve')


async def main():
    random.seed(7)
    trabajos = [(f't{i}', random.uniform(0.2, 1.2)) for i in range(TAREAS)]
    total = sum(d for _, d in trabajos)
    mas_lenta = max(d for _, d in trabajos)

    print(f'{TAREAS} descargas simuladas. Suma de demoras: {total:.1f}s, '
          f'la más lenta: {mas_lenta:.1f}s\n')

    for etiqueta, corrutina in [
        ('secuencial            ', secuencial(trabajos)),
        ('gather (todas juntas) ', concurrente(trabajos)),
        (f'con semáforo de {LIMITE}     ', con_limite(trabajos, LIMITE)),
        ('con timeout de 0.8s   ', con_timeout(trabajos, 0.8)),
    ]:
        t0 = time.perf_counter()
        resultados = await corrutina
        dt = time.perf_counter() - t0
        fallidas = sum(1 for r in resultados if 'TIMEOUT' in r)
        extra = f'  ({fallidas} canceladas por timeout)' if fallidas else ''
        print(f'  {etiqueta} {dt:5.2f}s{extra}')

    print(f'\n  secuencial   = la suma de todas las demoras')
    print(f'  gather       = lo que tarda la más lenta')
    print(f'  con semáforo = intermedio: acota cuántas corren a la vez,')
    print(f'                 para no agotar descriptores ni saturar la red')

    await demostrar_cancelacion()


# Con HTTP real sería así:
#
#     import httpx
#     async def bajar(cliente, url):
#         r = await cliente.get(url)              # await: no bloquea
#         return url, r.status_code, len(r.content)
#
#     async def main():
#         async with httpx.AsyncClient(timeout=10) as cliente:
#             # el cliente se crea UNA vez: reutiliza conexiones (keep-alive)
#             await asyncio.gather(*(bajar(cliente, u) for u in urls))
#
# requests NO sirve acá: es sincrónico y bloquea el event loop (clase 19).

if __name__ == '__main__':
    asyncio.run(main())
