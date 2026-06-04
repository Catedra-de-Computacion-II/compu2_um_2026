#!/usr/bin/env python3
"""
pipe_playground.py — Playground interactivo de Pipes en la shell
Clase 4 - Computación II 2026 - Universidad de Mendoza
"""

import os
import sys
import subprocess
import tempfile
from pathlib import Path

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
    from rich.prompt import Prompt
    from rich.rule import Rule
    from rich.columns import Columns
    from rich import box
except ImportError:
    print("Instalando rich (una sola vez)...")
    subprocess.run([sys.executable, "-m", "pip", "install", "--quiet", "rich"], check=True)
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
    from rich.prompt import Prompt
    from rich.rule import Rule
    from rich.columns import Columns
    from rich import box

console = Console()
TMPDIR = Path(tempfile.mkdtemp(prefix="pipe_playground_"))


# ── Helpers ─────────────────────────────────────────────────────────────────

def cls():
    console.clear()

def section(title):
    console.print()
    console.rule(f"[bold magenta]{title}[/]")
    console.print()

def press_enter():
    console.input("\n[dim]  Presioná Enter para continuar...[/]")

def run_and_show(cmd, title=None):
    """Ejecuta un comando y muestra su salida en un panel."""
    if title:
        console.print(f"\n[bold]$ [bold yellow]{cmd}[/][/]")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    stdout = result.stdout.strip()
    stderr = result.stderr.strip()
    if stdout:
        console.print(Panel(stdout, border_style="green", title="stdout"))
    if stderr:
        console.print(Panel(stderr, border_style="red", title="stderr"))
    return result

def pipe_diagram(*etapas):
    """
    Dibuja un diagrama visual de un pipeline.
    etapas: lista de strings con cada comando del pipe.
    """
    parts = []
    for i, etapa in enumerate(etapas):
        parts.append(f"[bold cyan]{etapa}[/]")
        if i < len(etapas) - 1:
            parts.append("[bold yellow] | [/]")
    console.print("  " + "".join(parts))
    console.print()

def fd_pipe_table(cmd_izq, cmd_der):
    """Muestra la tabla de FDs de los dos procesos en un pipe."""
    left = Table(title=f"[cyan]{cmd_izq}[/]", box=box.ROUNDED, show_lines=True, title_style="bold")
    left.add_column("FD", style="bold yellow", justify="center", width=4)
    left.add_column("Nombre", width=8)
    left.add_column("Destino", width=22)
    left.add_row("0", "stdin",  Text("teclado", style="green"))
    left.add_row("1", "stdout", Text("→ extremo escritura del pipe", style="bold yellow"))
    left.add_row("2", "stderr", Text("pantalla", style="green"))

    right = Table(title=f"[cyan]{cmd_der}[/]", box=box.ROUNDED, show_lines=True, title_style="bold")
    right.add_column("FD", style="bold yellow", justify="center", width=4)
    right.add_column("Nombre", width=8)
    right.add_column("Destino", width=22)
    right.add_row("0", "stdin",  Text("← extremo lectura del pipe", style="bold yellow"))
    right.add_row("1", "stdout", Text("pantalla", style="green"))
    right.add_row("2", "stderr", Text("pantalla", style="green"))

    console.print(Columns([left, right], padding=(0, 2)))
    console.print()
    console.print("  [dim]El kernel conecta el stdout de la izquierda con el stdin de la derecha.[/]")


# ── Secciones ────────────────────────────────────────────────────────────────

def intro_pipe():
    cls()
    section("¿Qué es un pipe?")
    console.print(Panel(
        """Un [bold]pipe[/] ( [bold yellow]|[/] ) es un canal unidireccional en memoria que conecta
dos procesos: el [bold]stdout[/] del proceso de la izquierda se convierte
en el [bold]stdin[/] del proceso de la derecha.

  [bold yellow]proceso_A  |  proceso_B[/]

  • A escribe en su FD 1 (stdout)
  • B lee de su FD 0 (stdin)
  • El kernel los conecta internamente sin usar archivos en disco

El pipe es la base de la [bold]filosofía UNIX[/]:
  "Hacé programas que hagan una sola cosa bien,
   y que puedan conectarse entre sí."

Cada programa no sabe si su stdin viene del teclado o de otro proceso.
Cada programa no sabe si su stdout va a la pantalla o a otro proceso.
Esa ignorancia es la clave del diseño.""",
        title="El pipe  |", border_style="cyan"
    ))
    console.print()
    fd_pipe_table("proceso_A", "proceso_B")
    press_enter()


