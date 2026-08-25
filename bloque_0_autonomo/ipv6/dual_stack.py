#!/usr/bin/env python3
"""Servidor dual-stack: un socket IPv6 que también atiende IPv4.

Demuestra IPV6_V6ONLY y las direcciones IPv4 mapeadas (::ffff:x.x.x.x).
Incluye un cliente agnóstico de familia usando getaddrinfo().

Uso:
    python3 dual_stack.py demo             # servidor + clientes de las dos familias
    python3 dual_stack.py servidor [puerto]
    python3 dual_stack.py servidor --v6only [puerto]
    python3 dual_stack.py cliente  [host] [puerto]
"""
import ipaddress
import socket
import sys
import threading
import time


def normalizar(host):
    """Convierte ::ffff:1.2.3.4 en 1.2.3.4. El resto queda igual.

    Hace falta porque el mismo cliente IPv4 se ve distinto según el socket
    sea dual-stack o no, y eso rompe logs, filtros y listas de bloqueo.
    """
    try:
        a = ipaddress.ip_address(host)
    except ValueError:
        return host
    if a.version == 6 and a.ipv4_mapped:
        return str(a.ipv4_mapped)
    return host


def crear_servidor(puerto, v6only=False):
    """Socket IPv6 en '::'. Con v6only=False atiende también IPv4."""
    s = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # SIEMPRE explícito: el default varía entre sistemas operativos
    # (Linux suele traer 0; OpenBSD y Windows, 1).
    s.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 1 if v6only else 0)
    s.bind(("::", puerto))
    s.listen(16)
    return s


def servidor(puerto, v6only=False, hasta=None, salida=None):
    s = crear_servidor(puerto, v6only)
    modo = "solo IPv6" if v6only else "dual-stack (IPv6 + IPv4)"
    print(f"Escuchando en [::]:{puerto} — {modo}")
    atendidos = 0
    try:
        while hasta is None or atendidos < hasta:
            conn, peer = s.accept()
            crudo, limpio = peer[0], normalizar(peer[0])
            marca = "  <- IPv4 mapeada" if crudo != limpio else ""
            print(f"  conexión de {crudo:<24} normalizado: {limpio}{marca}")
            if salida is not None:
                salida.append((crudo, limpio))
            with conn:
                conn.sendall(b"hola desde el servidor dual-stack\n")
            atendidos += 1
    except KeyboardInterrupt:
        print("\nCortado")
    finally:
        s.close()


def cliente(host, puerto, timeout=3):
    """Conecta probando todas las direcciones que devuelve getaddrinfo().

    Tener una dirección IPv6 no garantiza que la ruta funcione: por eso
    se prueba en orden y se sigue con la siguiente si falla.
    """
    ultimo = None
    for familia, tipo, proto, _, direccion in socket.getaddrinfo(
            host, puerto, type=socket.SOCK_STREAM):
        etiqueta = "IPv6" if familia == socket.AF_INET6 else "IPv4"
        s = socket.socket(familia, tipo, proto)
        try:
            s.settimeout(timeout)
            s.connect(direccion)
            print(f"  {etiqueta} -> conectado a {direccion[0]}")
            print(f"     respuesta: {s.recv(1024)!r}")
            s.close()
            return True
        except OSError as e:
            print(f"  {etiqueta} -> falló ({e.strerror}), sigo con la próxima")
            ultimo = e
        finally:
            s.close()
    print(f"  Ninguna dirección funcionó: {ultimo}")
    return False


def demo():
    """Levanta el servidor y le pega desde las dos familias."""
    puerto = 8316
    vistos = []
    hilo = threading.Thread(target=servidor,
                            args=(puerto, False, 2, vistos), daemon=True)
    hilo.start()
    time.sleep(0.4)

    print("\nCliente IPv6 (::1):")
    c6 = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
    c6.settimeout(3); c6.connect(("::1", puerto)); c6.recv(100); c6.close()

    print("Cliente IPv4 (127.0.0.1):")
    c4 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    c4.settimeout(3); c4.connect(("127.0.0.1", puerto)); c4.recv(100); c4.close()

    hilo.join(timeout=3)
    print(f"\nUn solo socket atendió {len(vistos)} conexiones de familias distintas.")
    print("Con IPV6_V6ONLY=1, la conexión IPv4 habría sido rechazada.")


if __name__ == "__main__":
    modo = sys.argv[1] if len(sys.argv) > 1 else "demo"
    args = [a for a in sys.argv[2:] if not a.startswith("--")]
    if modo == "servidor":
        servidor(int(args[0]) if args else 8080, v6only="--v6only" in sys.argv)
    elif modo == "cliente":
        host = args[0] if args else "localhost"
        cliente(host, int(args[1]) if len(args) > 1 else 8080)
    else:
        demo()
