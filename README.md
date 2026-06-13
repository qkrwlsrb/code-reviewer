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

**이슈 발견 시:**

**`cr review --lang ko` — 이슈 발견 시:**

```
─────────────────────────────── cr · 코드 리뷰 ────────────────────────────────
┌──────────────────── app.py:1  ✗ HIGH  SECURITY ──────────────────────────────┐
│ 소스 코드에 하드코딩된 비밀번호                                              │
│ 소스 코드에 직접 비밀번호를 하드코딩하는 것은 매우 위험한 보안 취약점입니다. │
│ 코드 저장소에 노출되어 무단 접근의 위험을 초래합니다.                        │
│                                                                              │
│ 제안: 환경 변수, 보안 비밀 관리 서비스, 또는 안전하게 구성된 설정 파일을     │
│ 통해 관리하세요. 절대로 코드에 직접 포함하지 마십시오.                       │
└──────────────────────────────────────────────────────────────────────────────┘
┌──────────────────── app.py:4  ⚠ MEDIUM  BUG ─────────────────────────────────┐
│ 0으로 나누기 예외 처리 누락                                                  │
│ divide 함수는 b가 0일 경우 ZeroDivisionError를 발생시킬 수 있습니다.          │
│                                                                              │
│ 제안: b가 0인지 확인하는 로직을 추가하세요.                                  │
│ 예: if b == 0: raise ValueError("0으로 나눌 수 없습니다")                    │
└──────────────────────────────────────────────────────────────────────────────┘

요약: 하드코딩된 비밀번호와 0으로 나누기 오류에 대한 잠재적 취약점이 있습니다.
발견된 이슈: 1 HIGH  ·  1 MEDIUM

심각도 — HIGH: 보안·크래시(즉시 수정)  MEDIUM: 버그·성능(수정 권장)  LOW: 나쁜 관행(고려)  INFO: 선택적 개선
```

**`cr review --lang ko` — 이슈 없을 시:**

```
─────────────────────────────── cr · 코드 리뷰 ────────────────────────────────
┌────────────────────────────── ✓ 이상 없음 ───────────────────────────────────┐
│ 발견된 이슈가 없습니다.                                                      │
└──────────────────────────────────────────────────────────────────────────────┘

심각도 — HIGH: 보안·크래시(즉시 수정)  MEDIUM: 버그·성능(수정 권장)  LOW: 나쁜 관행(고려)  INFO: 선택적 개선
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

**`cr review` — Issues found:**

```
──────────────────────────── cr · Code Review ─────────────────────────────────
┌──────────────────── app.py:1  ✗ HIGH  SECURITY ──────────────────────────────┐
│ Hardcoded Password in Source Code                                            │
│ A password is hardcoded directly in the source code. This is a critical      │
│ security vulnerability as it exposes credentials in the repository.          │
│                                                                              │
│ Suggestion: Use environment variables or a secrets manager instead.          │
│ Never hardcode credentials in source code.                                   │
└──────────────────────────────────────────────────────────────────────────────┘
┌──────────────────── app.py:4  ⚠ MEDIUM  BUG ─────────────────────────────────┐
│ Missing Division by Zero Handling                                            │
│ The divide function will raise ZeroDivisionError if b is zero.               │
│                                                                              │
│ Suggestion: Add a zero check before dividing.                                │
│ e.g. if b == 0: raise ValueError("Cannot divide by zero")                   │
└──────────────────────────────────────────────────────────────────────────────┘

Summary: Hardcoded password and missing division-by-zero handling detected.
Issues: 1 HIGH  ·  1 MEDIUM

Severity — HIGH: Security·Crash (fix immediately)  MEDIUM: Bug·Performance (fix recommended)  LOW: Bad practice (consider)  INFO: Optional
```

**`cr review` — No issues:**

```
──────────────────────────── cr · Code Review ─────────────────────────────────
┌───────────────────────────────── ✓ Clean ────────────────────────────────────┐
│ No issues detected.                                                          │
└──────────────────────────────────────────────────────────────────────────────┘

Severity — HIGH: Security·Crash (fix immediately)  MEDIUM: Bug·Performance (fix recommended)  LOW: Bad practice (consider)  INFO: Optional
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
