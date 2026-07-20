from __future__ import annotations

import importlib.util
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime
from io import StringIO
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools" / "kernel" / "workspace_audit_log.py"
SPEC = importlib.util.spec_from_file_location("workspace_audit_log", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
workspace_audit_log = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(workspace_audit_log)


class WorkspaceAuditLogTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.stamp = datetime(2026, 6, 15, 10, 30)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def append(
        self,
        message: str,
        *,
        target: workspace_audit_log.MonthlyTarget = workspace_audit_log.MonthlyTarget.AUDIT,
        stamp: datetime | None = None,
        dry_run: bool = False,
    ) -> dict[str, str | bool]:
        effective_stamp = stamp or self.stamp
        return workspace_audit_log.append_entry(
            message,
            target=target,
            file_year=effective_stamp.year,
            file_month=effective_stamp.month,
            stamp=effective_stamp,
            root=self.root,
            dry_run=dry_run,
        )

    def test_append_creates_month_file_with_header(self) -> None:
        result = self.append("ルールを追加")

        path = Path(str(result["path"]))
        self.assertEqual(
            path,
            (self.root / "_workingspace" / "log" / "202606.md").resolve(),
        )
        self.assertEqual(
            path.read_text(encoding="utf-8"),
            "# 査証ログ 2026年6月\n\n- 2026-06-15 10:30: ルールを追加\n",
        )
        self.assertTrue(result["written"])

    def test_append_preserves_content_without_final_newline(self) -> None:
        path = self.root / "_workingspace" / "log" / "202606.md"
        path.parent.mkdir(parents=True)
        path.write_text(
            "# 査証ログ 2026年6月\n\n- 2026-06-15 09:00: 最初の記録",
            encoding="utf-8",
        )

        self.append("次の記録", stamp=datetime(2026, 6, 15, 11, 45))

        self.assertTrue(
            path.read_text(encoding="utf-8").endswith(
                "最初の記録\n- 2026-06-15 11:45: 次の記録\n"
            )
        )

    def test_dry_run_does_not_create_file(self) -> None:
        result = self.append("確認だけ", dry_run=True)

        self.assertFalse(Path(str(result["path"])).exists())
        self.assertFalse(result["written"])
        self.assertIn("- 2026-06-15 10:30: 確認だけ", str(result["line"]))

    def test_multiline_message_is_normalized(self) -> None:
        result = self.append("1行目\n\n  2行目", dry_run=True)

        self.assertIn("1行目 2行目", str(result["line"]))

    def test_diary_append_uses_diary_header(self) -> None:
        result = self.append(
            "運用知見",
            target=workspace_audit_log.MonthlyTarget.DIARY,
        )

        path = Path(str(result["path"]))
        self.assertEqual(
            path,
            (self.root / "_workingspace" / "diary" / "202606.md").resolve(),
        )
        self.assertTrue(
            path.read_text(encoding="utf-8").startswith(
                "# 日記（横断ナレッジ） 2026年6月\n\n"
            )
        )

    def test_verify_accepts_valid_log(self) -> None:
        self.append("形式確認")

        with redirect_stdout(StringIO()):
            result = workspace_audit_log._verify_monthly_files(
                workspace_audit_log.log_dir(self.root),
                first_line_prefix="# 査証ログ ",
                kind_label="log",
                strict=True,
            )

        self.assertEqual(result, 0)

    def test_verify_rejects_invalid_entry(self) -> None:
        log_dir = workspace_audit_log.log_dir(self.root)
        log_dir.mkdir(parents=True)
        (log_dir / "202606.md").write_text(
            "# 査証ログ 2026年6月\n\n不正な行\n",
            encoding="utf-8",
        )
        errors = StringIO()

        with redirect_stderr(errors):
            result = workspace_audit_log._verify_monthly_files(
                log_dir,
                first_line_prefix="# 査証ログ ",
                kind_label="log",
                strict=True,
            )

        self.assertEqual(result, 1)
        self.assertIn("箇条書き", errors.getvalue())

    def test_repo_root_raises_outside_repository(self) -> None:
        with self.assertRaisesRegex(FileNotFoundError, "ルートを検出できません"):
            workspace_audit_log.repo_root(self.root)


if __name__ == "__main__":
    unittest.main()
