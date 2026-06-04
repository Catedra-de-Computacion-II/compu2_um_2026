#!/usr/bin/env python3
"""
fd_playground.py — Playground interactivo de File Descriptors y Redirección
Clase 4 - Computación II 2026 - Universidad de Mendoza
"""

import os
import sys
import subprocess
import tempfile
from pathlib import Path

# ── Instalar rich si no está ────────────────────────────────────────────────
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
    from rich.prompt import Prompt
    from rich.syntax import Syntax
    from rich.rule import Rule
    from rich import box
except ImportError:
    print("Instalando rich (una sola vez)...")
    subprocess.run([sys.executable, "-m", "pip", "install", "--quiet", "rich"], check=True)
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
    from rich.prompt import Prompt
    from rich.syntax import Syntax
    from rich.rule import Rule
    from rich import box

console = Console()
TMPDIR = Path(tempfile.mkdtemp(prefix="fd_playground_"))


# ── Helpers visuales ────────────────────────────────────────────────────────

def cls():
    console.clear()

def fd_table(fd0="stdin  → teclado", fd1="stdout → pantalla", fd2="stderr → pantalla", title="Tabla de File Descriptors del proceso"):
    """Dibuja la tabla de FDs del proceso con los destinos actuales."""
    t = Table(title=title, box=box.ROUNDED, show_lines=True, title_style="bold cyan")
    t.add_column("FD", style="bold yellow", justify="center", width=4)
    t.add_column("Nombre", style="bold", width=10)
    t.add_column("Destino actual", width=40)

    styles = {
        "stdin  → teclado":   "green",
        "stdout → pantalla":  "green",
        "stderr → pantalla":  "green",
    }
    def color(v):
        return styles.get(v, "cyan")

    t.add_row("0", "stdin",  Text(fd0, style=color(fd0)))
    t.add_row("1", "stdout", Text(fd1, style=color(fd1)))
    t.add_row("2", "stderr", Text(fd2, style=color(fd2)))
    return t

def arrow(src, dst):
    console.print(f"\n  [bold yellow]{src}[/]  →  [bold cyan]{dst}[/]\n")

def section(title):
    console.print()
    console.rule(f"[bold magenta]{title}[/]")
    console.print()

def press_enter():
    console.input("\n[dim]  Presioná Enter para continuar...[/]")


# ── Menú principal ──────────────────────────────────────────────────────────

MENU = """
[bold cyan]¿Qué querés explorar?[/]

  [bold yellow]1[/]  ¿Qué es un file descriptor?
  [bold yellow]2[/]  ¿Qué significa [bold]>[/] ?  (stdout → archivo)
  [bold yellow]3[/]  [bold]>>[/]  vs  [bold]>[/]   (append vs overwrite)
  [bold yellow]4[/]  [bold]2>[/]  redirigir stderr
  [bold yellow]5[/]  [bold]2>&1[/]  combinar stdout y stderr
  [bold yellow]6[/]  [bold]<[/]   redirigir stdin
  [bold yellow]7[/]  🎮  Playground libre: escribí tu propio comando
  [bold yellow]0[/]  Salir
"""

# ── Secciones ───────────────────────────────────────────────────────────────

def intro_fds():
    cls()
    section("¿Qué es un File Descriptor?")
    console.print(Panel(
        """Cuando el SO crea un proceso, le abre automáticamente [bold]tres archivos[/]:

  • FD [bold yellow]0[/] — [bold]stdin[/]   → de donde lee el proceso  (por defecto: tu teclado)
  • FD [bold yellow]1[/] — [bold]stdout[/]  → donde escribe la salida  (por defecto: tu pantalla)
  • FD [bold yellow]2[/] — [bold]stderr[/]  → donde escribe los errores (por defecto: tu pantalla)

Un FD es simplemente un [bold cyan]número entero[/] que identifica un archivo abierto.
Todo en UNIX es un archivo: un pipe, un socket, un terminal... todos tienen FD.""",
        title="File Descriptors", border_style="cyan"
    ))
    console.print()
    console.print(fd_table())
    console.print()
    console.print("[dim]Podés verlos en /proc/<pid>/fd mientras un proceso corre.[/]")
    press_enter()


