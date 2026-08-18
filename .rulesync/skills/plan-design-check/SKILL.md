---
name: plan-design-check
description: >-
  計画書・設計書の進捗欄を確認し、[ ] / [x] のチェックボックス形式と
  完了状態の表記を機械検査する。
targets: ["*"]
---

## 目的

計画書・設計書の進捗表記をプロジェクトごとに揺らさず、複数セッションや複数PCで状態を共有できるようにする。
進捗の定義は `rules/concepts.md` を正本とする。

## 実行

計画書・設計書を作成または更新した後、次を実行する。

```bash
uv run python tools/kernel/plan_check.py _workingspace/plans
```

別のファイルまたはディレクトリを確認する場合は、対象パスを渡す。

```bash
uv run python tools/kernel/plan_check.py docs/design.md docs/design/
```

終了コード **0** を確認してから完了扱いにする。1 の場合は、対象文書に `## 進捗` または `## Progress` と、`- [ ]` / `- [x]` の項目を追加する。

## 検査内容

- 進捗セクションが存在すること
- 進捗セクションに1件以上のチェック項目があること
- 状態記号が `[ ]` または `[x]` であること
- チェック項目に説明があること

部分完了、確認待ち、保留は `[ ]` のまま項目名や補足へ記載する。`[~]` や `完了` / `部分完了` だけの表記は使用しない。

## 関連

- 概念正本: `rules/concepts.md`
- 検査ツール: `tools/kernel/plan_check.py`
- 完了規律: `skills/output-discipline/SKILL.md`
