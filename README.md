# code-reviewer

AI-powered code reviewer that runs in your terminal. Analyzes staged git changes via Google Gemini and surfaces security vulnerabilities, bugs, and quality issues before you commit.

## Features

- Reviews staged changes (`git diff --staged`) using Gemini 2.5 Flash
- Categorizes issues by severity: **HIGH** · **MEDIUM** · **LOW** · **INFO**
- Installs as a pre-commit hook — runs automatically on every commit
- Blocks commits on HIGH severity issues (optional)
- Handles large diffs gracefully (truncates at 120 KB)

## Requirements

- Python 3.11+
- A [Google AI Studio](https://aistudio.google.com/app/apikey) API key (free tier available)
- Git

## Installation

```sh
pip install .
```

Set your Gemini API key:

```sh
# Windows (permanent)
[System.Environment]::SetEnvironmentVariable("GEMINI_API_KEY", "your-key", "User")

# macOS / Linux
export GEMINI_API_KEY=your-key
```

## Usage

### Manual review

Review your staged changes at any time:

```sh
git add <files>
cr review
```

Example output:

```
─────────────────────── cr · Code Review ───────────────────────
┌──── src/app.py:42  ✗ HIGH  SECURITY ───────────────────────────┐
│ SQL query built with string interpolation                      │
│ User input is concatenated directly into the SQL query,        │
│ allowing an attacker to inject arbitrary SQL.                  │
│                                                                │
│ Suggestion: Use parameterized queries or an ORM.               │
└────────────────────────────────────────────────────────────────┘

Summary: One critical SQL injection vulnerability detected.
Issues: 1 HIGH
```

### Pre-commit hook

Install the hook so every `git commit` triggers a review automatically:

```sh
cr install-hook
```

To block commits when HIGH severity issues are found:

```sh
cr install-hook --block-on-high
```

Remove the hook:

```sh
cr uninstall-hook
```

Check hook status:

```sh
cr hook-status
```

## Commands

| Command | Description |
|---|---|
| `cr review` | Review staged changes |
| `cr review --block-on-high` | Review and exit 1 if any HIGH issue found |
| `cr install-hook` | Install pre-commit hook |
| `cr install-hook --block-on-high` | Install hook that blocks on HIGH issues |
| `cr uninstall-hook` | Remove the pre-commit hook |
| `cr hook-status` | Show whether the hook is installed |
| `cr --version` | Show version |

## Severity levels

| Level | Meaning |
|---|---|
| **HIGH** | Security vulnerabilities, injection risks, auth bypass, data exposure, crashes |
| **MEDIUM** | Logic bugs, dangerous API misuse, performance pitfalls, missing validation |
| **LOW** | Minor bad practices, redundant code, unclear naming |
| **INFO** | Optional improvements, stylistic suggestions |

## Development

```sh
pip install -e ".[dev]"
pytest
```

## License

MIT