def demo_pipe_basico():
    cls()
    section("Pipe básico: conectar dos comandos")
    console.print(Panel(
        """La forma más simple: la salida de [bold cyan]ls[/] entra a [bold cyan]grep[/].

  [bold yellow]ls /etc | grep conf[/]

  Sin pipe necesitaríamos:
    1. Guardar la salida de ls en un archivo temporal
    2. Pasarle ese archivo a grep
    3. Borrar el archivo temporal

  El pipe hace todo eso en memoria, sin archivos.""",
        title="Pipe básico", border_style="green"
    ))

    pipe_diagram("ls /etc", "grep conf")
    fd_pipe_table("ls /etc", "grep conf")

    console.print("[bold]Ejecutando:[/] [bold yellow]ls /etc | grep conf[/]")
    run_and_show("ls /etc | grep conf")
    press_enter()


def demo_pipeline_largo():
    cls()
    section("Pipeline largo: varios comandos encadenados")
    console.print(Panel(
        """Podés encadenar tantos comandos como quieras.
Cada [bold yellow]|[/] crea un nuevo proceso y un nuevo pipe.

  [bold yellow]cat /etc/passwd | grep bash | cut -d: -f1 | sort[/]

  Esto forma 4 procesos corriendo [bold]en paralelo[/]:
    • cat   lee el archivo y lo vuelca
    • grep  filtra las líneas con "bash"
    • cut   extrae el primer campo (usuario)
    • sort  ordena alfabéticamente

  El kernel sincroniza el flujo: si grep no consume rápido,
  cat se bloquea hasta que haya lugar en el buffer del pipe.""",
        title="Pipeline de 4 etapas", border_style="green"
    ))

    pipe_diagram("cat /etc/passwd", "grep bash", "cut -d: -f1", "sort")

    console.print("[bold]Ejecutando:[/]")
    run_and_show("cat /etc/passwd | grep bash | cut -d: -f1 | sort")
    press_enter()


def demo_wc():
    cls()
    section("Contar cosas con wc")
    console.print(Panel(
        """[bold cyan]wc[/] (word count) es el clásico destino de un pipe para contar:
  • [bold]wc -l[/]  → líneas
  • [bold]wc -w[/]  → palabras
  • [bold]wc -c[/]  → bytes

  [bold yellow]ls /etc | wc -l[/]   →  ¿cuántos archivos hay en /etc?""",
        title="Contar con wc", border_style="green"
    ))

    ejemplos = [
        ("ls /etc | wc -l",              "Cantidad de archivos en /etc"),
        ("cat /etc/passwd | wc -l",      "Cantidad de usuarios en el sistema"),
        ("ps aux | wc -l",               "Procesos corriendo ahora"),
    ]

    for cmd, desc in ejemplos:
        console.print(f"\n[dim]{desc}[/]")
        pipe_diagram(*cmd.split(" | "))
        run_and_show(cmd)

    press_enter()


def demo_sort_uniq():
    cls()
    section("sort + uniq: el dúo clásico")
    console.print(Panel(
        """[bold cyan]uniq[/] elimina líneas duplicadas [bold]consecutivas[/].
Por eso siempre se usa con [bold cyan]sort[/] primero.

  [bold yellow]comando | sort | uniq -c | sort -rn | head[/]

  Este pipeline es uno de los más usados en sistemas UNIX:
  1. [bold]sort[/]       → ordena (agrupa los iguales)
  2. [bold]uniq -c[/]    → cuenta y elimina duplicados
  3. [bold]sort -rn[/]   → ordena por frecuencia (mayor primero)
  4. [bold]head[/]       → muestra solo los primeros""",
        title="sort | uniq | sort | head", border_style="green"
    ))

    # Crear archivo con datos repetidos
    data = TMPDIR / "accesos.txt"
    data.write_text(
        "192.168.1.1\n10.0.0.1\n192.168.1.1\n172.16.0.5\n"
        "10.0.0.1\n192.168.1.1\n172.16.0.5\n10.0.0.2\n"
        "192.168.1.1\n10.0.0.1\n172.16.0.5\n192.168.1.1\n"
    )

    console.print(f"\n[bold]Archivo de ejemplo ({data.name}) — IPs que accedieron al servidor:[/]")
    console.print(Panel(data.read_text(), border_style="dim"))

    cmd = f"cat {data} | sort | uniq -c | sort -rn"
    console.print(f"\n[bold]¿Qué IP accedió más veces?[/]")
    pipe_diagram(f"cat {data.name}", "sort", "uniq -c", "sort -rn")
    run_and_show(cmd)
    press_enter()


