---
targets: ["codexcli", "grokcli"]
root: true
description: "全target共通の入口として使うルール索引と作業ルーター"
globs: ["**/*"]
---

# agents — ルール索引と作業ルーター

このファイルは共有 `AGENTS.md` から参照する短い入口であり、詳細ルール本文の置き場ではない。通常作業では、最初にこの索引で対象条件と正本を確認し、必要なルール・スキルだけを読む。

## 常時適用

- システム・開発者・ユーザーの上位指示を、リポジトリ内ルールで上書きしない。
- 正本は `.rulesync/rules/` と `.rulesync/skills/`。`AGENTS.md` 等の生成物は、通常は直接編集せず、正本を更新して再生成する。
- 指示が衝突した場合の優先順位は `.rulesync/rules/concepts.md` を正本とする。判断できない場合は推測せず、差分と選択肢を提示する。
- 作業の完了には、正本への保存、機械検証、必要な生成確認、監査ログを含める。

## ルーティング表

| ID | 条件 | 参照する正本・スキル | 完了確認 |
|---|---|---|---|
| `route-general` | 一般的な実装・調査・修正 | `.rulesync/rules/concepts.md`、対象に一致するskill | 変更内容に応じたテスト・再読込 |
| `route-docs` | `docs/**/*.md` の作成・更新 | `.rulesync/rules/docs-writing.md`、`content-placement` | 日英同期・リンク・再読込 |
| `route-plan` | `_workingspace/plans/` の計画・設計更新 | `plan-design-check`、`content-placement` | `plan_check.py` 終了コード0 |
| `route-rules` | `.rulesync/`、Rulesync設定、生成物の変更 | `.rulesync/rules/rule-authoring.md`、`output-discipline`、`backup-before-edit` | `generate --check`、テスト |
| `route-rule-evolution` | 同じ修正・判断が再発、レビューで再発防止が求められた | `.rulesync/rules/rule-authoring.md`、`approval-flow`、`content-placement` | 保存先承認 → 正本更新 → 生成/check → 監査 |
| `route-import` | 既存リポジトリへのdna_kernel導入 | `project-onboarding`、`pre-work-check`、`.rulesync/rules/rule-authoring.md`、`approval-flow` | preflight → inventory → 索引化 → dry-run → 承認 → 生成/check |
| `route-onboarding` | 新規プロジェクトまたは既存注入の導入判断 | `project-onboarding`、`pre-work-check` | プロファイル確定・導入検査 |
| `route-audit` | 作業事実・判断理由の記録 | `workspace-audit-log`、`workspace-diary` | strict検査 |
| `route-git` | コミット文案・Git操作 | `.rulesync/rules/git.md` | 差分・検証・依頼範囲の確認 |

## スキル索引

| skill | 条件 |
|---|---|
| `approval-flow` | 課金・外部API・不可逆操作を含む処理 |
| `backup-before-edit` | 既存ファイルを上書き・清書・リライトする処理 |
| `code-testing` | コードを新規作成・変更する処理 |
| `content-placement` | docs・計画書・ルール等の成果物を配置する処理 |
| `output-discipline` | チャット出力を正本ファイルへ保存して確認する処理 |
| `plan-design-check` | 計画書・設計書を作成・更新する処理 |
| `pre-work-check` | 新しい作業を開始する前の必須構成確認 |
| `project-context` | プロジェクトの文脈・制約・決定事項を再利用する処理 |
| `project-onboarding` | dna_kernelを新規または既存リポジトリへ導入する処理 |
| `user-locale` | ホーム設定から会話言語を同期する処理 |
| `weighted-pick` | JSONリストから再現可能な乱数選択を行う処理 |
| `workspace-audit-log` | コード・docs・設定変更後、テスト後、コミット前の証跡記録 |
| `workspace-diary` | 複数作業へ再利用する知見を横断日記へ記録する処理 |

## 正本とtarget分離

- 詳細な標準ルールは、targetとglobを明示した正本として管理する。Codex用の共有 `AGENTS.md` には、この索引以外の詳細本文を自動展開しない。
- `.rulesync/rules/concepts.md` はClaude CodeとCursorの概念正本として生成対象にし、共有 `AGENTS.md` を読むtargetでは必要時に正本を参照する。
- `.rulesync/skills/` は条件付きの作業手順であり、Codex固有skillsは `.agents/skills/` に生成される。
- `tools/kernel/` はコアツール、`tools/plugins/` は標準プロファイル外の承認済み準拠プラグインとする。導入・昇格・依存追加は別途確認する。

## インポートとルール進化

- 既存リポジトリへの導入はdna_kernel主導で行い、対象側を正本として維持する。
- import時は、対象ルートのpreflight、既存ルールのinventory、全ルール・スキルの索引登録または明示除外、target分離、dry-run、ユーザー承認、バックアップ、生成/check、監査を順に行う。
- 同じ修正・判断が再発したときは、LLMが保存候補と保存先を提示し、「rulesyncへ保存するか」をユーザーへ確認する。承認なしに永続化しない。

## フォールバック

条件に一致する正本・スキルがない、targetの実読込が確認できない、共有出力の所有権が衝突する場合は、推測で適用しない。不足情報、影響範囲、選択肢、必要な検証を報告して判断を求める。

索引自体を変更した場合は、`.rulesync/rules/agents.md` を正本として更新し、`python tools/rulesync.py generate --check` と関連テストを実行する。