def demo_stdout_redir():
    cls()
    section("El operador  >  (redirigir stdout a un archivo)")
    console.print(Panel(
        """[bold]>[/]  le dice al shell: [italic]"antes de ejecutar el comando, redirigí el FD 1 a este archivo"[/]

  [bold yellow]echo "hola" > salida.txt[/]

  Lo que hace el shell por debajo:
    1. Abre [bold]salida.txt[/] para escritura (lo crea o lo vacía si existe)
    2. Hace [bold]dup2(fd_archivo, 1)[/]  →  FD 1 ahora apunta al archivo
    3. Ejecuta [bold]echo "hola"[/]
    4. Echo escribe en FD 1 creyendo que es la pantalla... pero es el archivo.""",
        title="> redirección de stdout", border_style="green"
    ))

    console.print("[bold]Antes de la redirección:[/]")
    console.print(fd_table())
    console.print()
    outfile = TMPDIR / "salida.txt"
    console.print(f"[bold]Después de   echo 'hola mundo' > {outfile.name}[/]")
    console.print(fd_table(
        fd1=f"stdout → [bold]{outfile.name}[/] (archivo)",
        fd2="stderr → pantalla"
    ))

    console.print()
    result = subprocess.run(
        f'echo "hola mundo" > {outfile}',
        shell=True, capture_output=True, text=True
    )
    console.print(f"[dim]Ejecutado. En pantalla no aparece nada.[/]")
    console.print(f"Contenido de [bold]{outfile.name}[/]:")
    console.print(Panel(outfile.read_text(), border_style="yellow"))

    console.print("\n[bold red]Ojo:[/] si el archivo ya existía, [bold]>[/] lo [bold red]borra y empieza de cero[/].")
    press_enter()


def demo_append():
    cls()
    section(">>  vs  >   (append vs overwrite)")
    console.print(Panel(
        """  [bold yellow]>[/]   abre el archivo con [bold]O_TRUNC[/]  → lo vacía antes de escribir
  [bold yellow]>>[/]  abre el archivo con [bold]O_APPEND[/] → escribe al final, sin borrar nada

  Típico uso de [bold]>>[/]:  acumular logs sin perder los anteriores.""",
        title=">> vs >", border_style="green"
    ))

    logfile = TMPDIR / "log.txt"
    console.print("[bold]Demo en vivo:[/]")

    for cmd in [
        f'echo "Línea 1" > {logfile}',
        f'echo "Línea 2" >> {logfile}',
        f'echo "Línea 3" >> {logfile}',
    ]:
        console.print(f"  [bold yellow]$ {cmd}[/]")
        subprocess.run(cmd, shell=True)

    console.print(f"\nContenido de [bold]{logfile.name}[/] después de los tres comandos:")
    console.print(Panel(logfile.read_text(), border_style="yellow"))

    console.print("\nAhora con [bold]>[/] (overwrite):")
    cmd = f'echo "Solo esta línea" > {logfile}'
    console.print(f"  [bold yellow]$ {cmd}[/]")
    subprocess.run(cmd, shell=True)
    console.print(Panel(logfile.read_text(), border_style="red"))
    console.print("[bold red]Todo lo anterior se perdió.[/]")
    press_enter()


def demo_stderr_redir():
    cls()
    section("2>  redirigir stderr")
    console.print(Panel(
        """  [bold yellow]2>[/]  redirige el FD [bold]2[/] (stderr) a un archivo.
  stdout (FD 1) sigue yendo a la pantalla.

  [bold yellow]ls /no_existe 2> errores.txt[/]

  El mensaje de error va al archivo, no a la pantalla.
  Muy útil para separar salida normal de errores en scripts.""",
        title="2> redirección de stderr", border_style="red"
    ))

    errfile = TMPDIR / "errores.txt"
    outfile = TMPDIR / "salida_ok.txt"

    cmd = f'ls /etc/hosts /no_existe_jamas 2> {errfile}'
    console.print(f"[bold]Ejecutando:[/] [bold yellow]{cmd}[/]\n")
    result = subprocess.run(cmd, shell=True, capture_output=False)

    console.print(f"\nLo que fue a pantalla (stdout normal):")
    console.print(Panel("/etc/hosts", border_style="green"))

    console.print(f"\nLo que fue a [bold]{errfile.name}[/] (stderr):")
    console.print(Panel(errfile.read_text(), border_style="red"))

    console.print("\n[bold]Tabla de FDs durante la ejecución:[/]")
    console.print(fd_table(
        fd2=f"stderr → {errfile.name} (archivo)"
    ))
    press_enter()


