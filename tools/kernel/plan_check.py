#!/usr/bin/env python3
"""Check progress and version-history formatting in plan/design Markdown documents."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Iterable


PROGRESS_HEADINGS = {"進捗", "Progress"}
HISTORY_HEADINGS = {"変更履歴", "Change History"}
CHECKBOX_RE = re.compile(r"^\s*-\s+\[([^\]]*)\]\s*(.*)$")
LEVEL_TWO_HEADING_RE = re.compile(r"^##\s+\S")
VERSION_LINE_RE = re.compile(r"^\s*(?:バージョン|Version)\s*:\s*(\d+\.\d+)\s*$")
VERSION_RE = re.compile(r"^\d+\.\d+$")
TABLE_SEPARATOR_RE = re.compile(r"^:?-{3,}:?$")


def _section(lines: list[str], headings: set[str]) -> tuple[int, int] | None:
    start: int | None = None
    for index, line in enumerate(lines):
        if not line.startswith("## "):
            continue
        heading = line[3:].strip()
        if heading in headings:
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


def _progress_section(lines: list[str]) -> tuple[int, int] | None:
    return _section(lines, PROGRESS_HEADINGS)


def _header_version(lines: list[str]) -> str | None:
    """Return the version in the document header, before the first level-2 heading."""

    for line in lines:
        if LEVEL_TWO_HEADING_RE.match(line):
            break
        match = VERSION_LINE_RE.match(line)
        if match:
            return match.group(1)
    return None


def _table_cells(line: str) -> list[str] | None:
    stripped = line.strip()
    if not (stripped.startswith("|") and stripped.endswith("|")):
        return None
    return [cell.strip() for cell in stripped[1:-1].split("|")]


def _is_table_separator(cells: list[str]) -> bool:
    return bool(cells) and all(TABLE_SEPARATOR_RE.fullmatch(cell) for cell in cells)


def _version_history_errors(lines: list[str], *, source: str) -> list[str]:
    errors: list[str] = []
    header_version = _header_version(lines)
    if header_version is None:
        errors.append(
            f"{source}: ヘッダに バージョン: MAJOR.MINOR または Version: MAJOR.MINOR がありません"
        )

    history = _section(lines, HISTORY_HEADINGS)
    if history is None:
        errors.append(f"{source}: ## 変更履歴 または ## Change History セクションがありません")
        return errors

    progress = _progress_section(lines)
    if progress is not None and history[0] > progress[0]:
        errors.append(f"{source}: 変更履歴セクションは進捗セクションの前に置いてください")

    start, end = history
    rows: list[tuple[int, list[str]]] = []
    for index in range(start, end):
        cells = _table_cells(lines[index])
        if cells is not None and not _is_table_separator(cells):
            rows.append((index, cells))

    if len(rows) < 2:
        errors.append(f"{source}: 変更履歴にヘッダと1件以上の履歴行が必要です")
        return errors

    header_line, header = rows[0]
    version_names = {"バージョン", "Version"}
    date_names = {"日付", "Date"}
    change_names = {"変更内容", "Change", "Changes", "Description"}
    try:
        version_index = next(index for index, name in enumerate(header) if name in version_names)
    except StopIteration:
        errors.append(f"{source}:{header_line + 1}: 変更履歴のバージョン列がありません")
        return errors

    missing_columns = []
    if not any(name in date_names for name in header):
        missing_columns.append("日付/Date")
    if not any(name in change_names for name in header):
        missing_columns.append("変更内容/Change")
    if missing_columns:
        errors.append(
            f"{source}:{header_line + 1}: 変更履歴の列が不足しています: {', '.join(missing_columns)}"
        )

    history_versions: list[tuple[int, str]] = []
    for line_number, row in rows[1:]:
        if version_index >= len(row):
            errors.append(f"{source}:{line_number + 1}: 変更履歴のバージョン列が空です")
            continue
        version = row[version_index]
        if not VERSION_RE.fullmatch(version):
            errors.append(
                f"{source}:{line_number + 1}: 変更履歴のバージョンは MAJOR.MINOR 形式にしてください"
            )
        else:
            history_versions.append((line_number, version))

    if header_version is not None and history_versions:
        last_line, last_version = history_versions[-1]
        if last_version != header_version:
            errors.append(
                f"{source}:{last_line + 1}: ヘッダのバージョン {header_version} と"
                f"変更履歴の最終バージョン {last_version} が一致しません"
            )
    return errors


def check_text(text: str, *, source: str = "<document>") -> list[str]:
    """Return human-readable errors for one Markdown document."""

    lines = text.splitlines()
    errors = _version_history_errors(lines, source=source)
    section = _progress_section(lines)
    if section is None:
        errors.append(f"{source}: ## 進捗 または ## Progress セクションがありません")
        return errors

    start, end = section
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
