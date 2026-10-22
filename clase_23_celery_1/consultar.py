"""
Clase 23: consultar el resultado desde un proceso que no encolo nada.

Este programa no conoce a encolar.py, no comparte memoria con el, y puede
correr minutos despues de que ese proceso haya muerto. Lo unico que tiene
es un id.

Eso es lo que un Future de la clase 22 no puede hacer: un Future es un
objeto en la memoria de un proceso, y muere con el. Un AsyncResult es una
vista sobre algo guardado en el backend.

Uso:
    python3 consultar.py                  # lee ultimos_ids.txt
    python3 consultar.py <id>             # un id puntual
    python3 consultar.py --esperar        # bloquea con get()
    python3 consultar.py --inventado      # la trampa de PENDING
"""
import sys

from celery.result import AsyncResult

from tareas import app

ARCHIVO_IDS = 'ultimos_ids.txt'


def leer_ids():
    try:
        with open(ARCHIVO_IDS) as f:
            return [linea.strip() for linea in f if linea.strip()]
    except FileNotFoundError:
        print(f"  No existe {ARCHIVO_IDS}. Corré primero: python3 encolar.py")
        sys.exit(1)


def mostrar(tid):
    """Todo lo que se puede saber de una tarea teniendo solo su id."""
    r = AsyncResult(tid, app=app)

    print(f"  id:           {tid}")
    print(f"  state:        {r.state}")
    print(f"  ready():      {r.ready()}")

    if r.state == 'SUCCESS':
        print(f"  successful(): {r.successful()}")
        print(f"  result:       {r.result!r}")
    elif r.state == 'FAILURE':
        print(f"  failed():     {r.failed()}")
        print(f"  result:       {r.result!r}   <- la excepcion, como objeto")
        if r.traceback:
            ultima = r.traceback.strip().splitlines()[-1]
            print(f"  traceback:    ...{ultima}")
            print("                (el traceback viajo desde el worker)")
    else:
        print("  todavia no termino (o el worker no esta corriendo)")

    print()


def consultar_todos():
    print("=" * 62)
    print("Consultar por id, desde un proceso que no encolo nada")
    print("=" * 62)
    print()

    for tid in leer_ids():
        mostrar(tid)


def esperar():
    """get() bloquea hasta que haya resultado, como result() del Future."""
    print("=" * 62)
    print("Esperar con get()")
    print("=" * 62)
    print()

    for tid in leer_ids():
        r = AsyncResult(tid, app=app)
        print(f"  {tid}")
        try:
            # get() relanza la excepcion si la tarea fallo, igual que
            # Future.result() en la clase 22.
            valor = r.get(timeout=30)
            print(f"    -> {valor!r}")
        except Exception as e:
            print(f"    -> get() relanzo: {type(e).__name__}: {e}")
        print()


def inventado():
    """La trampa: PENDING no significa 'en cola'."""
    print("=" * 62)
    print("La trampa de PENDING")
    print("=" * 62)
    print()

    r = AsyncResult('id-que-no-existe-jamas', app=app)
    print(f"  id inventado -> state: {r.state!r}")
    print(f"                  ready(): {r.ready()}")
    print(f"                  result: {r.result!r}")
    print()
    print("  PENDING no quiere decir 'esta en la cola'.")
    print("  Quiere decir 'el backend no sabe nada de este id'.")
    print("  Una tarea encolada y un id inexistente son indistinguibles:")
    print("  el backend recien guarda algo cuando la tarea termina.")
    print()
    print("  Si necesitas distinguirlos, el id lo tenes que guardar vos")
    print("  en el momento de encolar.")
    print()


if __name__ == '__main__':
    if '--esperar' in sys.argv:
        esperar()
    elif '--inventado' in sys.argv:
        inventado()
    elif len(sys.argv) > 1 and not sys.argv[1].startswith('--'):
        print()
        mostrar(sys.argv[1])
    else:
        consultar_todos()
