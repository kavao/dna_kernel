# tools（dna_kernel）

自己発展型ルールガバナンスを「実働」させるためのツールです。
`kernel/` にコアツールと拡張例を収めてあります。

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
