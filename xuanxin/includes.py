"""Conditional markdown includes (bubble ``<!-- include: ... if ... -->``)."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

INCLUDE_PATTERN = re.compile(
    r"<!--\s*include:\s*([^\s]+)\s+if\s+([^>]+)\s*-->",
    re.IGNORECASE,
)


def find_peanut_config(start: Path | str) -> Path | None:
    """Walk up from *start* looking for ``peanut.config``."""
    cur = Path(start).resolve()
    seen: set[Path] = set()
    while cur not in seen:
        seen.add(cur)
        candidate = cur / "peanut.config"
        if candidate.is_file():
            return candidate
        if cur.parent == cur:
            break
        cur = cur.parent
    return None


def load_config(config_path: Path | str | None) -> dict[str, bool]:
    """Load boolean flags from ``peanut.config`` JSON."""
    if config_path is None:
        return {}

    path = Path(config_path).resolve()
    if not path.is_file():
        print(f"Warning: config file not found: {path}", file=sys.stderr)
        return {}

    try:
        raw: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"Warning: invalid JSON in {path}: {exc}", file=sys.stderr)
        return {}
    except OSError as exc:
        print(f"Warning: cannot read {path}: {exc}", file=sys.stderr)
        return {}

    result: dict[str, bool] = {}
    for key, value in raw.items():
        if isinstance(value, bool):
            result[key] = value
        elif isinstance(value, str):
            result[key] = bool(value and value.strip())
        elif isinstance(value, (int, float)):
            result[key] = bool(value)
        else:
            result[key] = bool(value)
    return result


def evaluate_condition(condition_expr: str, config: dict[str, bool]) -> bool:
    """Evaluate bubble-style include conditions (``true``, ``not x``, ``a and b``, ``a or b``)."""
    condition_expr = condition_expr.strip()
    if not condition_expr:
        return False

    while "(" in condition_expr:
        start = condition_expr.rfind("(")
        end = condition_expr.find(")", start)
        if end == -1:
            return False
        inner = condition_expr[start + 1 : end]
        inner_result = evaluate_condition(inner, config)
        condition_expr = (
            condition_expr[:start]
            + str(inner_result).lower()
            + condition_expr[end + 1 :]
        )

    condition_expr = re.sub(
        r"\bnot\s+(\w+)\b",
        lambda match: str(not config.get(match.group(1), False)).lower(),
        condition_expr,
        flags=re.IGNORECASE,
    )

    while " and " in condition_expr.lower():
        match = re.search(r"\b(\w+)\s+and\s+(\w+)\b", condition_expr, re.IGNORECASE)
        if not match:
            break
        left_val = _condition_atom(match.group(1), config)
        right_val = _condition_atom(match.group(2), config)
        condition_expr = (
            condition_expr[: match.start()]
            + str(left_val and right_val).lower()
            + condition_expr[match.end() :]
        )

    while " or " in condition_expr.lower():
        match = re.search(r"\b(\w+)\s+or\s+(\w+)\b", condition_expr, re.IGNORECASE)
        if not match:
            break
        left_val = _condition_atom(match.group(1), config)
        right_val = _condition_atom(match.group(2), config)
        condition_expr = (
            condition_expr[: match.start()]
            + str(left_val or right_val).lower()
            + condition_expr[match.end() :]
        )

    condition_expr = condition_expr.strip().lower()
    if condition_expr in ("true", "false"):
        return condition_expr == "true"
    return config.get(condition_expr, False)


def _condition_atom(name: str, config: dict[str, bool]) -> bool:
    lowered = name.lower()
    if lowered in ("true", "false"):
        return lowered == "true"
    return config.get(name, False)


def process_includes(
    content: str,
    base_dir: Path | str,
    config: dict[str, bool],
    *,
    visited_files: set[Path] | None = None,
    depth: int = 0,
) -> str:
    """Expand ``<!-- include: path if condition -->`` directives."""
    base_dir = Path(base_dir).resolve()
    if visited_files is None:
        visited_files = set()

    if depth > 10:
        print("Warning: maximum include depth (10) exceeded.", file=sys.stderr)
        return content

    def replace_include(match: re.Match[str]) -> str:
        file_path_str = match.group(1).strip()
        condition_expr = match.group(2).strip()

        if not evaluate_condition(condition_expr, config):
            return ""

        include_path = (
            Path(file_path_str).resolve()
            if Path(file_path_str).is_absolute()
            else (base_dir / file_path_str).resolve()
        )

        if include_path in visited_files:
            print(f"Warning: circular include: {include_path}", file=sys.stderr)
            return ""

        if not include_path.is_file():
            print(
                f"Warning: include file not found: {include_path} (from {base_dir})",
                file=sys.stderr,
            )
            return ""

        try:
            included_content = include_path.read_text(encoding="utf-8")
        except OSError as exc:
            print(f"Warning: cannot read include {include_path}: {exc}", file=sys.stderr)
            return ""

        visited_files.add(include_path)
        processed = process_includes(
            included_content,
            include_path.parent,
            config,
            visited_files=visited_files,
            depth=depth + 1,
        )
        visited_files.remove(include_path)
        return f"\n{processed}\n"

    return INCLUDE_PATTERN.sub(replace_include, content)
