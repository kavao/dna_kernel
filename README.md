# dna_kernel — 自己発展型ルールガバナンスの最小カーネル

LLM ハーネス（Claude Code 等）を使う創作・執筆プロジェクトに、
**ルールが肥大化せず、完了条件が曖昧にならず、再現可能に発展する**仕組みを組み込むための最小セットです。

## なぜ必要か

LLM への指示は「書き足す」ほど矛盾が増え、「完了した」は言葉で言うだけでは根拠にならない。
このカーネルは、その2つの問題を構造で解決します。

- **ルールの一本化**: 概念の正本を1か所に置き、他の指示は「それを参照する」形にする
- **完了の拘束**: ファイルへの書き込みと機械確認を済ませるまで「完了」と言わせない
- **追記だけの履歴**: 査証ログは上書き禁止にし、作業事実を改ざんさせない

## このカーネルに含まれるもの

```
dna_kernel/
  README.md                  ← このファイル
  manifest.md                ← 各ファイルの役割と移植先での置き場
  rulesync.jsonc             ← rulesync 設定（targets・features）
  .rulesync/
    rules/
      concepts.md            ← 概念正本（正本副本・完了条件・拘束ルール）
      rule-authoring.md      ← ルールを増やすときの作法
      docs-writing.md        ← docs/ ドキュメント記述ルール
      git.md                 ← git コミットメッセージ・ブランチ運用ルール
    skills/
      workspace-audit-log/SKILL.md  ← 査証ログ運用の手順
      workspace-diary/SKILL.md      ← 横断ナレッジ日記の手順
      output-discipline/SKILL.md    ← ファイル出力→確認→報告の完了規律
      pre-work-check/SKILL.md       ← 作業前の必須確認パターン
      backup-before-edit/SKILL.md   ← 上書き前の旧版退避パターン
      approval-flow/SKILL.md        ← dry-run→承認→実行→確認の承認フロー
      weighted-pick/SKILL.md        ← JSON 重み付き乱数選択の手順
      project-context/SKILL.md      ← プロジェクト文脈の要約・引き継ぎ
      project-onboarding/SKILL.md   ← 新規プロジェクト導入と overview.md 作成フロー
      code-testing/SKILL.md         ← コード変更時のテスト実行・デグレード防止
  docs/
    self-evolving-governance.md  ← パターン全体の説明
  tools/
    README.md                ← ツール一覧・依存関係
    kernel/
      workspace_audit_log.py ← 査証ログ・日記への追記ツール（コア）
      json_weighted_pick.py  ← JSON 重み付き乱数選択ツール（コア）
      novel_project_check.py ← [拡張例] 小説プロジェクト向け pre-work-check 実装
      novel_code_allocate.py ← novel_project_check の依存
      novel_image_layout.py  ← novel_project_check の依存
```

## 新プロジェクトへの導入手順

### 前提

- [rulesync](https://github.com/aisync/rulesync)（npm）
- [uv](https://docs.astral.sh/uv/)（Python パッケージマネージャー）

### 1. rulesync を導入する

```bash
npm install -g rulesync
```

### 2. uv を導入して初回セットアップを実行する

```bash
uv run python init.py
```

`_workingspace/` ディレクトリの確認・作成と、使えるコマンドの案内が出ます。

### 3. ファイルをコピーする

dna_kernel の以下をプロジェクトルートへコピーします。

```
your-project/
  rulesync.jsonc     ← dna_kernel/rulesync.jsonc から
  .rulesync/         ← dna_kernel/.rulesync/ ごとコピー
  pyproject.toml     ← dna_kernel/pyproject.toml から（依存関係追加時に編集）
  init.py            ← dna_kernel/init.py から（プロジェクト用に編集）
```

### 4. rulesync.jsonc を編集する

`targets` に使用する LLM ツールを指定します。

```jsonc
{
  "targets": ["claudecode", "cursor", "codexcli"],  // 使うツールだけ残す
  "features": ["rules", "skills"],
  "outputRoots": ["."],
  "delete": true
}
```

選択肢: `claudecode` / `cursor` / `copilot` / `codexcli` / `kilo`

### 5. rulesync を実行する

生成前に、まず dry-run で出力内容を確認します。

```bash
npx rulesync generate --dry-run
```

問題がなければ生成します。

```bash
npx rulesync generate
```

各 LLM ツール向けの設定ファイル（`.claude/`、`.cursor/`、`.codex/` 等）が自動生成されます。

`npx rulesync` だけを実行すると、現在の rulesync ではヘルプが表示されるだけです。
これはエラーではなく、サブコマンドが未指定であることを示しています。

### 6. ツールを置く（任意）

コアツールをプロジェクトの `tools/kernel/` へコピーします。

```
your-project/
  tools/
    kernel/
      workspace_audit_log.py ← 査証ログ・日記への追記
      json_weighted_pick.py  ← JSON 重み付き乱数選択
```

`novel_project_check.py`（+依存2ファイル）は `pre-work-check` パターンの小説プロジェクト向け実装例です。
新プロジェクトでは参考にして独自のチェックスクリプトを用意するか、`REQUIRED_FILES` / `REQUIRED_DIRS` を書き換えて流用してください。

### 7. .gitignore を確認する

dna_kernel の `.gitignore` をそのままコピーするか、既存の `.gitignore` に以下を追記します。

```
# rulesync 生成物
# 正本は rulesync.jsonc と .rulesync/ に置き、各ツール向け生成物は除外する
.claude/
.cursor/
.codex/
.kilo/
.agent/
AGENTS.md
CLAUDE.md

# ワークスペース（ローカル作業ファイル）
_workingspace/**
!_workingspace/**/
!_workingspace/**/.gitkeep
_backup/
```

rulesync の生成物はコミットせず、`rulesync.jsonc` と `.rulesync/` を正本としてコミットします。
リポジトリをクローンしたメンバーは、必要に応じて `npx rulesync generate` を実行して各ツール向け設定を再生成します。

## 日常運用でよく使うコマンド

初回セットアップ:

```bash
uv run python init.py
```

ルール再生成（`.rulesync/` を変更したあとに実行）:

```bash
npx rulesync generate
```

査証ログ追記:

```bash
uv run python tools/kernel/workspace_audit_log.py append "作業内容"
```

## 既存プロジェクトへの段階的な組み込み方

既存のルールが散在している場合は、段階的に移行できます。

1. `.rulesync/rules/concepts.md` を置き、既存ルールの「短い定義・禁止・完了条件」だけを移す
2. 既存の各ルールファイルから概念本文を削り、`concepts.md` への参照リンクに置き換える
3. `workspace_audit_log.py` を置いてから、LLM への指示に「作業後はログを書く」を加える
4. `npx rulesync generate` を実行して各ツールへ反映する

## 新規プロジェクト導入時の対話フロー

新しいプロジェクトへ導入する場合、アシスタントはまず `overview.md` の有無を確認します。
`overview.md` がなければ作成するかを確認し、了承後に rulesync・uv の導入状況を確認します。

未導入のものがあれば、実行予定コマンドを提示して了承を得てから自動導入します。
導入と `npx rulesync generate` が終わったあとで、どのようなプロジェクトを行うのかを質問し、回答を `overview.md` に反映します。

dna_kernel 本体を修正する場合は **DNA_KERNEL 開発モード** として扱い、この導入質問フローは省略します。
