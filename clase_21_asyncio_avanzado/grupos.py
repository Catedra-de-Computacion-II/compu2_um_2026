#!/usr/bin/env python3
"""gather contra TaskGroup: qué pasa cuando una tarea falla.

La diferencia no es de sintaxis sino de qué queda corriendo después del
error. Con gather, las hermanas siguen huérfanas; con TaskGroup, se
cancelan.

Uso:
    python3 grupos.py
"""
import asyncio

vivas = set()           # para ver qué quedó corriendo después del fallo


async def larga(nombre, segundos=3):
    """Una tarea que tarda. Registra si llegó a terminar."""
    vivas.add(nombre)
    try:
        await asyncio.sleep(segundos)
        return f'{nombre} terminó'
    except asyncio.CancelledError:
        print(f'    {nombre}: me cancelaron')
        raise
    finally:
        vivas.discard(nombre)


async def falla_rapido():
    await asyncio.sleep(0.2)
    raise ValueError('algo salió mal')


async def con_gather():
    print('=== gather: la hermana queda huérfana ===')
    vivas.clear()
    try:
        await asyncio.gather(larga('A'), falla_rapido())
    except ValueError as e:
        print(f'  capturé: {e}')

    await asyncio.sleep(0.1)
    print(f'  tareas todavía corriendo: {vivas or "ninguna"}')
    if vivas:
        print('  <- A sigue viva, consumiendo recursos, sin nadie que la espere')
    await asyncio.sleep(3)          # dejar que termine para no ensuciar


async def con_taskgroup():
    print('\n=== TaskGroup: cancela a las hermanas ===')
    vivas.clear()
    try:
        async with asyncio.TaskGroup() as grupo:
            grupo.create_task(larga('B'))
            grupo.create_task(falla_rapido())
    except* ValueError as eg:
        print(f'  capturé un ExceptionGroup con {len(eg.exceptions)} excepción(es)')

    print(f'  tareas todavía corriendo: {vivas or "ninguna"}')
    print('  <- B fue cancelada automáticamente: no quedó nada suelto')


async def resultados():
    print('\n=== Obtener resultados de un TaskGroup ===')
    async with asyncio.TaskGroup() as grupo:
        t1 = grupo.create_task(larga('X', 0.1))
        t2 = grupo.create_task(larga('Y', 0.2))
    # Afuera del bloque las tareas ya terminaron: se puede leer .result()
    print(f'  {t1.result()}  |  {t2.result()}')
    print('  TaskGroup no devuelve los resultados: hay que guardar las tasks.')


async def varias_fallas():
    print('\n=== Varias fallas a la vez: por eso es un GRUPO ===')
    async def falla(tipo):
        await asyncio.sleep(0.1)
        raise tipo('falló')
    try:
        async with asyncio.TaskGroup() as grupo:
            grupo.create_task(falla(ValueError))
            grupo.create_task(falla(TypeError))
    except* ValueError:
        print('  rama ValueError: entró')
    except* TypeError:
        print('  rama TypeError: entró')
    print('  <- entraron LAS DOS: except* no es excluyente como un except común')


async def main():
    await con_gather()
    await con_taskgroup()
    await resultados()
    await varias_fallas()


if __name__ == '__main__':
    asyncio.run(main())
