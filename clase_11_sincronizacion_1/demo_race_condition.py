#!/usr/bin/env python3
"""
demo_race_condition.py — Demostración interactiva de una race condition

Este script demuestra cómo, sin sincronización, varios threads que modifican
la misma variable pueden producir resultados distintos cada vez que se ejecuta.

El ejemplo es un contador compartido. Cada thread lo incrementa N veces.
SIN sincronización, parte de los incrementos se pierden.

Uso:
    python3 demo_race_condition.py                    # 5 ejecuciones por defecto
    python3 demo_race_condition.py --runs 20          # 20 ejecuciones
    python3 demo_race_condition.py --safe             # con Lock: siempre da el resultado correcto
    python3 demo_race_condition.py --runs 10 --safe   # compará: 10 ejecuciones con Lock

Conceptos:
    - Race condition: dos o más threads acceden a una variable compartida sin sincronización
    - El operador += NO es atómico: se descompone en leer, sumar y escribir
    - El scheduler del SO puede intercalar esas operaciones de forma impredecible
    - Resultado: parte de los incrementos se "pierden"
"""

import argparse
import threading
import time


# Variable global compartida entre threads
contador = 0
lock = threading.Lock()


def incrementar_inseguro(iteraciones):
    """
    Incrementa `contador` `iteraciones` veces, descomponiendo el += en
    lectura/modificación/escritura para que la race condition sea visible.

    En CPython moderno (con GIL), `contador += 1` puede ejecutarse muy
    rápido y casi atómicamente para enteros. Para ver la race en vivo,
    forzamos un context switch entre lectura y escritura usando time.sleep(0)
    que cede el GIL al scheduler.

    Esto SIMULA fielmente lo que sucede a nivel bytecode:
      1. LOAD_GLOBAL contador        -> tmp = contador (leer)
      2. BINARY_ADD                  -> tmp = tmp + 1 (sumar)
      3. (posible context switch aquí)
      4. STORE_GLOBAL contador       -> contador = tmp (escribir)
    """
    global contador
    for _ in range(iteraciones):
        tmp = contador      # leer
        tmp = tmp + 1       # sumar
        time.sleep(0)       # CEDE EL GIL al scheduler -> abre ventana
        contador = tmp      # escribir


def incrementar_seguro(iteraciones):
    """
    Igual al anterior, PERO con Lock. Garantiza que solo un thread
    ejecute la sección crítica a la vez.
    """
    global contador
    for _ in range(iteraciones):
        with lock:
            tmp = contador
            tmp = tmp + 1
            time.sleep(0)
            contador = tmp


def ejecutar_una_vez(usar_lock=False, num_threads=10, iteraciones=100_000):
    """
    Lanza `num_threads` threads. Cada uno incrementa `contador` `iteraciones` veces.
    Devuelve el valor final del contador.

    Esperado teórico:
        contador_final == num_threads * iteraciones

    Con race condition: el contador final puede ser MENOR al esperado
    (porque algunos incrementos se pisan).
    """
    global contador
    contador = 0

    target = incrementar_seguro if usar_lock else incrementar_inseguro

    hilos = [
        threading.Thread(target=target, args=(iteraciones,))
        for _ in range(num_threads)
    ]

    for h in hilos:
        h.start()
    for h in hilos:
        h.join()

    return contador


def main():
    parser = argparse.ArgumentParser(
        description="Demostración de race condition en Python",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        "--runs", type=int, default=5,
        help="Cantidad de ejecuciones (default: 5). Probá con 20 para ver la variabilidad."
    )
    parser.add_argument(
        "--threads", type=int, default=10,
        help="Cantidad de threads en cada ejecución (default: 10)"
    )
    parser.add_argument(
        "--iter", type=int, default=10_000, dest="iteraciones",
        help="Iteraciones por thread (default: 10_000). Cuanto más alto, mayor la race."
    )
    parser.add_argument(
        "--safe", action="store_true",
        help="Ejecuta la versión SEGURA con Lock (siempre da el resultado correcto)"
    )
    args = parser.parse_args()

    esperado = args.threads * args.iteraciones

    modo = "CON Lock (segura)" if args.safe else "SIN Lock (race condition)"
    print(f"=" * 60)
    print(f"Modo: {modo}")
    print(f"Threads: {args.threads}")
    print(f"Iteraciones por thread: {args.iteraciones:,}")
    print(f"Contador esperado: {esperado:,}")
    print(f"=" * 60)
    print()

    resultados = []
    for i in range(args.runs):
        final = ejecutar_una_vez(
            usar_lock=args.safe,
            num_threads=args.threads,
            iteraciones=args.iteraciones,
        )
        diff = esperado - final
        if diff == 0:
            marca = "OK"
        else:
            porcentaje_perdido = (diff / esperado) * 100
            marca = f"PERDIDOS {diff:,} ({porcentaje_perdido:.1f}%)"
        print(f"Run {i+1:3d}: contador = {final:>10,}   [{marca}]")
        resultados.append(final)

    print()
    print(f"=" * 60)
    print(f"Resumen de {args.runs} ejecuciones:")
    print(f"  Resultados únicos: {len(set(resultados))}")
    print(f"  Mínimo:   {min(resultados):>10,}")
    print(f"  Máximo:   {max(resultados):>10,}")
    print(f"  Promedio: {sum(resultados)/len(resultados):>10,.1f}")
    print(f"  Esperado: {esperado:>10,}")

    if not args.safe:
        if len(set(resultados)) > 1:
            print()
            print(f"  Los resultados son DISTINTOS en cada ejecución.")
            print(f"  Esa variabilidad es la race condition en acción.")
            print(f"  Sin sincronización, el orden de ejecución del scheduler")
            print(f"  determina cuántos incrementos se pierden.")
        else:
            print()
            print(f"  Los resultados fueron idénticos en estas {args.runs} ejecuciones.")
            print(f"  Probá con --iter 1000000 para amplificar la race condition.")
    else:
        if len(set(resultados)) == 1 and resultados[0] == esperado:
            print()
            print(f"  Todos los resultados son idénticos e iguales al esperado.")
            print(f"  El Lock garantiza correctitud y determinismo.")

    print(f"=" * 60)


if __name__ == "__main__":
    main()
