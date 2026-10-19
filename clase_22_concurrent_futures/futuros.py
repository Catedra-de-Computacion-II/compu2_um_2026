#!/usr/bin/env python3
"""El ciclo de vida de un Future, visto desde afuera.

submit() vuelve enseguida con un recibo. Acá se ve cómo ese recibo
cambia de estado y cuándo cada método bloquea.

Uso:
    python3 futuros.py
"""
import time
from concurrent.futures import ThreadPoolExecutor


def trabajo(segundos, etiqueta):
    time.sleep(segundos)
    return f'{etiqueta} listo'


def estado(f):
    """Los tres predicados que NO bloquean."""
    if f.cancelled():
        return 'CANCELLED'
    if f.done():
        return 'FINISHED'
    if f.running():
        return 'RUNNING'
    return 'PENDING'


def ciclo_de_vida():
    print('=' * 62)
    print('1. El ciclo de vida de un Future')
    print('=' * 62)

    # Un solo worker: la segunda tarea queda en cola y se ve el PENDING
    with ThreadPoolExecutor(max_workers=1) as pool:
        t0 = time.perf_counter()
        primera = pool.submit(trabajo, 0.4, 'primera')
        segunda = pool.submit(trabajo, 0.1, 'segunda')

        print(f'  submit() volvió en {(time.perf_counter() - t0) * 1000:.2f} ms '
              f'— no esperó nada\n')

        for momento in (0.05, 0.25, 0.6):
            time.sleep(momento - (time.perf_counter() - t0))
            print(f'  t={momento:.2f}s   primera: {estado(primera):<9} '
                  f'segunda: {estado(segunda)}')

        print(f'\n  result() de la primera: {primera.result()!r}')


def bloquea_o_no():
    print('\n' + '=' * 62)
    print('2. Qué bloquea y qué no')
    print('=' * 62)

    with ThreadPoolExecutor(1) as pool:
        f = pool.submit(trabajo, 0.5, 'tarea')

        t0 = time.perf_counter()
        f.done()
        print(f'  done()    tardó {(time.perf_counter() - t0) * 1000:7.3f} ms  '
              f'-> consulta instantánea')

        t0 = time.perf_counter()
        f.result()
        print(f'  result()  tardó {(time.perf_counter() - t0) * 1000:7.1f} ms  '
              f'-> esperó a que terminara')


def cancelar():
    print('\n' + '=' * 62)
    print('3. cancel() solo funciona si la tarea no arrancó')
    print('=' * 62)

    with ThreadPoolExecutor(max_workers=1) as pool:
        corriendo = pool.submit(trabajo, 0.5, 'en curso')
        en_cola = pool.submit(trabajo, 0.1, 'esperando')
        time.sleep(0.1)                       # dar tiempo a que arranque la 1a

        print(f'  la que ya arrancó  -> cancel(): {corriendo.cancel()}')
        print(f'  la que está en cola -> cancel(): {en_cola.cancel()}')
        print(f'\n  estados: en curso={estado(corriendo)}  '
              f'en cola={estado(en_cola)}')
        print('\n  No se puede interrumpir un thread en ejecución: cancel()')
        print('  solo saca de la cola lo que todavía no empezó.')
        print('  (En asyncio sí se puede: inyecta la excepción en el próximo await.)')


def con_timeout():
    print('\n' + '=' * 62)
    print('4. result() con timeout')
    print('=' * 62)

    with ThreadPoolExecutor(1) as pool:
        f = pool.submit(trabajo, 1.0, 'lenta')
        try:
            f.result(timeout=0.3)
        except TimeoutError:
            print('  TimeoutError tras 0.3s de espera')
            print(f'  ¿la tarea se canceló? estado: {estado(f)}')
            print('  <- NO: sigue corriendo. El timeout es de la ESPERA,')
            print('     no de la tarea.')
        print(f'  y efectivamente termina: {f.result()!r}')


if __name__ == '__main__':
    ciclo_de_vida()
    bloquea_o_no()
    cancelar()
    con_timeout()
