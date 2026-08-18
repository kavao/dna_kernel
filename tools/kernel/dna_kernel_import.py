#!/usr/bin/env python3
"""Read-only preflight, inventory, dry-run planning, and verification.

This tool is intentionally conservative: it never writes to the target
repository.  A caller can use its deterministic output as the input to an
approved, separately controlled import operation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Iterable


GENERATED_ROOTS = {".agents", ".claude", ".codex", ".cursor", ".grok", ".kilo"}
GENERATED_FILES = {"AGENTS.md", "CLAUDE.md"}
SKIP_DIRS = {".git", ".tools", "_backup", "_old", "__pycache__", ".venv"}
FRONTMATTER_LIST_RE = re.compile(r"^([A-Za-z0-9_-]+):\s*(\[.*\])\s*$")
FRONTMATTER_SCALAR_RE = re.compile(r"^([A-Za-z0-9_-]+):\s*(.+?)\s*$")
TARGETS_RE = re.compile(r'"targets"\s*:\s*\[(.*?)\]', re.DOTALL)


def resolve_target_root(value: str | Path) -> Path:
    root = Path(value).expanduser().resolve()
    if not root.is_dir():
        raise ValueError(f"対象ルートがディレクトリではありません: {root}")
    return root


def _git_info(root: Path) -> dict[str, object]:
    git_marker = root / ".git"
    result: dict[str, object] = {
        "marker_exists": git_marker.exists(),
        "available": shutil.which("git") is not None,
        "boundary": False,
        "clean": None,
        "status": None,
    }
    if not result["available"] or not git_marker.exists():
        return result

    boundary = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        check=False,
    )
    if boundary.returncode == 0:
        try:
            result["boundary"] = Path(boundary.stdout.strip()).resolve() == root
        except OSError:
            result["boundary"] = False

    status = subprocess.run(
        ["git", "-C", str(root), "status", "--porcelain", "--untracked-files=no"],
        capture_output=True,
        text=True,
        check=False,
    )
    if status.returncode == 0:
        result["status"] = status.stdout.splitlines()
        result["clean"] = not status.stdout.strip()
    return result


def preflight(root_value: str | Path) -> dict[str, object]:
    """Inspect a target root without changing it."""

    root = resolve_target_root(root_value)
    git = _git_info(root)
    paths = {
        "README.md": (root / "README.md").is_file(),
        "docs": (root / "docs").is_dir(),
        "tools": (root / "tools").is_dir(),
        ".rulesync": (root / ".rulesync").is_dir(),
        "rulesync.jsonc": (root / "rulesync.jsonc").is_file(),
        ".gitignore": (root / ".gitignore").is_file(),
        "AGENTS.md": (root / "AGENTS.md").is_file(),
        "CLAUDE.md": (root / "CLAUDE.md").is_file(),
    }
    result = {
        "root": str(root),
        "ok": bool(git["marker_exists"] and git["boundary"]),
        "git": git,
        "paths": paths,
        "environment": {
            "python": sys.version.split()[0],
            "uv": shutil.which("uv") is not None,
            "rulesync_wrapper": (root / "tools" / "rulesync.py").is_file(),
        },
    }
    return result


def _iter_files(root: Path) -> Iterable[Path]:
    for path in sorted(root.rglob("*"), key=lambda item: item.as_posix()):
        if not path.is_file():
            continue
        relative_parts = path.relative_to(root).parts
        if any(part in SKIP_DIRS for part in relative_parts):
            continue
        yield path


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _frontmatter(path: Path) -> dict[str, object]:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    values: dict[str, object] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            break
        list_match = FRONTMATTER_LIST_RE.match(line)
        if list_match:
            try:
                values[list_match.group(1)] = json.loads(list_match.group(2))
            except json.JSONDecodeError:
                values[list_match.group(1)] = list_match.group(2)
            continue
        scalar_match = FRONTMATTER_SCALAR_RE.match(line)
        if not scalar_match:
            continue
        key, value = scalar_match.groups()
        if value.lower() in {"true", "false"}:
            values[key] = value.lower() == "true"
        else:
            values[key] = value.strip('"')
    return values


def _category(root: Path, path: Path) -> str:
    relative = path.relative_to(root)
    parts = relative.parts
    if relative.as_posix() == "rulesync.jsonc":
        return "config"
    if len(parts) >= 3 and parts[:2] == (".rulesync", "rules") and path.suffix == ".md":
        return "canonical-rule"
    if len(parts) >= 4 and parts[:2] == (".rulesync", "skills") and path.name == "SKILL.md":
        return "canonical-skill"
    if parts[0] in GENERATED_ROOTS or path.name in GENERATED_FILES:
        return "generated"
    if parts[0] == "docs" or path.name in {"README.md", "manifest.md"}:
        return "docs"
    if parts[0] == "tools":
        return "tool"
    return "other"


def _index_tokens(index_text: str) -> set[str]:
    tokens = set(re.findall(r"[A-Za-z0-9_.-]+", index_text))
    return tokens


def _is_indexed(relative: Path, tokens: set[str]) -> bool:
    if relative.parts[:2] == (".rulesync", "rules"):
        return relative.name in tokens or relative.stem in tokens
    if relative.parts[:2] == (".rulesync", "skills") and len(relative.parts) >= 3:
        return relative.parts[2] in tokens
    return False


def _configured_targets(root: Path) -> list[str]:
    path = root / "rulesync.jsonc"
    if not path.is_file():
        return []
    match = TARGETS_RE.search(path.read_text(encoding="utf-8"))
    if not match:
        return []
    return re.findall(r'"([^"\\]+)"', match.group(1))


def inventory(root_value: str | Path) -> dict[str, object]:
    """List canonical sources, generated outputs, and index coverage."""

    root = resolve_target_root(root_value)
    index_path = root / ".rulesync" / "rules" / "agents.md"
    index_text = index_path.read_text(encoding="utf-8") if index_path.is_file() else ""
    tokens = _index_tokens(index_text)
    entries: list[dict[str, object]] = []
    for path in _iter_files(root):
        relative = path.relative_to(root)
        category = _category(root, path)
        entry: dict[str, object] = {
            "path": relative.as_posix(),
            "category": category,
            "bytes": path.stat().st_size,
            "sha256": _hash(path),
        }
        if category in {"canonical-rule", "canonical-skill"}:
            entry["indexed"] = _is_indexed(relative, tokens)
            entry["frontmatter"] = _frontmatter(path)
        entries.append(entry)

    canonical = [
        entry for entry in entries if entry["category"] in {"canonical-rule", "canonical-skill"}
    ]
    indexed = [entry for entry in canonical if entry.get("indexed")]
    root_rules = [
        entry
        for entry in entries
        if entry["category"] == "canonical-rule"
        and isinstance(entry.get("frontmatter"), dict)
        and entry["frontmatter"].get("root") is True
    ]
    return {
        "root": str(root),
        "targets": _configured_targets(root),
        "index": {
            "path": ".rulesync/rules/agents.md",
            "exists": index_path.is_file(),
            "indexed_count": len(indexed),
            "canonical_count": len(canonical),
            "coverage": len(indexed) / len(canonical) if canonical else 1.0,
        },
        "root_rules": [entry["path"] for entry in root_rules],
        "entries": entries,
        "summary": {
            category: sum(1 for entry in entries if entry["category"] == category)
            for category in (
                "canonical-rule",
                "canonical-skill",
                "generated",
                "docs",
                "tool",
                "config",
                "other",
            )
        },
    }


def build_import_plan(root_value: str | Path, profile: str) -> dict[str, object]:
    """Create a deterministic, non-writing import plan."""

    if profile not in {"rule-only", "governance", "full"}:
        raise ValueError(f"未知の導入プロファイルです: {profile}")
    root = resolve_target_root(root_value)
    current = inventory(root)
    actions = [
        {
            "action": "preflight",
            "path": str(root),
            "writes": False,
            "approval_required": False,
        },
        {
            "action": "inventory-existing-rules",
            "path": ".rulesync/",
            "writes": False,
            "approval_required": False,
        },
        {
            "action": "design-agents-index",
            "path": ".rulesync/rules/agents.md",
            "writes": True,
            "approval_required": True,
        },
        {
            "action": "dry-run-target-separation",
            "path": "rulesync.jsonc",
            "writes": False,
            "approval_required": True,
        },
        {
            "action": "backup-and-import-after-approval",
            "path": ".rulesync/ and tools/",
            "writes": True,
            "approval_required": True,
        },
        {
            "action": "generate-and-verify",
            "path": "generated targets",
            "writes": True,
            "approval_required": True,
        },
    ]
    if profile in {"governance", "full"}:
        actions.append(
            {
                "action": "enable-audit-and-contract-checks",
                "path": "tools/kernel/ and tests/",
                "writes": True,
                "approval_required": True,
            }
        )
    if profile == "full":
        actions.append(
            {
                "action": "enable-onboarding-and-locale-support",
                "path": ".rulesync/skills/",
                "writes": True,
                "approval_required": True,
            }
        )
    return {
        "root": str(root),
        "profile": profile,
        "dry_run": True,
        "writes_performed": False,
        "approval_required": True,
        "existing_inventory_summary": current["summary"],
        "actions": actions,
    }


def verify(root_value: str | Path) -> tuple[int, dict[str, object]]:
    """Verify index coverage and per-target root ownership."""

    data = inventory(root_value)
    errors: list[str] = []
    index = data["index"]
    assert isinstance(index, dict)
    if not index["exists"]:
        errors.append(".rulesync/rules/agents.md がありません")
    if index["canonical_count"] and index["coverage"] != 1.0:
        errors.append(
            f"インデックス網羅率が100%ではありません: {index['indexed_count']}/{index['canonical_count']}"
        )

    entries = data["entries"]
    assert isinstance(entries, list)
    target_roots: dict[str, list[str]] = {}
    for entry in entries:
        if entry["category"] != "canonical-rule":
            continue
        frontmatter = entry.get("frontmatter")
        if not isinstance(frontmatter, dict):
            errors.append(f"ルールfrontmatterがありません: {entry['path']}")
            continue
        targets = frontmatter.get("targets", [])
        if not isinstance(targets, list):
            errors.append(f"ルールのtargetsが配列ではありません: {entry['path']}")
            continue
        if not targets or "*" in targets:
            errors.append(f"ルールのtargetsは明示許可リストにしてください: {entry['path']}")
        if frontmatter.get("root") is not True:
            continue
        for target in targets:
            target_roots.setdefault(str(target), []).append(str(entry["path"]))
    for target, paths in sorted(target_roots.items()):
        if len(paths) != 1:
            errors.append(f"target {target} のroot所有者が一意ではありません: {paths}")

    data["target_root_owners"] = target_roots
    data["errors"] = errors
    data["ok"] = not errors
    return (0 if not errors else 1), data


def _print(data: dict[str, object], output_format: str) -> None:
    if output_format == "json":
        print(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True))
        return
    print(f"root: {data.get('root')}")
    if "ok" in data:
        print(f"ok: {data['ok']}")
    if "errors" in data:
        for error in data["errors"]:
            print(f"ERROR: {error}")
    if "summary" in data:
        print(f"summary: {json.dumps(data['summary'], ensure_ascii=False, sort_keys=True)}")
    if "actions" in data:
        for action in data["actions"]:
            print(f"- {action['action']}: {action['path']}")
    if "paths" in data:
        print(f"paths: {json.dumps(data['paths'], ensure_ascii=False, sort_keys=True)}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="既存リポジトリへのdna_kernel導入を読み取り専用で検査・計画します。"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("preflight", "inventory", "verify"):
        subparser = subparsers.add_parser(command)
        subparser.add_argument("root", type=Path)
        subparser.add_argument("--format", choices=("json", "table"), default="table")
    plan_parser = subparsers.add_parser("plan")
    plan_parser.add_argument("root", type=Path)
    plan_parser.add_argument("--profile", choices=("rule-only", "governance", "full"), default="governance")
    plan_parser.add_argument("--dry-run", action="store_true", help="書き込みなしの計画として出力（常に有効）")
    plan_parser.add_argument("--format", choices=("json", "table"), default="table")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "preflight":
            data = preflight(args.root)
            _print(data, args.format)
            return 0 if data["ok"] else 1
        if args.command == "inventory":
            _print(inventory(args.root), args.format)
            return 0
        if args.command == "plan":
            _print(build_import_plan(args.root, args.profile), args.format)
            return 0
        code, data = verify(args.root)
        _print(data, args.format)
        return code
    except (OSError, UnicodeError, ValueError, subprocess.SubprocessError) as exc:
        print(f"import tool error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
