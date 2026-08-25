#!/usr/bin/env python3
"""Explorador de IPv6: qué tenés en tu máquina y qué te dice getaddrinfo().

No necesita conectividad IPv6 a Internet. Las partes que sí la necesitan
avisan cuando no hay ruta, que es el caso más común en Argentina.

Uso:
    python3 explorar_ipv6.py                 # todo
    python3 explorar_ipv6.py resolver google.com
"""
import ipaddress
import socket
import sys


def separador(titulo):
    print(f"\n{'=' * 68}\n{titulo}\n{'=' * 68}")


def compresion():
    """Las reglas de compresión, aplicadas por la stdlib."""
    separador("1. Compresión de direcciones")
    ejemplos = [
        "2001:0db8:85a3:0000:0000:8a2e:0370:7334",
        "0000:0000:0000:0000:0000:0000:0000:0001",
        "fe80:0000:0000:0000:e570:5b50:dafb:ec40",
        "2001:0db8:0000:0000:0001:0000:0000:0001",
    ]
    for e in ejemplos:
        a = ipaddress.ip_address(e)
        print(f"  {e}")
        print(f"    -> {a.compressed}")
    # El último tiene DOS secuencias de ceros: el :: va en la más larga,
    # y la otra queda como 0 explícito. No puede haber dos '::'.
    print("\n  Notá el último: dos secuencias de ceros, pero '::' aparece")
    print("  una sola vez (en la más larga). Dos '::' serían ambiguos.")


def clasificar():
    """Cada dirección tiene un alcance. Se clasifica de lo específico
    a lo general: multicast y loopback antes que global/privada, porque
    los flags de la stdlib se solapan (ff02::1 da is_global=True)."""
    separador("2. Tipos de dirección")
    ejemplos = [
        ("::1", "loopback: el 127.0.0.1 de IPv6"),
        ("::", "sin especificar / todas las interfaces"),
        ("fe80::1", "link-local: no sale del segmento físico"),
        ("2803:9800:9842:8187::1", "unicast global: ruteable en Internet"),
        ("2001:db8::1", "rango de documentación (RFC 3849)"),
        ("ff02::1", "multicast: todos los nodos del enlace"),
        ("::ffff:192.168.1.5", "IPv4 mapeada dentro de IPv6"),
    ]
    print(f"  {'dirección':<26} {'clasificación':<22} qué es")
    print(f"  {'-' * 26} {'-' * 22} {'-' * 38}")
    for texto, descripcion in ejemplos:
        a = ipaddress.ip_address(texto)
        if getattr(a, "ipv4_mapped", None):
            tipo = f"IPv4 mapeada"
        elif a.is_loopback:
            tipo = "loopback"
        elif a.is_multicast:
            tipo = "multicast"
        elif a.is_link_local:
            tipo = "link-local"
        elif a.is_unspecified:
            tipo = "sin especificar"
        elif a.is_global:
            tipo = "global"
        else:
            tipo = "reservada/privada"
        print(f"  {texto:<26} {tipo:<22} {descripcion}")
    print("\n  Ojo con los flags de ipaddress: se solapan. ff02::1 da")
    print("  is_global=True aunque sea multicast, y 2001:db8::/32 da")
    print("  is_private=True porque es el rango reservado a ejemplos.")
    print("  Por eso conviene preguntar de lo específico a lo general.")


def mis_direcciones():
    """Qué direcciones tiene esta máquina, según el propio Python."""
    separador("3. Direcciones de esta máquina")
    nombre = socket.gethostname()
    print(f"  hostname: {nombre}\n")
    globales, link_local, otras = [], [], []
    for familia in (socket.AF_INET, socket.AF_INET6):
        try:
            infos = socket.getaddrinfo(nombre, None, familia)
        except socket.gaierror:
            continue
        for _, _, _, _, direccion in infos:
            host = direccion[0]
            try:
                a = ipaddress.ip_address(host)
            except ValueError:
                continue
            destino = (link_local if a.is_link_local else
                       globales if a.is_global else otras)
            if host not in destino:
                destino.append(host)

    for etiqueta, lista in [("Globales (ruteables)", globales),
                            ("Otras (loopback, privadas)", otras)]:
        if lista:
            print(f"  {etiqueta}:")
            for h in lista:
                print(f"    {h}")

    # Las link-local se resumen: con Docker o VMs puede haber decenas,
    # una por interfaz virtual, y no aportan nada verlas todas.
    if link_local:
        print(f"\n  Link-local (fe80::): {len(link_local)}")
        for h in link_local[:3]:
            print(f"    {h}")
        if len(link_local) > 3:
            print(f"    ... y {len(link_local) - 3} más "
                  "(una por interfaz; Docker y las VMs suman varias)")

    if not (globales or link_local or otras):
        print("    (no resolvió el hostname; probá 'ip -6 addr show')")
    print("\n  Para verlas por interfaz:  ip -6 addr show")


def resolver(host):
    """getaddrinfo() devuelve las dos familias, ordenadas por preferencia."""
    separador(f"4. getaddrinfo('{host}', 80)")
    try:
        infos = socket.getaddrinfo(host, 80, type=socket.SOCK_STREAM)
    except socket.gaierror as e:
        print(f"  No se pudo resolver: {e}")
        print("  (¿hay conexión a Internet?)")
        return
    for familia, tipo, proto, canon, direccion in infos:
        # La tupla IPv6 tiene 4 elementos; la IPv4, 2. Por eso nunca
        # hay que hacer 'host, puerto = direccion'.
        print(f"  {familia.name:<10} tupla de {len(direccion)} elementos: {direccion}")
    print("\n  El orden importa: el sistema pone primero lo que prefiere,")
    print("  y un cliente correcto prueba en ese orden hasta que uno ande.")


def probar_loopback():
    """::1 funciona siempre, haya o no Internet IPv6."""
    separador("5. Conexión sobre ::1 (loopback IPv6)")
    servidor = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
    servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        servidor.bind(("::1", 0))          # puerto 0 = que elija el kernel
        servidor.listen(1)
        puerto = servidor.getsockname()[1]
        print(f"  servidor escuchando en [::1]:{puerto}")
        print(f"  getsockname() completo: {servidor.getsockname()}")
        print("    (4 elementos: dirección, puerto, flowinfo, scope_id)")

        cliente = socket.create_connection(("::1", puerto), timeout=3)
        conn, peer = servidor.accept()
        print(f"  cliente conectado desde: {peer[0]}")
        conn.close(); cliente.close()
        print("  IPv6 local: FUNCIONA")
    except OSError as e:
        print(f"  Falló: {e}")
    finally:
        servidor.close()


def probar_internet():
    """Esto sí necesita ruta IPv6 real. Puede fallar y está bien."""
    separador("6. ¿Hay ruta IPv6 a Internet?")
    s = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
    s.settimeout(3)
    try:
        s.connect(("2001:4860:4860::8888", 53))    # DNS de Google, IPv6
        print(f"  Hay ruta. Salgo por: {s.getsockname()[0]}")
    except OSError as e:
        print(f"  Sin ruta IPv6 a Internet ({e.strerror}).")
        print("  Es lo habitual en Argentina: tenés dirección pero no ruta.")
        print("  No afecta a esta clase: todo se prueba sobre ::1.")
    finally:
        s.close()


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "resolver":
        resolver(sys.argv[2])
    else:
        compresion()
        clasificar()
        mis_direcciones()
        resolver("google.com")
        probar_loopback()
        probar_internet()
        print()
