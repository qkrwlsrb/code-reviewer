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

_UI = {
    "en": {
        "header":     "cr · Code Review",
        "truncated":  "⚠ Diff was truncated (>120 KB). Review covers the first portion only.",
        "clean_title": "✓ Clean",
        "no_issues":  "No issues detected.",
        "summary":    "Summary",
        "issues":     "Issues",
        "suggestion": "Suggestion",
        "legend": (
            "[dim]Severity — "
            "[red]HIGH[/red]: Security·Crash (fix immediately)  "
            "[yellow]MEDIUM[/yellow]: Bug·Performance (fix recommended)  "
            "[cyan]LOW[/cyan]: Bad practice (consider)  "
            "INFO: Optional[/dim]"
        ),
    },
    "ko": {
        "header":     "cr · 코드 리뷰",
        "truncated":  "⚠ Diff가 잘렸습니다 (>120 KB). 첫 번째 부분만 리뷰됩니다.",
        "clean_title": "✓ 이상 없음",
        "no_issues":  "발견된 이슈가 없습니다.",
        "summary":    "요약",
        "issues":     "발견된 이슈",
        "suggestion": "제안",
        "legend": (
            "[dim]심각도 — "
            "[red]HIGH[/red]: 보안·크래시(즉시 수정)  "
            "[yellow]MEDIUM[/yellow]: 버그·성능(수정 권장)  "
            "[cyan]LOW[/cyan]: 나쁜 관행(고려)  "
            "INFO: 선택적 개선[/dim]"
        ),
    },
}


def display_review(result: ReviewResult, lang: str = "en") -> None:
    ui = _UI.get(lang, _UI["en"])

    console.print()
    console.rule(f"[bold white]{ui['header']}[/bold white]")

    if result.truncated:
        console.print(f"[yellow]{ui['truncated']}[/yellow]\n")

    if not result.issues:
        console.print(
            Panel(
                f"[green]{result.summary or ui['no_issues']}[/green]",
                title=f"[green]{ui['clean_title']}[/green]",
                border_style="green",
            )
        )
        console.print()
        console.print(ui["legend"])
        console.print()
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
            body.append(f"\n\n{ui['suggestion']}: ", style=f"bold {color}")
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

    console.print(f"\n[bold]{ui['summary']}:[/bold] {result.summary}")
    console.print(f"{ui['issues']}: " + "  ·  ".join(parts))
    console.print()
    console.print(ui["legend"])
    console.print()
