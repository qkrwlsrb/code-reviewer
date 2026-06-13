import json
import os
import re
import time
from dataclasses import dataclass, field
from enum import Enum

from google import genai
from google.genai import types as genai_types
from google.genai.errors import ClientError

MAX_DIFF_BYTES = 120_000  # ~30k tokens
MAX_RETRIES = 3
_RETRY_BACKOFF = [30, 60, 90]  # seconds between attempts


class QuotaExceededError(RuntimeError):
    pass

_SYSTEM_PROMPT_BASE = """\
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

_LANG_INSTRUCTIONS = {
    "ko": "\n\n'description'과 'suggestion' 필드의 값을 한국어(Korean)로 작성하세요.",
    "en": "",
}


def _build_system_prompt(lang: str) -> str:
    return _SYSTEM_PROMPT_BASE + _LANG_INSTRUCTIONS.get(lang, "")


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

    # Strip markdown fences
    if raw.startswith("```"):
        parts = raw.split("```")
        raw = parts[1].lstrip("json").strip() if len(parts) >= 2 else raw

    # raw_decode tolerates trailing text after the JSON object
    try:
        decoder = json.JSONDecoder()
        data, _ = decoder.raw_decode(raw)
    except json.JSONDecodeError:
        # Fallback: find the first {...} block in the text
        match = re.search(r'\{[\s\S]*\}', raw)
        if not match:
            raise
        data = json.loads(match.group())

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


def review_diff(diff: str, model: str = "gemini-2.5-flash", lang: str = "en") -> ReviewResult:
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
                    system_instruction=_build_system_prompt(lang),
                    max_output_tokens=2048,
                ),
            )
            break
        except ClientError as e:
            if e.code in (429, 503) and attempt < MAX_RETRIES:
                time.sleep(_RETRY_BACKOFF[attempt])
            elif e.code == 429:
                raise QuotaExceededError(
                    "Gemini API 무료 한도에 도달했습니다. 잠시 후 다시 시도하거나 "
                    "https://aistudio.google.com 에서 한도를 확인하세요."
                ) from e
            else:
                raise

    result = _parse_response(response.text)
    result.truncated = truncated
    return result