def demo_xargs():
    cls()
    section("xargs: convertir stdin en argumentos")
    console.print(Panel(
        """Algunos comandos no leen de stdin sino que esperan [bold]argumentos[/].
[bold cyan]xargs[/] toma lo que viene por stdin y lo convierte en argumentos.

  [bold yellow]echo "hola mundo" | wc -w[/]          → wc lee de stdin ✓
  [bold yellow]ls *.py | rm[/]                       → rm NO lee stdin ✗
  [bold yellow]ls *.py | xargs rm[/]                 → xargs lo convierte ✓

  También sirve para procesar en lotes:
  [bold yellow]find . -name "*.log" | xargs wc -l[/]""",
        title="xargs", border_style="green"
    ))

    # Crear archivos de prueba
    for i in range(4):
        (TMPDIR / f"test_{i}.log").write_text(f"línea 1\nlínea 2\nlínea 3\n" * (i + 1))

    cmd = f"find {TMPDIR} -name '*.log' | xargs wc -l"
    console.print(f"\n[bold]Contando líneas de todos los .log:[/]")
    pipe_diagram(f"find {TMPDIR.name} -name '*.log'", "xargs wc -l")
    run_and_show(cmd)
    press_enter()


def demo_tee():
    cls()
    section("tee: bifurcar el pipe")
    console.print(Panel(
        """[bold cyan]tee[/] es como una T en una cañería: recibe un flujo y lo manda
a [bold]dos destinos[/] al mismo tiempo: stdout (para seguir el pipe)
y uno o más archivos.

  [bold yellow]comando | tee archivo.txt | siguiente_comando[/]

  Útil para guardar la salida intermedia sin cortar el pipeline.""",
        title="tee — bifurcación del pipe", border_style="green"
    ))

    logfile = TMPDIR / "log_procesos.txt"
    cmd = f"ps aux | tee {logfile} | grep python"

    console.print(f"\n[bold]Listar procesos, guardar en archivo Y filtrar python:[/]")
    pipe_diagram("ps aux", f"tee {logfile.name}", "grep python")
    run_and_show(cmd)

    console.print(f"\nEl archivo [bold]{logfile.name}[/] tiene [bold]todos[/] los procesos:")
    run_and_show(f"wc -l < {logfile}")
    press_enter()


def demo_stderr_en_pipe():
    cls()
    section("stderr no entra al pipe (a menos que lo fuerces)")
    console.print(Panel(
        """El pipe solo conecta [bold]stdout (FD 1)[/].
[bold]stderr (FD 2)[/] sigue yendo a la pantalla aunque uses [bold]|[/].

  [bold yellow]ls /etc /no_existe | grep conf[/]
    • stdout de ls  → pipe → grep
    • stderr de ls  → pantalla directamente

Para meter stderr en el pipe:
  [bold yellow]ls /etc /no_existe 2>&1 | grep conf[/]
    Primero redirigís stderr a stdout, después el pipe los lleva juntos.""",
        title="stderr en pipes", border_style="yellow"
    ))

    console.print("\n[bold]Sin combinar:[/] el error de /no_existe aparece en pantalla,")
    console.print("[dim]grep solo filtra el stdout:[/]")
    pipe_diagram("ls /etc /no_existe", "grep conf")
    run_and_show("ls /etc /no_existe | grep conf")

    console.print("\n[bold]Con 2>&1:[/] stderr entra al pipe y grep lo ve también:")
    pipe_diagram("ls /etc /no_existe 2>&1", "grep -E 'conf|No existe|cannot'")
    run_and_show("ls /etc /no_existe 2>&1 | grep -E 'conf|No such'")
    press_enter()


