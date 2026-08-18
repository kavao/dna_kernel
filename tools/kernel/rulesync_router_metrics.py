#!/usr/bin/env python3
"""Measure Rulesync sources and generated output with the Python stdlib only.

The command deliberately measures bytes, text characters, logical lines, and
SHA-256 in one place so that shell-specific tools do not become part of the
router contract.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Iterable


def _relative(path: Path, base: Path | None) -> str:
    resolved = path.resolve()
    if base is None:
        return str(resolved)
    try:
        return resolved.relative_to(base.resolve()).as_posix()
    except ValueError:
        return str(resolved)


def _files(paths: Iterable[Path]) -> list[Path]:
    found: set[Path] = set()
    for path in paths:
        resolved = path.resolve()
        if resolved.is_file():
            found.add(resolved)
        elif resolved.is_dir():
            found.update(candidate for candidate in resolved.rglob("*") if candidate.is_file())
        else:
            raise FileNotFoundError(f"測定対象が存在しません: {path}")
    return sorted(found, key=lambda item: item.as_posix())


def measure_file(path: Path, *, base: Path | None = None) -> dict[str, int | str]:
    """Return deterministic metrics for one UTF-8 text file."""

    resolved = path.resolve()
    payload = resolved.read_bytes()
    text = payload.decode("utf-8")
    return {
        "path": _relative(resolved, base),
        "lines": len(text.splitlines()),
        "chars": len(text),
        "bytes": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
    }


def summarize(paths: Iterable[Path], *, base: Path | None = None) -> dict[str, object]:
    """Measure files and return file-level metrics plus totals."""

    metrics = [measure_file(path, base=base) for path in _files(paths)]
    totals = {
        key: sum(int(item[key]) for item in metrics)
        for key in ("lines", "chars", "bytes")
    }
    totals["files"] = len(metrics)
    return {"files": metrics, "totals": totals}


def compare(current: dict[str, object], baseline: dict[str, object]) -> dict[str, int | float]:
    """Return numeric current-minus-baseline deltas."""

    current_totals = current.get("totals", {})
    baseline_totals = baseline.get("totals", {})
    if not isinstance(current_totals, dict) or not isinstance(baseline_totals, dict):
        raise ValueError("metrics JSON の totals が不正です")
    result: dict[str, int | float] = {}
    for key in ("files", "lines", "chars", "bytes"):
        current_value = int(current_totals.get(key, 0))
        baseline_value = int(baseline_totals.get(key, 0))
        result[f"{key}_delta"] = current_value - baseline_value
        result[f"{key}_change_ratio"] = (
            (current_value - baseline_value) / baseline_value if baseline_value else 0.0
        )
    return result


def build_report(
    paths: Iterable[Path],
    *,
    label: str | None = None,
    target: str | None = None,
    base: Path | None = None,
    baseline: dict[str, object] | None = None,
) -> dict[str, object]:
    report = summarize(paths, base=base)
    if label:
        report["label"] = label
    if target:
        report["target"] = target
    if base is not None:
        report["base"] = str(base.resolve())
    if baseline is not None:
        report["delta"] = compare(report, baseline)
    return report


def _print_table(report: dict[str, object]) -> None:
    if report.get("label"):
        print(f"label: {report['label']}")
    if report.get("target"):
        print(f"target: {report['target']}")
    totals = report["totals"]
    assert isinstance(totals, dict)
    print(
        "totals: "
        f"files={totals['files']} lines={totals['lines']} "
        f"chars={totals['chars']} bytes={totals['bytes']}"
    )
    for item in report["files"]:
        assert isinstance(item, dict)
        print(
            f"{item['path']}: lines={item['lines']} chars={item['chars']} "
            f"bytes={item['bytes']} sha256={item['sha256']}"
        )
    if "delta" in report:
        print(f"delta: {json.dumps(report['delta'], ensure_ascii=False, sort_keys=True)}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Rulesyncの正本・生成物をPython標準ライブラリだけで定量測定します。"
    )
    parser.add_argument("paths", nargs="+", type=Path, help="測定するファイルまたはディレクトリ")
    parser.add_argument("--base", type=Path, help="相対パス表示の基準ディレクトリ")
    parser.add_argument("--label", help="測定結果のラベル")
    parser.add_argument("--target", help="Rulesync target名")
    parser.add_argument("--baseline", type=Path, help="比較するmetrics JSON")
    parser.add_argument("--format", choices=("json", "table"), default="table")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        baseline = None
        if args.baseline:
            baseline = json.loads(args.baseline.read_text(encoding="utf-8"))
            if not isinstance(baseline, dict):
                raise ValueError("baseline JSONはオブジェクトで指定してください")
        report = build_report(
            args.paths,
            label=args.label,
            target=args.target,
            base=args.base,
            baseline=baseline,
        )
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as exc:
        print(f"metrics error: {exc}", file=sys.stderr)
        return 2

    if args.format == "json":
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        _print_table(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
