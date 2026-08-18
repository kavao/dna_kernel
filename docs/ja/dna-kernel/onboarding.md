# dna_kernel 導入・注入フロー

[English](../../en/dna-kernel/onboarding.md) · 日本語

dna_kernel には、次の3つの作業モードがあります。

| モード | 用途 | README の扱い |
|--------|------|---------------|
| 新規プロジェクト作成モード | まだ概要や README がない場所へ立ち上げる | 作成するか確認してからプロジェクト用 README を作る |
| 既存プロジェクト注入モード | すでにあるプロジェクトへ dna_kernel を追加する | 既存 README は触らず、dna_kernel 説明は `docs/ja/dna-kernel/` と `docs/en/dna-kernel/` へ置く |
| DNA_KERNEL 開発モード | dna_kernel 本体を修正する | 導入質問を省略して直接修正する |

## 導入プロファイルとツール切替

導入先の規模や運用に応じて、取り込む範囲を選びます。

| プロファイル | 取り込む範囲 | 向いている状況 |
|---|---|---|
| Rule-only | ルール正本、Rulesync設定・ラッパー、各AIツール向け生成設定 | まずCodex・Claude Code・Cursor等の指示を揃えたい |
| Governance | Rule-only + 完了規律、計画検査、査証ログ、`_workingspace/` | 作業の完了根拠と履歴も残したい |
| Full | Governance + onboarding、user-locale、必要な補助スキル・ツール | 複数人・複数PC・複数AIツールで運用したい |

共通正本から対応targetの設定を生成するため、AIツールを切り替えるたびにルール、完了条件、計画状態、会話言語を説明し直すコストを下げられます。現在の標準targetは `claudecode`、`cursor`、`codexcli`、`grokcli` です。Rulesync 15.0.1は `grokcli` で `.grok/skills/` を生成しますが、実際のGrok Buildの読み込みは導入先で確認します。

## 既存プロジェクト注入モード

既存プロジェクトでは、既存の構成を壊さないことを優先します。

ユーザーが注入先ディレクトリを明示した場合、そのディレクトリを注入先ルートとして扱います。
monorepo の上位ディレクトリや Git ルートへ自動的には広げません。

例:

```text
K:\共有\10_プログラム\node\grokbot_news\packages\discord-bot\
```

このパスを指定された場合、以下は `packages/discord-bot/` 配下へ置きます。

```text
.rulesync/
rulesync.jsonc
config/rulesync_toolchain.json
docs/ja/dna-kernel/
docs/en/dna-kernel/
tools/install_rulesync.py
tools/rulesync.py
tools/kernel/
_workingspace/
```

基本方針:

- 既存の `README.md` を上書きしない
- `images/title.png` は dna_kernel 本体 README 用のタイトル画像であり、注入先プロジェクトへは**取り込まない**
- 既存の `.gitignore`, `pyproject.toml`, `tools/`, `docs/` は内容を確認してから追記する
- dna_kernel の詳しい説明は `docs/ja/dna-kernel/`（編集正本）と `docs/en/dna-kernel/`（対訳）へ置く
- `.rulesync/`, `rulesync.jsonc`, `config/rulesync_toolchain.json`, `tools/install_rulesync.py`, `tools/rulesync.py`, `tools/kernel/` を正本・実働ツールとして追加する
- rulesync 生成物（`.claude/`, `.cursor/`, `.codex/`, `.agents/`, `.grok/`, `.kilo/`, `AGENTS.md`, `CLAUDE.md`）は ignore する

## 既存ルールの棚卸しと索引化

既存リポジトリへの導入は、dna_kernelを導入のcontrol plane、導入先を正本と成果物のdata planeとして扱います。dna_kernel側が手順と検査を主導しますが、導入後のプロジェクト固有ルールをdna_kernel本体へ無差別に戻したり、最新版で上書きし続けたりしません。

対象ルートはユーザーが指定したディレクトリに限定します。書き込み前に、対象ルートで次を順番に実行します。

```bash
uv run python tools/kernel/dna_kernel_import.py preflight <target-root>
uv run python tools/kernel/dna_kernel_import.py inventory <target-root> --format json
uv run python tools/kernel/dna_kernel_import.py plan <target-root> --profile governance --dry-run
```

`AGENTS.md`、`CLAUDE.md`、`.cursor/`、`.claude/` 等は、正本か生成物かを判定して一覧化します。判定できないものは一括コピーせず保留します。既存ルールとskillは、`.rulesync/rules/agents.md` のroute、常時適用、明示除外のいずれかに登録し、ルール名・適用条件・正本・完了確認を残します。

共有 `AGENTS.md` は詳細ルールの集積場所にしません。索引を所有するtargetを1件（本体の標準構成では `codexcli` と `grokcli` が同じ索引を生成）に固定し、標準ルールはtargetとglobで明示的に分離します。`targets: ["*"]` を共有入口への暗黙の許可として扱わず、生成確認と実際のAIツールの読込確認を別々に記録します。

LLMは、既存知識を採用・統合・参照化・除外・保留に分類した理由、保存先、target、生成物、依存性、テスト、ロールバックへの影響を提示します。ユーザー承認前は正本や設定を変更しません。承認後に限り、バックアップ、正本注入、生成、検査、監査を行います。

