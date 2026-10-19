#!/usr/bin/env python3
"""map contra as_completed: la misma concurrencia, distinta entrega.

Las tareas corren en paralelo en los dos casos. Lo que cambia es CUÁNDO
podés usar cada resultado.

Uso:
    python3 patrones.py
"""
import time
from concurrent.futures import ThreadPoolExecutor, as_completed, wait, FIRST_COMPLETED

TRABAJOS = [('lenta', 0.5), ('rapida', 0.1), ('media', 0.2), ('otra', 0.4)]


def tarea(nombre, demora):
    time.sleep(demora)
    return f'{nombre}'


def con_map():
    print('=' * 62)
    print('1. map(): resultados EN ORDEN DE ENTRADA')
    print('=' * 62)
    with ThreadPoolExecutor(4) as pool:
        t0 = time.perf_counter()
        for r in pool.map(tarea, *zip(*TRABAJOS)):
            print(f'  {r:<8} disponible a los {time.perf_counter() - t0:.2f}s')
    print('\n  Las cuatro llegaron juntas: "rapida" estaba lista a los 0.10s')
    print('  pero esperó a que "lenta" terminara para poder entregarse.')


def con_as_completed():
    print('\n' + '=' * 62)
    print('2. as_completed(): resultados A MEDIDA QUE TERMINAN')
    print('=' * 62)
    with ThreadPoolExecutor(4) as pool:
        t0 = time.perf_counter()
        futuros = [pool.submit(tarea, n, d) for n, d in TRABAJOS]
        for f in as_completed(futuros):
            print(f'  {f.result():<8} disponible a los {time.perf_counter() - t0:.2f}s')
    print('\n  Cada una apenas estuvo lista. El total es el mismo,')
    print('  pero podés empezar a trabajar con los resultados antes.')


def saber_de_cual():
    print('\n' + '=' * 62)
    print('3. as_completed pierde la correspondencia: el truco del dict')
    print('=' * 62)
    with ThreadPoolExecutor(4) as pool:
        # El future como CLAVE: así se recupera de qué entrada era
        futuros = {pool.submit(tarea, n, d): n for n, d in TRABAJOS}
        for f in as_completed(futuros):
            origen = futuros[f]
            print(f'  la tarea {origen!r} devolvió {f.result()!r}')
    print('\n  Patrón idiomático: {future: dato_original}')


def esperar_al_primero():
    print('\n' + '=' * 62)
    print('4. wait(): "el primero que conteste gana"')
    print('=' * 62)
    with ThreadPoolExecutor(4) as pool:
        futuros = [pool.submit(tarea, n, d) for n, d in TRABAJOS]
        t0 = time.perf_counter()
        listos, pendientes = wait(futuros, return_when=FIRST_COMPLETED)
        print(f'  a los {time.perf_counter() - t0:.2f}s: '
              f'{len(listos)} listo(s), {len(pendientes)} pendiente(s)')
        print(f'  el ganador: {list(listos)[0].result()!r}')
        for f in pendientes:
            f.cancel()
        print('  (cancelamos el resto; los que ya arrancaron igual terminan)')


if __name__ == '__main__':
    con_map()
    con_as_completed()
    saber_de_cual()
    esperar_al_primero()
