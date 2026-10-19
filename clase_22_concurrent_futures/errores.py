#!/usr/bin/env python3
"""Las excepciones en executors: dónde quedan y cómo se pierden.

Una excepción en un worker no sube por tu pila: queda guardada en el
Future. Si nunca pedís el resultado, desaparece sin dejar rastro.

Es el bug más común del módulo y el más difícil de diagnosticar,
porque no hay ningún síntoma.

Uso:
    python3 errores.py
"""
import logging
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# A stdout, no a stderr: así el aviso sale junto a su sección y no
# mezclado al principio cuando se redirige la salida.
logging.basicConfig(level=logging.INFO, format='  [log] %(message)s',
                    stream=sys.stdout)


def dividir(a, b):
    time.sleep(0.1)
    return a / b                      # ZeroDivisionError si b == 0


def el_bug():
    print('=' * 62)
    print('1. La excepción que nadie ve')
    print('=' * 62)
    with ThreadPoolExecutor(2) as pool:
        pool.submit(dividir, 10, 0)   # falla, pero no guardamos el future
    print('  ...')
    print('\n  Arriba de esta línea no se imprimió NADA.')
    print('  La tarea falló con ZeroDivisionError, el error quedó en un')
    print('  Future que nadie miró, y el objeto se destruyó.')
    print('\n  En un servidor, esto son tareas que fallan en silencio.')


def donde_queda():
    print('\n' + '=' * 62)
    print('2. Dónde está la excepción mientras tanto')
    print('=' * 62)
    with ThreadPoolExecutor(1) as pool:
        f = pool.submit(dividir, 10, 0)
        print(f'  recién hecho el submit:  done={f.done()}')
        time.sleep(0.3)
        print(f'  ya terminó:              done={f.done()}')
        print(f'  exception() la devuelve: {f.exception()!r}')
        print('  <- fijate que exception() NO la lanza, la devuelve')
        try:
            f.result()
        except ZeroDivisionError as e:
            print(f'  result() SÍ la lanza:    {type(e).__name__}: {e}')


def defensa_consumir():
    print('\n' + '=' * 62)
    print('3. Defensa A: consumir siempre los resultados')
    print('=' * 62)
    datos = [(10, 2), (10, 0), (10, 5), (1, 0)]
    with ThreadPoolExecutor(4) as pool:
        futuros = {pool.submit(dividir, a, b): (a, b) for a, b in datos}
        ok, fallaron = [], []
        for f in as_completed(futuros):
            entrada = futuros[f]
            try:
                ok.append((entrada, f.result()))
            except Exception as e:
                fallaron.append((entrada, repr(e)))
    print(f'  completadas: {len(ok)}   fallidas: {len(fallaron)}')
    for entrada, err in fallaron:
        print(f'    {entrada} -> {err}')


def defensa_callback():
    print('\n' + '=' * 62)
    print('4. Defensa B: un callback que vigile')
    print('=' * 62)

    def vigilar(futuro):
        if not futuro.cancelled() and futuro.exception():
            logging.error('una tarea falló: %r', futuro.exception())

    with ThreadPoolExecutor(2) as pool:
        f = pool.submit(dividir, 1, 0)
        f.add_done_callback(vigilar)   # se llama solo al terminar
    print('  El callback avisó sin que tuviéramos que pedir el resultado.')


def map_corta():
    print('\n' + '=' * 62)
    print('5. Con map(), una excepción CORTA la iteración')
    print('=' * 62)
    datos = [(10, 2), (10, 0), (10, 5), (10, 4)]
    with ThreadPoolExecutor(4) as pool:
        resultados = pool.map(dividir, *zip(*datos))
        print('  map() no lanzó nada todavía')
        vistos = []
        try:
            for r in resultados:
                vistos.append(r)
                print(f'  recibí {r}')
        except ZeroDivisionError:
            print('  ZeroDivisionError al llegar al segundo')
    print(f'\n  Vi {len(vistos)} de {len(datos)} resultados.')
    print('  Los dos últimos estaban calculados pero se perdieron:')
    print('  map() entrega en orden, y al cortar no sigue.')
    print('\n  Si querés procesar todo y revisar los errores después,')
    print('  usá as_completed con try/except adentro (defensa A).')


if __name__ == '__main__':
    el_bug()
    donde_queda()
    defensa_consumir()
    defensa_callback()
    map_corta()