def demo_pipe_python():
    cls()
    section("Pipe desde Python: subprocess con PIPE")
    console.print(Panel(
        """Desde Python podés construir pipelines usando [bold cyan]subprocess[/].
Cada proceso conecta su stdout al stdin del siguiente,
igual que el shell hace con [bold]|[/].

Esto es lo que el shell hace internamente cuando escribís [bold yellow]A | B[/]:
  1. Llama a [bold]os.pipe()[/] → obtiene (fd_read, fd_write)
  2. Fork → hijo A: su stdout apunta a fd_write
  3. Fork → hijo B: su stdin apunta a fd_read
  4. Exec en cada hijo""",
        title="Pipes en Python", border_style="cyan"
    ))

    code = '''\
import subprocess

# Equivalente a:  ls /etc | grep conf | wc -l
p1 = subprocess.Popen(["ls", "/etc"],
                      stdout=subprocess.PIPE)

p2 = subprocess.Popen(["grep", "conf"],
                      stdin=p1.stdout,
                      stdout=subprocess.PIPE)
p1.stdout.close()  # permite que p1 reciba SIGPIPE si p2 termina

p3 = subprocess.Popen(["wc", "-l"],
                      stdin=p2.stdout,
                      stdout=subprocess.PIPE)
p2.stdout.close()

salida, _ = p3.communicate()
print(f"Archivos con 'conf' en /etc: {salida.decode().strip()}")
'''

    from rich.syntax import Syntax
    console.print(Syntax(code, "python", theme="monokai", line_numbers=True))

    console.print("\n[bold]Ejecutando ese código:[/]")
    result = subprocess.run(["python3", "-c", code], capture_output=True, text=True)
    console.print(Panel(result.stdout.strip(), border_style="green"))
    press_enter()


def playground():
    cls()
    section("🎮 Playground libre — escribí tus pipelines")
    console.print(Panel(
        """Probá tus propios pipelines. Algunos para arrancar:

  [bold yellow]ls /usr/bin | shuf | head -10[/]          (10 comandos al azar)
  [bold yellow]cat /etc/passwd | cut -d: -f1,7 | sort[/]  (usuarios y sus shells)
  [bold yellow]ps aux | sort -k3 -rn | head -5[/]         (top 5 por CPU)
  [bold yellow]echo "a b c a b a" | tr ' ' '\\n' | sort | uniq -c | sort -rn[/]
  [bold yellow]seq 1 100 | paste - - - | head -5[/]        (3 columnas)

Escribí [bold red]salir[/] para volver al menú.""",
        title="Playground", border_style="magenta"
    ))

    while True:
        cmd = Prompt.ask("\n  [bold yellow]$[/]").strip()
        if cmd.lower() in ("salir", "exit", "q"):
            break
        if not cmd:
            continue
        try:
            subprocess.run(cmd, shell=True, cwd=TMPDIR)
        except Exception as e:
            console.print(f"[red]Error: {e}[/]")


# ── Menú principal ───────────────────────────────────────────────────────────

MENU = """
[bold cyan]¿Qué querés explorar?[/]

  [bold yellow]1[/]  ¿Qué es un pipe y cómo funciona internamente?
  [bold yellow]2[/]  Pipe básico: conectar dos comandos
  [bold yellow]3[/]  Pipeline largo: varios comandos encadenados
  [bold yellow]4[/]  sort + uniq: contar y ordenar
  [bold yellow]5[/]  xargs: convertir stdin en argumentos
  [bold yellow]6[/]  tee: bifurcar el pipe
  [bold yellow]7[/]  stderr no entra al pipe (y cómo forzarlo)
  [bold yellow]8[/]  Pipes desde Python con subprocess.Popen
  [bold yellow]9[/]  🎮  Playground libre
  [bold yellow]0[/]  Salir
"""

OPCIONES = {
    "1": intro_pipe,
    "2": demo_pipe_basico,
    "3": demo_pipeline_largo,
    "4": demo_sort_uniq,
    "5": demo_xargs,
    "6": demo_tee,
    "7": demo_stderr_en_pipe,
    "8": demo_pipe_python,
    "9": playground,
}


def main():
    cls()
    console.print(Panel(
        "[bold cyan]Playground de Pipes en la Shell[/]\n"
        "Computación II — 2026 — Clase 4",
        border_style="cyan", padding=(1, 4)
    ))

    while True:
        console.print(MENU)
        opcion = Prompt.ask("  Opción", default="0").strip()

        if opcion == "0":
            import shutil
            shutil.rmtree(TMPDIR, ignore_errors=True)
            console.print("\n[bold green]¡Hasta la próxima![/]\n")
            break

        fn = OPCIONES.get(opcion)
        if fn:
            fn()
            cls()
        else:
            console.print("[red]Opción inválida[/]")


if __name__ == "__main__":
    main()
