# tools（dna_kernel）

自己発展型ルールガバナンスを「実働」させるためのツールです。
`kernel/` にコアツールと拡張例を収めてあります。

`tools/` はルール体系そのものではなく、`.rulesync/` の正本に定めた生成・完了確認・証跡を実行する補助層です。Codex・Claude Code・Cursor等の間を移動しても、同じ正本と検査結果を使えるようにします。

## 導入プロファイル

- **Rule-only**: `.rulesync/` のルールとRulesync生成を使う
- **Governance**: `output-discipline`、`plan-design-check`、`workspace-audit-log`を加える
- **Full**: `project-onboarding`、`user-locale`、必要な補助処理まで使う

## コア（どのプロジェクトにも移植できる）

プロジェクトの種類に関わらず使えるツールです。

- **追記ログ（auditability）**
  - `kernel/workspace_audit_log.py`
  - 追記先: `_workingspace/log/YYYYMM.md`, `_workingspace/diary/YYYYMM.md`
  - 依存: なし（標準ライブラリのみ）
- **重み付き乱数選択（weighted-pick）**
  - `kernel/json_weighted_pick.py`
  - 依存: なし（標準ライブラリのみ）
- **ユーザーロケール（user-locale）**
  - `kernel/user_prefs.py`
  - ホーム config: `~/.config/dna-kernel/config.toml`（git 管理外）
  - 依存: なし（標準ライブラリのみ、`tomllib`）
- **計画書・設計書チェック（plan-design-check）**
  - `kernel/plan_check.py`
  - `## 進捗` / `## Progress` と `- [ ]` / `- [x]` の形式を検査
  - 依存: なし（標準ライブラリのみ）
- **Rulesyncルーター定量測定**
  - `kernel/rulesync_router_metrics.py`
  - 正本・一時生成物のファイル数、行数、文字数、バイト数、SHA-256、ベースライン差分を測定
  - 依存: なし（Python標準ライブラリのみ。`wc`、`awk`、`du` は使わない）
- **dna_kernel導入検査**
  - `kernel/dna_kernel_import.py`
  - 既存リポジトリの `preflight`、`inventory`、`plan --dry-run`、`verify` を読み取り専用で実行
  - `AGENTS.md` 索引の網羅率、targetごとのroot所有者、正本・生成物の分類を確認
  - 依存: なし（Python標準ライブラリのみ）

## Rulesync 固定版ツールチェーン

Rulesync 15.0.1 の公式単体バイナリを Python 標準ライブラリで取得・検証し、Node.js を使わずに実行します。

- `config/rulesync_toolchain.json` — OS・CPU 別の資産、URL、SHA-256、キャッシュ先
- `install_rulesync.py` — 初回取得、SHA-256 検証、`--version` 検証、`--force` 再取得
- `rulesync.py` — 検証済みローカルバイナリへ CLI 引数と終了コードを透過
- キャッシュ先: `.tools/rulesync/15.0.1/`（Git 管理外）

日常の生成は次の順で行います。

```bash
python tools/install_rulesync.py
python tools/rulesync.py generate --dry-run
python tools/rulesync.py generate
python tools/rulesync.py generate --check
uv run python tools/kernel/user_prefs.py sync
```

ルーターと導入の確認:

```bash
uv run python tools/kernel/rulesync_router_metrics.py .rulesync/rules .rulesync/skills --base . --format json
uv run python tools/kernel/dna_kernel_import.py preflight <target-root>
uv run python tools/kernel/dna_kernel_import.py inventory <target-root> --format json
uv run python tools/kernel/dna_kernel_import.py plan <target-root> --profile governance --dry-run
uv run python tools/kernel/dna_kernel_import.py verify <target-root>
```

`dna_kernel_import.py` は計画を表示するだけで対象リポジトリへ書き込みません。ユーザー承認、バックアップ、注入、Rulesync生成、`generate --check`、監査ログの順序は `project-onboarding` に従います。

## 拡張例（小説プロジェクト向けの pre-work-check 実装）

`pre-work-check` パターン（作業前に必須ファイル・ディレクトリを機械確認する）を、
小説プロジェクト向けに実装した例です。

新プロジェクトでは `REQUIRED_FILES` / `REQUIRED_DIRS` を書き換えるか、
独自のチェックスクリプトを作成して同じパターンを適用してください（→ `skills/pre-work-check/SKILL.md`）。

- `kernel/novel_project_check.py` — 作品フォルダの必須ファイル確認（エントリポイント）
  - 依存（import）: `kernel/novel_code_allocate.py`、`kernel/novel_image_layout.py`

## 依存の注意

- `novel_project_check.py` は `novel_code_allocate.py` と `novel_image_layout.py` を import します（3ファイルはセット）。
- `kernel/workspace_audit_log.py` と `kernel/json_weighted_pick.py` は単独で動きます。
- `kernel/user_prefs.py` も単独で動きます。
- 主要なkernelツールはPython `>=3.11` の標準ライブラリだけで動作し、uvは任意です。
- `python` と `uv run python` はどちらでも実行できます。`uv run python` は uv が管理するプロジェクト環境と `pyproject.toml` のPython条件（`>=3.11`）で実行し、`python` は素のインタプリタで実行します。`install_rulesync.py`・`rulesync.py` のように早期に使うツールは `python` を、`init.py` や `kernel/` 配下の運用ツールは `uv run python` を既定の例として示しています。
- Rulesyncの初回取得・版更新にはネットワークが必要ですが、日常の生成にNode.js、npm、pnpm、Corepackは必要ありません。
- 現在の標準targetは `claudecode`、`cursor`、`codexcli`、`grokcli` です。Rulesync 15.0.1は `grokcli` で `.grok/skills/` を生成しますが、実際のGrok Buildの読み込みは導入先で確認します。
