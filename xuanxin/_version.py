"""Resolve package version, using git commit hash for dev builds."""

from __future__ import annotations

import subprocess
from pathlib import Path

BASE_VERSION = "0.1.1.dev1"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def git_commit_hash(short: bool = True) -> str | None:
    """Return the current git commit hash, or None when unavailable."""
    cmd = ["git", "rev-parse", "--short", "HEAD"] if short else ["git", "rev-parse", "HEAD"]
    try:
        result = subprocess.run(
            cmd,
            cwd=_repo_root(),
            capture_output=True,
            text=True,
            timeout=2,
            check=True,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    value = result.stdout.strip()
    return value or None


def is_dev_version(version: str) -> bool:
    """Return True for in-development version strings."""
    return ".dev" in version


def resolve_version(base: str = BASE_VERSION) -> str:
    """Use git commit hash as version for dev builds."""
    if is_dev_version(base):
        commit = git_commit_hash()
        if commit:
            return commit
    return base


__version__ = resolve_version()
