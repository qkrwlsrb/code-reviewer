import stat
import subprocess
import sys
from pathlib import Path

HOOK_MARKER = "# managed-by: code-reviewer"


def _find_git_dir() -> Path | None:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--git-dir"],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
        return Path(out).resolve()
    except subprocess.CalledProcessError:
        return None


def _cr_executable() -> str:
    """Return the cr executable co-located with the running Python."""
    bin_dir = Path(sys.executable).parent
    for name in ("cr", "cr.exe"):
        candidate = bin_dir / name
        if candidate.exists():
            return str(candidate)
    return "cr"


def _to_posix_path(p: str) -> str:
    """Convert Windows path to POSIX for use inside a sh script."""
    p = p.replace("\\", "/")
    if len(p) >= 2 and p[1] == ":":
        p = "/" + p[0].lower() + p[2:]
    return p


def _build_hook(cr_path: str, block_on_high: bool) -> str:
    posix = _to_posix_path(cr_path)
    flag = " --block-on-high" if block_on_high else ""
    return f"""#!/bin/sh
{HOOK_MARKER}
"{posix}" review{flag}
"""


def install(block_on_high: bool = False) -> Path:
    git_dir = _find_git_dir()
    if git_dir is None:
        raise RuntimeError("Not inside a git repository.")

    hooks_dir = git_dir / "hooks"
    hooks_dir.mkdir(exist_ok=True)
    hook_path = hooks_dir / "pre-commit"

    # Preserve existing non-managed hook content
    if hook_path.exists():
        existing = hook_path.read_text(encoding="utf-8")
        if HOOK_MARKER not in existing:
            raise RuntimeError(
                f"A pre-commit hook already exists at {hook_path} and was not "
                "created by code-reviewer. Remove it manually before installing."
            )

    hook_path.write_text(_build_hook(_cr_executable(), block_on_high), encoding="utf-8")
    hook_path.chmod(hook_path.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    return hook_path


def uninstall() -> Path | None:
    git_dir = _find_git_dir()
    if git_dir is None:
        raise RuntimeError("Not inside a git repository.")

    hook_path = git_dir / "hooks" / "pre-commit"
    if not hook_path.exists():
        return None
    if HOOK_MARKER not in hook_path.read_text(encoding="utf-8"):
        return None

    hook_path.unlink()
    return hook_path


def is_installed() -> bool:
    git_dir = _find_git_dir()
    if git_dir is None:
        return False
    hook_path = git_dir / "hooks" / "pre-commit"
    return hook_path.exists() and HOOK_MARKER in hook_path.read_text(encoding="utf-8")
