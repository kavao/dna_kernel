from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from subprocess import CompletedProcess
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
sys.path.insert(0, str(TOOLS))

import install_rulesync as installer  # noqa: E402
import rulesync as rulesync_runner  # noqa: E402


class FakeResponse:
    def __init__(self, payload: bytes) -> None:
        self._payload = payload
        self._read = False

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def read(self, _size: int = -1) -> bytes:
        if self._read:
            return b""
        self._read = True
        return self._payload


class RulesyncToolchainTests(unittest.TestCase):
    def test_normalizes_supported_platforms(self) -> None:
        cases = {
            ("Windows", "AMD64"): "windows-x64",
            ("Darwin", "x86_64"): "darwin-x64",
            ("Darwin", "arm64"): "darwin-arm64",
            ("Linux", "x86_64"): "linux-x64",
            ("Linux", "aarch64"): "linux-arm64",
        }
        for (system, machine), expected in cases.items():
            with self.subTest(system=system, machine=machine):
                self.assertEqual(installer.normalize_platform(system, machine), expected)

    def test_rejects_unsupported_platform(self) -> None:
        with self.assertRaises(installer.RulesyncToolchainError):
            installer.normalize_platform("Windows", "ARM64")

    def test_current_configuration_contains_five_fixed_assets(self) -> None:
        config = installer.load_config()
        self.assertEqual(config["version"], "15.0.1")
        self.assertEqual(
            set(config["platforms"]),
            {
                "windows-x64",
                "darwin-x64",
                "darwin-arm64",
                "linux-x64",
                "linux-arm64",
            },
        )
        for asset in config["platforms"].values():
            self.assertEqual(len(asset["sha256"]), 64)
            self.assertTrue(asset["cache_path"].startswith(".tools/rulesync/15.0.1/"))

    def test_install_downloads_verifies_and_reuses_cache(self) -> None:
        payload = b"rulesync-test-binary"
        config = self._test_config(payload)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config_path = root / "rulesync_toolchain.json"
            config_path.write_text(json.dumps(config), encoding="utf-8")
            completed = CompletedProcess([], 0, stdout="15.0.1\n", stderr="")
            with (
                patch.object(
                    installer.urllib.request,
                    "urlopen",
                    side_effect=lambda *_args, **_kwargs: FakeResponse(payload),
                ) as urlopen,
                patch.object(installer.subprocess, "run", return_value=completed),
            ):
                binary = installer.install(
                    root=root,
                    config_path=config_path,
                    platform_key="linux-x64",
                )
                self.assertEqual(binary.read_bytes(), payload)
                installer.install(
                    root=root,
                    config_path=config_path,
                    platform_key="linux-x64",
                )
            self.assertEqual(urlopen.call_count, 1)

    def test_install_force_redownloads_valid_cache(self) -> None:
        payload = b"rulesync-test-binary"
        config = self._test_config(payload)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config_path = root / "rulesync_toolchain.json"
            config_path.write_text(json.dumps(config), encoding="utf-8")
            completed = CompletedProcess([], 0, stdout="15.0.1\n", stderr="")
            with (
                patch.object(
                    installer.urllib.request,
                    "urlopen",
                    side_effect=lambda *_args, **_kwargs: FakeResponse(payload),
                ) as urlopen,
                patch.object(installer.subprocess, "run", return_value=completed),
            ):
                installer.install(root=root, config_path=config_path, platform_key="linux-x64")
                installer.install(
                    root=root,
                    config_path=config_path,
                    platform_key="linux-x64",
                    force=True,
                )
            self.assertEqual(urlopen.call_count, 2)

    def test_install_rejects_hash_mismatch(self) -> None:
        payload = b"rulesync-test-binary"
        config = self._test_config(payload)
        config["platforms"]["linux-x64"]["sha256"] = "0" * 64
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config_path = root / "rulesync_toolchain.json"
            config_path.write_text(json.dumps(config), encoding="utf-8")
            with patch.object(
                installer.urllib.request,
                "urlopen",
                return_value=FakeResponse(payload),
            ):
                with self.assertRaises(installer.RulesyncToolchainError):
                    installer.install(
                        root=root,
                        config_path=config_path,
                        platform_key="linux-x64",
                    )
            self.assertFalse((root / ".tools/rulesync/15.0.1/linux-x64/rulesync").exists())

    def test_runner_reports_missing_installation(self) -> None:
        config = self._test_config(b"unused")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config_path = root / "rulesync_toolchain.json"
            config_path.write_text(json.dumps(config), encoding="utf-8")
            result = rulesync_runner.main(
                [], root=root, config_path=config_path, platform_key="linux-x64"
            )
        self.assertEqual(result, 2)

    def test_runner_transfers_arguments_and_exit_code(self) -> None:
        payload = b"rulesync-test-binary"
        config = self._test_config(payload)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config_path = root / "rulesync_toolchain.json"
            config_path.write_text(json.dumps(config), encoding="utf-8")
            binary = root / ".tools/rulesync/15.0.1/linux-x64/rulesync"
            binary.parent.mkdir(parents=True)
            binary.write_bytes(payload)
            with (
                patch.object(rulesync_runner, "verify_version"),
                patch.object(
                    rulesync_runner.subprocess,
                    "run",
                    return_value=CompletedProcess([], 7),
                ) as run,
            ):
                result = rulesync_runner.main(
                    ["generate", "--dry-run"],
                    root=root,
                    config_path=config_path,
                    platform_key="linux-x64",
                )
        self.assertEqual(result, 7)
        run.assert_called_once_with(
            [str(binary), "generate", "--dry-run"], cwd=root, check=False
        )

    @staticmethod
    def _test_config(payload: bytes) -> dict[str, object]:
        return {
            "version": "15.0.1",
            "release_base_url": "https://example.invalid/rulesync",
            "platforms": {
                "linux-x64": {
                    "asset": "rulesync-linux-x64",
                    "sha256": hashlib.sha256(payload).hexdigest(),
                    "cache_path": ".tools/rulesync/15.0.1/linux-x64/rulesync",
                }
            },
        }


if __name__ == "__main__":
    unittest.main()
