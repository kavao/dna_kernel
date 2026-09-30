"""Download and verify the repository's fixed Rulesync binary."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import stat
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config" / "rulesync_toolchain.json"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class RulesyncToolchainError(RuntimeError):
    """Raised when the fixed Rulesync toolchain cannot be used safely."""


def load_config(config_path: Path = CONFIG_PATH) -> dict[str, Any]:
    """Load and validate the fixed toolchain configuration."""

    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RulesyncToolchainError(
            f"Rulesync toolchain configuration could not be read: {config_path}"
        ) from exc

    if not isinstance(config, dict):
        raise RulesyncToolchainError("Rulesync toolchain configuration must be an object")
    version = config.get("version")
    release_base_url = config.get("release_base_url")
    platforms = config.get("platforms")
    if not isinstance(version, str) or not version:
        raise RulesyncToolchainError("Rulesync toolchain version is missing")
    if not isinstance(release_base_url, str) or not release_base_url.startswith("https://"):
        raise RulesyncToolchainError("Rulesync release_base_url must use HTTPS")
    if not isinstance(platforms, dict) or not platforms:
        raise RulesyncToolchainError("Rulesync platform settings are missing")

    for key, asset in platforms.items():
        if not isinstance(key, str) or not isinstance(asset, dict):
            raise RulesyncToolchainError("Rulesync platform settings are invalid")
        for field in ("asset", "cache_path", "sha256"):
            if not isinstance(asset.get(field), str) or not asset[field]:
                raise RulesyncToolchainError(f"Rulesync platform setting is missing: {key}.{field}")
        if not SHA256_RE.fullmatch(asset["sha256"]):
            raise RulesyncToolchainError(f"Rulesync SHA-256 is invalid: {key}")

    return config


def normalize_platform(system: str | None = None, machine: str | None = None) -> str:
    """Return the release asset key for an OS and CPU combination."""

    system_name = (system or platform.system()).strip().lower()
    machine_name = (machine or platform.machine()).strip().lower()
    os_key = {
        "windows": "windows",
        "darwin": "darwin",
        "macos": "darwin",
        "linux": "linux",
    }.get(system_name)
    architecture = {
        "amd64": "x64",
        "x86_64": "x64",
        "x64": "x64",
        "aarch64": "arm64",
        "arm64": "arm64",
    }.get(machine_name)
    if os_key is None or architecture is None:
        detected = f"{system or platform.system()} / {machine or platform.machine()}"
        raise RulesyncToolchainError(
            f"Unsupported Rulesync platform: {detected}. "
            "Supported platforms are Windows x64, macOS x64/arm64, and Linux x64/arm64."
        )
    if os_key == "windows" and architecture == "arm64":
        raise RulesyncToolchainError(
            "Unsupported Rulesync platform: Windows / ARM64. "
            "The fixed Rulesync 15.0.1 assets support Windows x64 only."
        )
    return f"{os_key}-{architecture}"


def platform_asset(config: dict[str, Any], platform_key: str) -> dict[str, str]:
    """Return a validated platform asset from a loaded configuration."""

    platforms = config["platforms"]
    asset = platforms.get(platform_key)
    if not isinstance(asset, dict):
        raise RulesyncToolchainError(f"No Rulesync asset is configured for {platform_key}")
    return asset


def binary_path(root: Path, asset: dict[str, str]) -> Path:
    """Resolve a configured cache path below the repository root."""

    relative_path = Path(asset["cache_path"])
    if relative_path.is_absolute() or ".." in relative_path.parts:
        raise RulesyncToolchainError("Rulesync cache_path must stay below the repository root")
    return root / relative_path


def sha256(path: Path) -> str:
    """Calculate a file's SHA-256 digest."""

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def verify_version(binary: Path, expected: str, root: Path = ROOT) -> None:
    """Require the binary to report exactly the configured Rulesync version."""

    result = subprocess.run(
        [str(binary), "--version"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    actual = result.stdout.strip()
    if result.returncode or actual != expected:
        detail = actual or result.stderr.strip() or "no version output"
        raise RulesyncToolchainError(
            f"Rulesync version verification failed: expected {expected}, got {detail!r}"
        )


def ensure_executable(binary: Path, platform_key: str) -> None:
    """Set the executable bit for native Unix binaries."""

    if not platform_key.startswith("windows-"):
        binary.chmod(binary.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def download_and_verify(
    *,
    binary: Path,
    url: str,
    expected_hash: str,
    platform_key: str,
) -> None:
    """Download one asset to a temporary file and atomically install it."""

    binary.parent.mkdir(parents=True, exist_ok=True)
    temporary_fd, temporary_name = tempfile.mkstemp(
        prefix="rulesync-", suffix=".download", dir=binary.parent
    )
    os.close(temporary_fd)
    temporary = Path(temporary_name)
    try:
        request = urllib.request.Request(
            url,
            headers={"User-Agent": "dna-kernel-rulesync-installer"},
        )
        with urllib.request.urlopen(request, timeout=60) as response, temporary.open("wb") as handle:
            while block := response.read(1024 * 1024):
                handle.write(block)
        actual_hash = sha256(temporary)
        if actual_hash != expected_hash:
            raise RulesyncToolchainError(
                f"Rulesync SHA-256 mismatch: expected {expected_hash}, got {actual_hash}"
            )
        ensure_executable(temporary, platform_key)
        os.replace(temporary, binary)
    finally:
        temporary.unlink(missing_ok=True)


def install(
    *,
    root: Path = ROOT,
    config_path: Path = CONFIG_PATH,
    platform_key: str | None = None,
    force: bool = False,
) -> Path:
    """Install or validate the fixed Rulesync binary and return its path."""

    config = load_config(config_path)
    selected_platform = platform_key or normalize_platform()
    asset = platform_asset(config, selected_platform)
    binary = binary_path(root, asset)
    expected_hash = asset["sha256"].lower()

    if binary.is_file() and not force:
        if sha256(binary) == expected_hash:
            ensure_executable(binary, selected_platform)
            verify_version(binary, config["version"], root)
            print(f"Rulesync {config['version']} is ready: {binary}")
            return binary
        print("Cached Rulesync binary has an unexpected SHA-256; downloading a verified replacement.")

    url = f"{config['release_base_url'].rstrip('/')}/{asset['asset']}"
    print(f"Downloading Rulesync {config['version']} ({selected_platform})...")
    download_and_verify(
        binary=binary,
        url=url,
        expected_hash=expected_hash,
        platform_key=selected_platform,
    )
    verify_version(binary, config["version"], root)
    print(f"Rulesync {config['version']} installed and verified: {binary}")
    return binary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--force",
        action="store_true",
        help="download again even when the cached binary is valid",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        install(force=args.force)
    except (OSError, RulesyncToolchainError) as exc:
        print(f"Rulesync installation failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