## ルール候補をrulesyncへ保存する動線

ユーザーがMarkdownを毎回手書きで整理することを前提にしません。同じ修正・判断が繰り返されたとき、またはユーザーが「今後は常に」と指定したとき、LLMが候補を要約します。そのうえで次のように確認します。

```text
今回の判断は、今後もこのプロジェクトで適用するルールとしてrulesyncへ保存しますか？
保存先候補: .rulesync/rules/ / .rulesync/skills/ / 個人設定 / 今回限り（保存しない）
```

承認時だけ保存先を分類し、正本をバックアップして更新します。却下・保留時は永続正本へ保存しません。保存後は `generate --dry-run`、生成、`generate --check`、関連テスト、監査ログを実行します。保存先が不明、既存ルールと重複、秘密情報や未検証推測を含む場合は保留します。

依存性は、Python `>=3.11` と標準ライブラリ中心のkernelツールを基盤とします。uvは推奨ですが任意で、日常のRulesync生成にNode.js、npm、pnpm、Corepackは不要です。Rulesync単体バイナリとネットワークは初回取得・版更新時だけ必要です。

推奨フロー:

1. 既存の README・docs・tools・.rulesync・rulesync.jsonc の有無を確認する
2. preflight・inventory・agents.md索引案・dry-runを実行する
3. Rule-only / Governance / Full のどれを使うか、既存ルールの採否を提示する
4. 注入してよいか、変更予定を提示して了承を得る
5. `docs/ja/dna-kernel/` に説明文書を置き、`docs/en/dna-kernel/` に英訳を同期する
6. `.rulesync/` と `rulesync.jsonc` を追加または統合する
7. `tools/kernel/` に必要なツールを置く（任意プラグインは承認後に `tools/plugins/`）
8. `.gitignore` に rulesync 生成物、Rulesync キャッシュ、`_workingspace/` の扱いを追記する
9. `python tools/install_rulesync.py` で Rulesync 15.0.1 を取得・検証する
10. `python tools/rulesync.py generate --dry-run` で生成内容を確認する
11. 了承後にバックアップ、正本注入、`python tools/rulesync.py generate` を実行する
12. `dna_kernel_import.py verify`、`python tools/rulesync.py generate --check`、関連テスト、監査ログを実行する
13. `uv run python tools/kernel/user_prefs.py sync` を実行する
14. 必要なら `overview.md` を作るか確認し、プロジェクトの目的・成果物・制約を聞く

## 新規プロジェクト作成モード

新規プロジェクトでは、最初に `overview.md` の有無を確認します。
なければ作成するかを確認し、了承後に rulesync と uv の導入状況を確認します。

導入の基本コマンド:

```bash
uv run python init.py
python tools/install_rulesync.py
python tools/rulesync.py generate --dry-run
python tools/rulesync.py generate
python tools/rulesync.py generate --check
uv run python tools/kernel/user_prefs.py sync
```

Rulesync は v15.0.1 の公式単体バイナリを Python ラッパーが取得・検証します。
日常の生成には Node.js、npm、pnpm、Corepack は不要です。生成には `generate` サブコマンドを使い、`generate` の**後**に `generate --check` と `user_prefs.py sync` を実行します。

計画書・設計書の進捗確認:

```bash
uv run python tools/kernel/plan_check.py _workingspace/plans
```

計画書・設計書には、進捗チェックボックスに加えて `バージョン: MAJOR.MINOR` と追記専用の `## 変更履歴` を置きます。計画を更新したら版を上げ、履歴の末尾へ変更内容を追加してから検査します。

## 会話言語とホーム config

**会話言語**（LLM とのチャット）と **docs の編集正本**（`docs/ja/` → `docs/en/` 同期）は別軸です。日本語で会話していても、docs は `docs-writing` のバイリンガル方針に従います。

| 設定 | 置き場 | git 管理 |
|------|--------|----------|
| 会話言語・執筆既定 | `~/.config/dna-kernel/config.toml` | ×（個人マシン） |
| プロジェクト上書き | `.dna-kernel.local.toml` | ×（gitignore） |
| API キー等 | `.env` | × |

初回テンプレ作成:

```bash
uv run python tools/kernel/user_prefs.py init-config
```

会話言語の確認:

```bash
uv run python tools/kernel/user_prefs.py show conversation.language
```

執筆前は `content-placement` スキルで種類と正本を宣言します（`user-locale` と併用）。

## .gitignore 例

```gitignore
# rulesync 生成物
# 正本は rulesync.jsonc と .rulesync/ に置き、各ツール向け生成物は除外する
.claude/
.cursor/
.codex/
.kilo/
.agents/
.grok/
AGENTS.md
!.rulesync/rules/agents.md
CLAUDE.md

# ワークスペース（計画書は共有、ログと日記はローカル）
_workingspace/**
!_workingspace/**/
!_workingspace/**/.gitkeep
!_workingspace/plans/
!_workingspace/plans/*.md
_workingspace/tmp-tools/
_backup/
_old/

# Rulesync 固定版キャッシュ（Python ラッパーが取得）
.tools/

# user-locale: プロジェクト local 上書き
.dna-kernel.local.toml
```