def demo_combine():
    cls()
    section("2>&1  combinar stdout y stderr en el mismo destino")
    console.print(Panel(
        """  [bold yellow]2>&1[/]  significa: [italic]"el FD 2 apunta al mismo lugar que el FD 1"[/]

  [bold yellow]ls /etc/hosts /no_existe > todo.txt 2>&1[/]

  Orden de evaluación (¡importante!):
    1. FD 1 se redirige al archivo  [bold]todo.txt[/]
    2. FD 2 se redirige a donde esté FD 1  →  también a [bold]todo.txt[/]

  Si escribís [bold red]2>&1 > todo.txt[/] (orden invertido) [bold red]NO funciona[/]:
    1. FD 2 apunta a donde está FD 1 ahora  →  pantalla
    2. FD 1 se redirige a todo.txt
    FD 2 quedó apuntando a la pantalla. El orden importa.""",
        title="2>&1", border_style="yellow"
    ))

    allfile = TMPDIR / "todo.txt"
    cmd = f'ls /etc/hosts /no_existe_jamas > {allfile} 2>&1'
    console.print(f"[bold]Ejecutando:[/] [bold yellow]{cmd}[/]")
    subprocess.run(cmd, shell=True)

    console.print(f"\nContenido de [bold]{allfile.name}[/] (stdout + stderr juntos):")
    console.print(Panel(allfile.read_text(), border_style="yellow"))

    console.print("[bold]Tabla de FDs durante la ejecución:[/]")
    console.print(fd_table(
        fd1=f"stdout → {allfile.name}",
        fd2=f"stderr → {allfile.name}  (= FD 1)"
    ))
    press_enter()


def demo_stdin_redir():
    cls()
    section("<  redirigir stdin (entrada desde archivo)")
    console.print(Panel(
        """  [bold yellow]<[/]  redirige el FD [bold]0[/] (stdin) desde un archivo en lugar del teclado.

  [bold yellow]sort < lista.txt[/]

  El programa [bold]sort[/] cree que está leyendo del teclado,
  pero en realidad lee del archivo. No sabe la diferencia.""",
        title="< redirección de stdin", border_style="blue"
    ))

    lista = TMPDIR / "lista.txt"
    lista.write_text("banana\nmanzana\narandano\ndurazno\n")
    console.print(f"[bold]Archivo de entrada [bold]{lista.name}[/]:[/]")
    console.print(Panel(lista.read_text(), border_style="dim"))

    console.print(f"\n[bold]Tabla de FDs con   sort < {lista.name}[/]")
    console.print(fd_table(
        fd0=f"stdin  → {lista.name} (archivo)",
    ))

    cmd = f"sort < {lista}"
    console.print(f"\n[bold]Resultado de [bold yellow]{cmd}[/]:[/]")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    console.print(Panel(result.stdout, border_style="blue"))

    console.print("\n[bold]Combinando todo junto:[/]")
    cmd2 = f"sort < {lista} > {TMPDIR}/ordenado.txt 2>/dev/null"
    console.print(f"  [bold yellow]{cmd2}[/]")
    console.print("  stdin ← archivo,  stdout → archivo,  stderr → /dev/null (basura)")
    press_enter()


def playground():
    cls()
    section("🎮 Playground libre")
    console.print(Panel(
        """Escribí comandos con redirecciones y mirá qué pasa.
El directorio de trabajo temporal es: [bold cyan]""" + str(TMPDIR) + """[/]

Ejemplos para probar:
  [bold yellow]echo "test" > archivo.txt[/]
  [bold yellow]cat < archivo.txt[/]
  [bold yellow]ls /no_existe 2> err.txt && cat err.txt[/]
  [bold yellow]python3 -c "import sys; print('out'); print('err', file=sys.stderr)" > out.txt 2> err.txt[/]

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


# ── Main loop ────────────────────────────────────────────────────────────────

OPCIONES = {
    "1": intro_fds,
    "2": demo_stdout_redir,
    "3": demo_append,
    "4": demo_stderr_redir,
    "5": demo_combine,
    "6": demo_stdin_redir,
    "7": playground,
}

def main():
    cls()
    console.print(Panel(
        "[bold cyan]Playground de File Descriptors y Redirección[/]\n"
        "Computación II — 2026 — Clase 4",
        border_style="cyan", padding=(1, 4)
    ))

    while True:
        console.print(MENU)
        opcion = Prompt.ask("  Opción", default="0").strip()

        if opcion == "0":
            console.print("\n[dim]Limpiando archivos temporales...[/]")
            import shutil
            shutil.rmtree(TMPDIR, ignore_errors=True)
            console.print("[bold green]¡Hasta la próxima![/]\n")
            break

        fn = OPCIONES.get(opcion)
        if fn:
            fn()
            cls()
        else:
            console.print("[red]Opción inválida[/]")


if __name__ == "__main__":
    main()
