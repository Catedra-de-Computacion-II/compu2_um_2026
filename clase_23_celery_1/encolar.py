"""
Clase 23: encolar trabajo y morirse sin esperarlo.

Esta es la mitad interesante de la demostracion. El programa encola una
tarea, guarda el id en un archivo, y termina. No espera nada.

La tarea queda en el broker. Se puede ejecutar despues, con un worker que
todavia no existe, y el resultado se consulta desde otro programa
(consultar.py) usando ese id.

Uso:
    python3 encolar.py            # una tarea
    python3 encolar.py --varias   # varias, para ver el reparto
    python3 encolar.py --falla    # una que revienta

El broker tiene que estar arriba (docker compose up -d). El worker NO hace
falta todavia: esa es justamente la idea.
"""
import sys

from tareas import sumar, lenta, dividir

ARCHIVO_IDS = 'ultimos_ids.txt'


def guardar(ids):
    """Deja los ids en un archivo para que consultar.py los encuentre."""
    with open(ARCHIVO_IDS, 'w') as f:
        f.write('\n'.join(ids))
    print(f"\n  ids guardados en {ARCHIVO_IDS}")


def una():
    print("=" * 62)
    print("Encolar una tarea y morirse")
    print("=" * 62)

    resultado = sumar.delay(2, 3)

    print(f"  id:     {resultado.id}")
    print(f"  estado: {resultado.state}")
    print()
    print("  Fijate que delay() volvio enseguida: no espero el resultado.")
    print("  La tarea esta en el broker, no en este proceso.")
    print("  Cuando este programa termine, la tarea sigue ahi.")

    guardar([resultado.id])


def varias():
    print("=" * 62)
    print("Encolar varias para ver el reparto")
    print("=" * 62)

    # Cuatro tareas de 2 segundos. Con --concurrency=2 van a salir en
    # dos rondas: mirá los timestamps en el log del worker.
    resultados = [lenta.delay(2) for _ in range(4)]

    for i, r in enumerate(resultados, 1):
        print(f"  tarea {i}: {r.id}")

    print()
    print("  4 tareas de 2s. Con --concurrency=2 deberian tardar ~4s en")
    print("  total, no 8s. Mirá los timestamps del log del worker.")

    guardar([r.id for r in resultados])


def falla():
    print("=" * 62)
    print("Encolar una tarea que va a fallar")
    print("=" * 62)

    resultado = dividir.delay(1, 0)

    print(f"  id: {resultado.id}")
    print()
    print("  Esta va a reventar con ZeroDivisionError en el worker.")
    print("  A diferencia de un Future abandonado (clase 22), la excepcion")
    print("  NO se pierde: queda guardada en el backend con su traceback.")
    print("  Consultala con consultar.py.")

    guardar([resultado.id])


if __name__ == '__main__':
    if '--varias' in sys.argv:
        varias()
    elif '--falla' in sys.argv:
        falla()
    else:
        una()

    print("\n  Ahora: python3 consultar.py")
