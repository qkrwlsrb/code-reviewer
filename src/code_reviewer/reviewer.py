import json
import os
from dataclasses import dataclass, field
from enum import Enum

import anthropic

MAX_DIFF_BYTES = 120_000  # ~30k tokens

SYSTEM_PROMPT = """\
You are a senior code reviewer specializing in security vulnerabilities and code quality.
Analyze the provided git diff and return findings as JSON only — no prose, no markdown fences.

Return exactly this structure:
{
  "summary": "one-sentence overall assessment",
  "issues": [
    {
      "severity": "HIGH|MEDIUM|LOW|INFO",
      "category": "SECURITY|BUG|QUALITY|STYLE",
      "title": "short title (max 60 chars)",
      "description": "what is wrong and why it matters",
      "suggestion": "concrete fix or improvement",
      "file": "filename or empty string",
      "line": 0
    }
  ]
}

Severity rules:
- HIGH   : security vulnerabilities, injection risks, auth bypass, data exposure, crashes
- MEDIUM : logic bugs, dangerous API misuse, performance pitfalls, missing validation
- LOW    : minor bad practices, redundant code, unclear naming
- INFO   : optional improvements, stylistic suggestions

Only report real issues. If the diff is clean, return an empty issues array.\
"""


class Severity(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


@dataclass
class ReviewIssue:
    severity: Severity
    category: str
    title: str
    description: str
    suggestion: str
    file: str = ""
    line: int = 0


@dataclass
class ReviewResult:
    issues: list[ReviewIssue] = field(default_factory=list)
    summary: str = ""
    truncated: bool = False


def _parse_response(text: str) -> ReviewResult:
    raw = text.strip()
    # Strip accidental markdown fences
    if raw.startswith("```"):
        parts = raw.split("```")
        raw = parts[1].lstrip("json").strip() if len(parts) >= 2 else raw

    data = json.loads(raw)
    issues = [
        ReviewIssue(
            severity=Severity(i.get("severity", "INFO")),
            category=i.get("category", "QUALITY"),
            title=i.get("title", ""),
            description=i.get("description", ""),
            suggestion=i.get("suggestion", ""),
            file=i.get("file", ""),
            line=int(i.get("line") or 0),
        )
        for i in data.get("issues", [])
    ]
    return ReviewResult(issues=issues, summary=data.get("summary", ""))


def review_diff(diff: str, model: str = "claude-haiku-4-5-20251001") -> ReviewResult:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY is not set. "
            "Export it with: set ANTHROPIC_API_KEY=sk-..."
        )

    truncated = False
    encoded = diff.encode("utf-8")
    if len(encoded) > MAX_DIFF_BYTES:
        diff = encoded[:MAX_DIFF_BYTES].decode("utf-8", errors="ignore")
        truncated = True

    client = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model=model,
        max_tokens=2048,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": f"```diff\n{diff}\n```"}],
    )

    result = _parse_response(message.content[0].text)
    result.truncated = truncated
    return result
