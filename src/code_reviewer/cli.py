import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import typer
from rich.console import Console

app = typer.Typer(
    name="cr",
    help="AI-powered code reviewer — runs in your terminal.",
    no_args_is_help=True,
)
console = Console()


@app.callback(invoke_without_command=True)
def main(version: bool = typer.Option(False, "--version", "-v", help="Show version and exit.")):
    if version:
        from code_reviewer import __version__
        console.print(f"code-reviewer {__version__}")
        raise typer.Exit()
