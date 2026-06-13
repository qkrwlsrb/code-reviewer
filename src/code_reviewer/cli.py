import subprocess
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
def _root(
    ctx: typer.Context,
    version: bool = typer.Option(False, "--version", "-v", help="Show version and exit."),
):
    if version:
        from code_reviewer import __version__
        console.print(f"code-reviewer {__version__}")
        raise typer.Exit()


@app.command()
def review(
    block_on_high: bool = typer.Option(
        False, "--block-on-high",
        help="Exit 1 if any HIGH severity issue is found (blocks the commit).",
    ),
    model: str = typer.Option(
        "gemini-2.5-flash", "--model", "-m",
        help="Gemini model to use for review.",
    ),
):
    """Review staged changes via AI and print findings to the terminal."""
    from code_reviewer import display, reviewer

    result = subprocess.run(
        ["git", "diff", "--staged"],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    diff = result.stdout.strip()

    if not diff:
        console.print("[dim]Nothing staged — skipping review.[/dim]")
        raise typer.Exit(0)

    with console.status("[bold]Reviewing staged changes...[/bold]", spinner="dots"):
        try:
            review_result = reviewer.review_diff(diff, model=model)
        except RuntimeError as exc:
            console.print(f"[red]Error:[/red] {exc}")
            raise typer.Exit(0)  # Don't block commit on tool errors
        except Exception as exc:
            console.print(f"[red]Unexpected error during review:[/red] {exc}")
            raise typer.Exit(0)

    display.display_review(review_result)

    if block_on_high:
        high_count = sum(1 for i in review_result.issues if i.severity.value == "HIGH")
        if high_count:
            console.print(
                f"[bold red]Commit blocked:[/bold red] {high_count} HIGH severity issue(s) found.\n"
                "Fix the issues or commit with [bold]git commit --no-verify[/bold] to skip."
            )
            raise typer.Exit(1)


@app.command("install-hook")
def install_hook(
    block_on_high: bool = typer.Option(
        False, "--block-on-high",
        help="Block commits when HIGH severity issues are found.",
    ),
):
    """Install the pre-commit hook in the current git repository."""
    from code_reviewer import hook

    try:
        path = hook.install(block_on_high=block_on_high)
        console.print(f"[green]✓[/green] Pre-commit hook installed: [bold]{path}[/bold]")
        if block_on_high:
            console.print("[yellow]  Commits will be blocked on HIGH severity issues.[/yellow]")
    except RuntimeError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(1)


@app.command("uninstall-hook")
def uninstall_hook():
    """Remove the code-reviewer pre-commit hook from the current git repository."""
    from code_reviewer import hook

    try:
        path = hook.uninstall()
        if path:
            console.print(f"[green]✓[/green] Hook removed: [bold]{path}[/bold]")
        else:
            console.print("[yellow]No managed hook found.[/yellow]")
    except RuntimeError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(1)


@app.command("hook-status")
def hook_status():
    """Show whether the pre-commit hook is installed in the current repository."""
    from code_reviewer import hook

    if hook.is_installed():
        console.print("[green]✓[/green] Pre-commit hook is installed.")
    else:
        console.print("[dim]Pre-commit hook is not installed.[/dim]")
        console.print("Run [bold]cr install-hook[/bold] to enable.")
