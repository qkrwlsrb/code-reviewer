# code-reviewer

**언어 선택 · Language**  
[한국어](#한국어) · [English](#english)

---

## 한국어

AI 기반 터미널 코드 리뷰어. staged된 git 변경사항을 Google Gemini로 분석해 커밋 전에 보안 취약점, 버그, 코드 품질 문제를 알려줍니다.

### 기능

- `git diff --staged` 변경사항을 Gemini 2.5 Flash로 자동 분석
- 심각도별 이슈 분류: **HIGH** · **MEDIUM** · **LOW** · **INFO**
- pre-commit 훅으로 설치해 커밋마다 자동 실행
- HIGH 심각도 이슈 발생 시 커밋 차단 (선택)
- 대용량 diff 자동 처리 (120 KB 초과 시 트림)

### 요구사항

- Python 3.11+
- [Google AI Studio](https://aistudio.google.com/app/apikey) API 키 (무료 티어 제공)
- Git

### 설치

```sh
pip install .
```

Gemini API 키를 환경변수로 등록합니다:

```powershell
# Windows (영구 등록)
[System.Environment]::SetEnvironmentVariable("GEMINI_API_KEY", "your-key", "User")
```

```sh
# macOS / Linux
export GEMINI_API_KEY=your-key
```

### 사용법

#### 수동 리뷰

```sh
git add <파일>
cr review
```

출력 예시:

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

#### pre-commit 훅

커밋할 때마다 자동으로 리뷰가 실행되도록 훅을 설치합니다:

```sh
cr install-hook
```

HIGH 이슈 발생 시 커밋을 차단하려면:

```sh
cr install-hook --block-on-high
```

훅 제거:

```sh
cr uninstall-hook
```

훅 설치 여부 확인:

```sh
cr hook-status
```

### 명령어

| 명령어 | 설명 |
|---|---|
| `cr review` | staged 변경사항 리뷰 |
| `cr review --block-on-high` | HIGH 이슈 발견 시 exit 1 |
| `cr install-hook` | pre-commit 훅 설치 |
| `cr install-hook --block-on-high` | HIGH 이슈 시 커밋 차단 훅 설치 |
| `cr uninstall-hook` | pre-commit 훅 제거 |
| `cr hook-status` | 훅 설치 여부 확인 |
| `cr --version` | 버전 확인 |

### 심각도 기준

| 레벨 | 의미 | 대응 |
|---|---|---|
| **HIGH** | 보안 취약점, 인젝션 위험, 인증 우회, 데이터 노출, 크래시 | 즉시 수정 |
| **MEDIUM** | 로직 버그, 위험한 API 오용, 성능 문제, 유효성 검사 누락 | 수정 권장 |
| **LOW** | 사소한 나쁜 관행, 중복 코드, 불명확한 네이밍 | 고려 |
| **INFO** | 선택적 개선 사항, 스타일 제안 | 선택 사항 |

### 개발

```sh
pip install -e ".[dev]"
pytest
```

---

## English

AI-powered code reviewer that runs in your terminal. Analyzes staged git changes via Google Gemini and surfaces security vulnerabilities, bugs, and quality issues before you commit.

### Features

- Reviews staged changes (`git diff --staged`) using Gemini 2.5 Flash
- Categorizes issues by severity: **HIGH** · **MEDIUM** · **LOW** · **INFO**
- Installs as a pre-commit hook — runs automatically on every commit
- Blocks commits on HIGH severity issues (optional)
- Handles large diffs gracefully (truncates at 120 KB)

### Requirements

- Python 3.11+
- A [Google AI Studio](https://aistudio.google.com/app/apikey) API key (free tier available)
- Git

### Installation

```sh
pip install .
```

Set your Gemini API key:

```powershell
# Windows (permanent)
[System.Environment]::SetEnvironmentVariable("GEMINI_API_KEY", "your-key", "User")
```

```sh
# macOS / Linux
export GEMINI_API_KEY=your-key
```

### Usage

#### Manual review

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

#### Pre-commit hook

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

### Commands

| Command | Description |
|---|---|
| `cr review` | Review staged changes |
| `cr review --block-on-high` | Review and exit 1 if any HIGH issue found |
| `cr install-hook` | Install pre-commit hook |
| `cr install-hook --block-on-high` | Install hook that blocks on HIGH issues |
| `cr uninstall-hook` | Remove the pre-commit hook |
| `cr hook-status` | Show whether the hook is installed |
| `cr --version` | Show version |

### Severity levels

| Level | Meaning | Action |
|---|---|---|
| **HIGH** | Security vulnerabilities, injection risks, auth bypass, data exposure, crashes | Fix immediately |
| **MEDIUM** | Logic bugs, dangerous API misuse, performance pitfalls, missing validation | Recommended fix |
| **LOW** | Minor bad practices, redundant code, unclear naming | Consider fixing |
| **INFO** | Optional improvements, stylistic suggestions | Optional |

### Development

```sh
pip install -e ".[dev]"
pytest
```

### License

MIT
