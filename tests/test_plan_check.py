from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools" / "kernel" / "plan_check.py"
SPEC = importlib.util.spec_from_file_location("plan_check", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
plan_check = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(plan_check)


def japanese_document(body: str) -> str:
    return (
        "# 計画\n"
        "\n"
        "作成日: 2026-08-18\n"
        "バージョン: 1.0\n"
        "\n"
        "## 変更履歴\n"
        "\n"
        "| 日付 | バージョン | 変更内容 |\n"
        "|---|---|---|\n"
        "| 2026-08-18 | 1.0 | 初版 |\n"
        "\n"
        + body
    )


def english_document(body: str) -> str:
    return (
        "# Plan\n"
        "\n"
        "Date: 2026-08-18\n"
        "Version: 1.0\n"
        "\n"
        "## Change History\n"
        "\n"
        "| Date | Version | Change |\n"
        "|---|---|---|\n"
        "| 2026-08-18 | 1.0 | Initial |\n"
        "\n"
        + body
    )


class PlanCheckTests(unittest.TestCase):
    def test_accepts_japanese_progress_checklist(self) -> None:
        errors = plan_check.check_text(
            japanese_document("## 進捗\n\n- [x] 調査\n- [ ] 実装\n"),
            source="sample.md",
        )
        self.assertEqual(errors, [])

    def test_accepts_english_progress_heading(self) -> None:
        errors = plan_check.check_text(
            english_document("## Progress\n\n- [x] Research\n"),
        )
        self.assertEqual(errors, [])

    def test_rejects_missing_progress_section(self) -> None:
        errors = plan_check.check_text(
            japanese_document("- [ ] Task\n"), source="sample.md"
        )
        self.assertEqual(len(errors), 1)
        self.assertIn("進捗", errors[0])

    def test_rejects_progress_without_checklist(self) -> None:
        errors = plan_check.check_text(
            japanese_document("## 進捗\n\n状態: 未着手\n"), source="sample.md"
        )
        self.assertEqual(len(errors), 1)
        self.assertIn("チェック項目", errors[0])

    def test_rejects_nonstandard_marker_and_empty_label(self) -> None:
        errors = plan_check.check_text(
            japanese_document("## 進捗\n\n- [~] 保留\n- [x]\n"),
            source="sample.md",
        )
        self.assertEqual(len(errors), 2)
        self.assertIn(":14:", errors[0])
        self.assertIn(":15:", errors[1])

    def test_stops_at_next_level_two_heading(self) -> None:
        errors = plan_check.check_text(
            japanese_document(
                "## 進捗\n\n- [x] Done\n\n## メモ\n\n状態: 完了\n"
            ),
        )
        self.assertEqual(errors, [])

    def test_rejects_missing_version_and_change_history(self) -> None:
        errors = plan_check.check_text(
            "# Plan\n\n## 進捗\n\n- [x] Done\n", source="sample.md"
        )
        self.assertEqual(len(errors), 2)
        self.assertTrue(any("バージョン" in error for error in errors))
        self.assertTrue(any("変更履歴" in error for error in errors))

    def test_rejects_mismatched_last_history_version(self) -> None:
        document = japanese_document("## 進捗\n\n- [x] Done\n").replace(
            "| 2026-08-18 | 1.0 | 初版 |", "| 2026-08-18 | 0.9 | 旧版 |"
        )
        errors = plan_check.check_text(document, source="sample.md")
        self.assertEqual(len(errors), 1)
        self.assertIn("一致しません", errors[0])

    def test_rejects_change_history_after_progress(self) -> None:
        document = (
            "# 計画\n\n"
            "バージョン: 1.0\n\n"
            "## 進捗\n\n"
            "- [x] Done\n\n"
            "## 変更履歴\n\n"
            "| 日付 | バージョン | 変更内容 |\n"
            "|---|---|---|\n"
            "| 2026-08-18 | 1.0 | 初版 |\n"
        )
        errors = plan_check.check_text(document, source="sample.md")
        self.assertTrue(any("前に置いてください" in error for error in errors))

    def test_checks_markdown_files_recursively(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "valid.md").write_text(
                japanese_document("## 進捗\n\n- [x] 完了\n"), encoding="utf-8"
            )
            nested = root / "nested"
            nested.mkdir()
            (nested / "invalid.md").write_text("# 未設定\n", encoding="utf-8")

            exit_code, output = plan_check.check_paths([root])

        self.assertEqual(exit_code, 1)
        self.assertTrue(any("valid.md" in line and line.startswith("OK:") for line in output))
        self.assertTrue(any("invalid.md" in line for line in output))

    def test_empty_existing_directory_is_a_successful_skip(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            exit_code, output = plan_check.check_paths([Path(directory)])

        self.assertEqual(exit_code, 0)
        self.assertEqual(output, ["SKIP: 検査対象のMarkdownファイルがありません"])

    def test_missing_path_is_an_error(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            missing = Path(directory) / "missing.md"
            exit_code, output = plan_check.check_paths([missing])

        self.assertEqual(exit_code, 1)
        self.assertIn("存在しません", output[0])


if __name__ == "__main__":
    unittest.main()
