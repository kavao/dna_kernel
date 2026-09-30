"""Run the repository's fixed, verified Rulesync binary."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from install_rulesync import (
    CONFIG_PATH,
    ROOT,
    RulesyncToolchainError,
    binary_path,
    load_config,
    normalize_platform,
    platform_asset,
    sha256,
    ensure_executable,
    verify_version,
)


def main(
    argv: list[str] | None = None,
    *,
    root: Path = ROOT,
    config_path: Path = CONFIG_PATH,
    platform_key: str | None = None,
) -> int:
    """Run Rulesync with the supplied arguments and return its exit code."""

    arguments = sys.argv[1:] if argv is None else argv
    try:
        config = load_config(config_path)
        selected_platform = platform_key or normalize_platform()
        asset = platform_asset(config, selected_platform)
        binary = binary_path(root, asset)
        if not binary.is_file():
            print(
                "Rulesync is not installed. Run: python tools/install_rulesync.py",
                file=sys.stderr,
            )
            return 2
        if sha256(binary) != asset["sha256"].lower():
            print(
                "Rulesync cache failed SHA-256 verification. Run: "
                "python tools/install_rulesync.py --force",
                file=sys.stderr,
            )
            return 2
        ensure_executable(binary, selected_platform)
        verify_version(binary, config["version"], root)
    except (OSError, RulesyncToolchainError) as exc:
        print(f"Rulesync cannot be run: {exc}", file=sys.stderr)
        return 2

    return subprocess.run([str(binary), *arguments], cwd=root, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
