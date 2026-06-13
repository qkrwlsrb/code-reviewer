from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from code_reviewer.reviewer import ReviewResult, Severity

console = Console()

_COLORS = {
    Severity.HIGH:   "red",
    Severity.MEDIUM: "yellow",
    Severity.LOW:    "cyan",
    Severity.INFO:   "dim",
}
_ICONS = {
    Severity.HIGH:   "✗",
    Severity.MEDIUM: "⚠",
    Severity.LOW:    "ℹ",
    Severity.INFO:   "·",
}


def _print_legend() -> None:
    console.print(
        "[dim]Severity — "
        "[red]HIGH[/red]: 보안·크래시(즉시 수정)  "
        "[yellow]MEDIUM[/yellow]: 버그·성능(수정 권장)  "
        "[cyan]LOW[/cyan]: 나쁜 관행(고려)  "
        "INFO: 선택적 개선[/dim]"
    )
    console.print()


def display_review(result: ReviewResult) -> None:
    console.print()
    console.rule("[bold white]cr · Code Review[/bold white]")

    if result.truncated:
        console.print("[yellow]⚠ Diff was truncated (>120 KB). Review covers the first portion only.[/yellow]\n")

    if not result.issues:
        console.print(
            Panel(
                f"[green]{result.summary or 'No issues detected.'}[/green]",
                title="[green]✓ Clean[/green]",
                border_style="green",
            )
        )
        console.print()
        _print_legend()
        return

    for issue in result.issues:
        color = _COLORS[issue.severity]
        icon = _ICONS[issue.severity]

        location = f"[dim]{issue.file}:{issue.line}  [/dim]" if issue.file else ""
        title_line = (
            f"{location}"
            f"[bold {color}]{icon} {issue.severity.value}[/bold {color}]"
            f"  [dim]{issue.category}[/dim]"
        )

        body = Text()
        body.append(f"{issue.title}\n", style="bold white")
        body.append(f"{issue.description}", style="default")
        if issue.suggestion:
            body.append("\n\nSuggestion: ", style=f"bold {color}")
            body.append(issue.suggestion, style=color)

        console.print(Panel(body, title=title_line, border_style=color))

    # --- summary bar ---
    counts: dict[Severity, int] = {}
    for issue in result.issues:
        counts[issue.severity] = counts.get(issue.severity, 0) + 1

    parts = []
    for sev in (Severity.HIGH, Severity.MEDIUM, Severity.LOW, Severity.INFO):
        if sev in counts:
            c = _COLORS[sev]
            parts.append(f"[{c}]{counts[sev]} {sev.value}[/{c}]")

    console.print(f"\n[bold]Summary:[/bold] {result.summary}")
    console.print("Issues: " + "  ·  ".join(parts))
    console.print()
    _print_legend()
