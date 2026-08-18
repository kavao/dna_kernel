from __future__ import annotations

import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
import sys

sys.path.insert(0, str(ROOT / "tools" / "kernel"))

import dna_kernel_import  # noqa: E402
import rulesync_router_metrics  # noqa: E402


class RulesyncRouterContractTests(unittest.TestCase):
    def test_current_source_inventory_has_complete_index_coverage(self) -> None:
        inventory = dna_kernel_import.inventory(ROOT)
        self.assertTrue(inventory["index"]["exists"])
        self.assertEqual(inventory["index"]["coverage"], 1.0)

    def test_index_has_routing_fallback_and_generation_contract(self) -> None:
        text = (ROOT / ".rulesync" / "rules" / "agents.md").read_text(encoding="utf-8")
        for required in ("## ルーティング表", "## スキル索引", "## フォールバック", "generate --check"):
            with self.subTest(required=required):
                self.assertIn(required, text)
        self.assertNotIn("## 正本と副本", text)
        self.assertLessEqual(len(text.splitlines()), 250)
        self.assertLessEqual(len(text.encode("utf-8")), 12_000)

    def test_root_owners_are_unique_per_target_and_detailed_rules_are_excluded(self) -> None:
        code, report = dna_kernel_import.verify(ROOT)
        self.assertEqual(code, 0, report["errors"])
        self.assertEqual(
            report["target_root_owners"],
            {
                "claudecode": [".rulesync/rules/concepts.md"],
                "codexcli": [".rulesync/rules/agents.md"],
                "cursor": [".rulesync/rules/concepts.md"],
                "grokcli": [".rulesync/rules/agents.md"],
            },
        )

        for path in (
            ROOT / ".rulesync" / "rules" / "concepts.md",
            ROOT / ".rulesync" / "rules" / "docs-writing.md",
            ROOT / ".rulesync" / "rules" / "git.md",
            ROOT / ".rulesync" / "rules" / "rule-authoring.md",
        ):
            frontmatter = dna_kernel_import._frontmatter(path)
            self.assertNotIn("codexcli", frontmatter["targets"])
            self.assertNotIn("grokcli", frontmatter["targets"])

    def test_metrics_reproduce_utf8_lines_chars_bytes_and_hash(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "sample.md"
            path.write_text("a\n日本\n", encoding="utf-8")
            report = rulesync_router_metrics.summarize([path], base=root)

        self.assertEqual(report["totals"], {"files": 1, "lines": 2, "chars": 5, "bytes": 9})
        self.assertEqual(report["files"][0]["path"], "sample.md")
        self.assertEqual(len(report["files"][0]["sha256"]), 64)

    def test_import_plan_is_read_only_and_has_approval_gate(self) -> None:
        before = dna_kernel_import.inventory(ROOT)
        plan = dna_kernel_import.build_import_plan(ROOT, "governance")
        after = dna_kernel_import.inventory(ROOT)

        self.assertTrue(plan["dry_run"])
        self.assertFalse(plan["writes_performed"])
        self.assertTrue(plan["approval_required"])
        self.assertEqual(before["entries"], after["entries"])
        self.assertTrue(all(action["approval_required"] for action in plan["actions"] if action["writes"]))

    def test_preflight_rejects_a_directory_without_a_git_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            report = dna_kernel_import.preflight(Path(directory))
        self.assertFalse(report["ok"])
        self.assertFalse(report["git"]["marker_exists"])

    def test_verify_detects_an_unindexed_canonical_rule(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            rules = root / ".rulesync" / "rules"
            rules.mkdir(parents=True)
            (rules / "agents.md").write_text(
                '---\ntargets: ["codexcli"]\nroot: true\n---\n\n# index\n',
                encoding="utf-8",
            )
            (rules / "unlisted.md").write_text(
                '---\ntargets: ["codexcli"]\n---\n\n# unlisted\n',
                encoding="utf-8",
            )
            code, report = dna_kernel_import.verify(root)
        self.assertEqual(code, 1)
        self.assertFalse(report["ok"])
        self.assertIn("網羅率", report["errors"][0])


if __name__ == "__main__":
    unittest.main()
