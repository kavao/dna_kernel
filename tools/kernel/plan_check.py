#!/usr/bin/env python3
"""Check progress formatting in plan and design Markdown documents."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Iterable


PROGRESS_HEADINGS = {"進捗", "Progress"}
CHECKBOX_RE = re.compile(r"^\s*-\s+\[([^\]]*)\]\s*(.*)$")
LEVEL_TWO_HEADING_RE = re.compile(r"^##\s+\S")


def _progress_section(lines: list[str]) -> tuple[int, int] | None:
    start: int | None = None
    for index, line in enumerate(lines):
        if not line.startswith("## "):
            continue
        heading = line[3:].strip()
        if heading in PROGRESS_HEADINGS:
            start = index + 1
            break

    if start is None:
        return None

    end = len(lines)
    for index in range(start, len(lines)):
        if LEVEL_TWO_HEADING_RE.match(lines[index]):
            end = index
            break
    return start, end


def check_text(text: str, *, source: str = "<document>") -> list[str]:
    """Return human-readable errors for one Markdown document."""

    lines = text.splitlines()
    section = _progress_section(lines)
    if section is None:
        return [f"{source}: ## 進捗 または ## Progress セクションがありません"]

    start, end = section
    errors: list[str] = []
    checklist_count = 0
    for index in range(start, end):
        match = CHECKBOX_RE.match(lines[index])
        if match is None:
            continue

        checklist_count += 1
        marker, label = match.groups()
        line_number = index + 1
        if marker not in {" ", "x"}:
            errors.append(
                f"{source}:{line_number}: チェック状態は [ ] または [x] を使用してください"
            )
        if not label.strip():
            errors.append(f"{source}:{line_number}: チェック項目の説明がありません")

    if checklist_count == 0:
        errors.append(f"{source}: 進捗セクションにチェック項目がありません")
    return errors


def _markdown_files(paths: Iterable[Path]) -> list[Path]:
    files: list[Path] = []
    for path in paths:
        if path.is_file():
            if path.suffix.lower() == ".md":
                files.append(path)
            continue
        if path.is_dir():
            files.extend(sorted(candidate for candidate in path.rglob("*.md")))
    return sorted(set(files))


def check_paths(paths: Iterable[Path]) -> tuple[int, list[str]]:
    """Check Markdown files and return ``(exit_code, output_lines)``."""

    requested_paths = list(paths)
    missing = [path for path in requested_paths if not path.exists()]
    if missing:
        return 1, [f"検査対象が存在しません: {path}" for path in missing]

    files = _markdown_files(requested_paths)
    if not files:
        return 0, ["SKIP: 検査対象のMarkdownファイルがありません"]

    output: list[str] = []
    failed = False
    for path in files:
        errors = check_text(path.read_text(encoding="utf-8"), source=str(path))
        if errors:
            failed = True
            output.extend(errors)
        else:
            output.append(f"OK: {path}")
    return (1 if failed else 0), output


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="計画書・設計書の進捗チェックボックス形式を検査します。"
    )
    parser.add_argument(
        "paths",
        nargs="*",
        type=Path,
        default=[Path("_workingspace/plans")],
        help="検査対象のMarkdownファイルまたはディレクトリ（既定: _workingspace/plans）",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    exit_code, output = check_paths(args.paths)
    stream = sys.stdout if exit_code == 0 else sys.stderr
    for line in output:
        print(line, file=stream)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
