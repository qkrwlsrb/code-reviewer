import json
import os
import time
from dataclasses import dataclass, field
from enum import Enum

from google import genai
from google.genai import types as genai_types
from google.genai.errors import ClientError

MAX_DIFF_BYTES = 120_000  # ~30k tokens
MAX_RETRIES = 3
_RETRY_BACKOFF = [30, 60, 90]  # seconds between attempts

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


def review_diff(diff: str, model: str = "gemini-2.5-flash") -> ReviewResult:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is not set. "
            "Export it with: set GEMINI_API_KEY=your-key"
        )

    truncated = False
    encoded = diff.encode("utf-8")
    if len(encoded) > MAX_DIFF_BYTES:
        diff = encoded[:MAX_DIFF_BYTES].decode("utf-8", errors="ignore")
        truncated = True

    client = genai.Client(api_key=api_key)
    for attempt in range(MAX_RETRIES + 1):
        try:
            response = client.models.generate_content(
                model=model,
                contents=f"```diff\n{diff}\n```",
                config=genai_types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    max_output_tokens=2048,
                ),
            )
            break
        except ClientError as e:
            if e.code in (429, 503) and attempt < MAX_RETRIES:
                time.sleep(_RETRY_BACKOFF[attempt])
            else:
                raise

    result = _parse_response(response.text)
    result.truncated = truncated
    return result
