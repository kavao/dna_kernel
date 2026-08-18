# dna_kernel 詳細

[English](../../en/dna-kernel/README.md) · 日本語

dna_kernel は、LLM ハーネス（Claude Code 等）を使う創作・執筆・開発プロジェクトに、
**ルールが肥大化せず、完了条件が曖昧にならず、再現可能に発展する**仕組みを組み込むための最小セットです。

ルート `README.md` は導入先プロジェクトのものとして扱います。
dna_kernel 自体の詳しい説明は、この `docs/ja/dna-kernel/` 配下（編集正本）と `docs/en/dna-kernel/`（英訳）へ置きます。

## 誰向けか

既存の開発・創作リポジトリで、Codex・Claude Code・Cursorなど複数のLLMツールを使い分けるチーム向けです。dna_kernelを導入先へ注入すると、ツールごとに指示を再説明したり、異なる設定ファイルを個別に修正したりする作業を減らせます。

対応するAIツールごとの現状:

| ツール | Rulesync target | 生成 | 実際の読み込み |
|---|---|---|---|
| Claude Code | `claudecode` | `CLAUDE.md` と `.claude/` | 確認済み※ |
| Cursor | `cursor` | `.cursor/` | 未検証 |
| Codex CLI | `codexcli` | 索引専用の `AGENTS.md` と `.agents/skills/` | 未検証 |
| Grok Build | `grokcli` | 索引専用の `AGENTS.md` と `.grok/skills/` | 未検証（導入先で要確認） |

※ 2026-08-18時点、この表を作成したClaude Codeセッション自身が、生成された `CLAUDE.md` を読み込んで動作していることで確認済みです（このセッションの`CLAUDE.md`・`.claude/rules/`はここまでの編集を反映して再生成済み。記録: `_workingspace/log/202608.md`）。他の導入先では改めて確認してください。

「生成できる」ことと「実際にツールが読み込む」ことは別です。上表の状態は、targetを追加・更新するたびに見直してください。

Codex CLIとGrok Buildが共有する `AGENTS.md` は、詳細ルールを連結する場所ではなく、`.rulesync/rules/agents.md` から必要な正本・skillへ進む索引です。Claude CodeとCursorには、targetを明示した詳細ルールを別出力します。これにより、標準ルールが共有入口へ後勝ちで混入することを防ぎ、入口の大きさとtarget別の責任範囲を測定できます。

## 導入で得られるもの

| 課題 | 導入後の仕組み | 確認場所 |
|---|---|---|
| ツールごとにルールが分かれる | `.rulesync/` の正本から設定を生成する | `AGENTS.md`、`CLAUDE.md`、`.cursor/` 等 |
| 完了報告の根拠が曖昧 | 保存・再読込・機械検査を完了条件にする | `generate --check`、`plan_check.py` |
| 作業履歴が書き換わる | 査証ログを追記専用で残す | `_workingspace/log/` |
| 計画の詳細状態がずれる | `[ ]` / `[x]` と版・変更履歴を検査する | `_workingspace/plans/` |
| 環境構築がツールごとに必要 | Python標準ライブラリ中心で生成する | `tools/`、`config/` |
| 既存ルールの知見が分散する | 導入時に棚卸しし、`AGENTS.md` 索引へ登録または明示除外する | `dna_kernel_import.py`、`.rulesync/rules/agents.md` |
| ルールをユーザーが手書きで整理し続ける | LLMが候補を整理し、保存先とrulesyncへの保存を確認してから正本へ反映する | `self-evolving-governance.md` |

## 導入プロファイル

必要な範囲から始められるよう、次の3段階で導入します。

- **Rule-only**: ルール正本と各AIツール向け設定の統一
- **Governance**: 完了判定、計画検査、査証ログまで統一
- **Full**: 導入判定、会話言語、副本同期などの補助機能まで利用

プロファイルの具体的なコピー対象は [`manifest.md`](../../../manifest.md) と [onboarding.md](onboarding.md) を確認してください。

## 依存性

- Python `>=3.11` が基盤です。主要なkernelツールに外部Pythonパッケージはありません。
- uvは推奨実行補助ですが、標準ライブラリのツールは `python` でも実行できます。
- 日常のRulesync生成にNode.js、npm、pnpm、Corepackは必要ありません。
- Rulesync単体バイナリとネットワークは、初回取得または版更新時に必要です。取得後は`.tools/`のキャッシュを使います。

会話言語は、チャットでの明示、プロジェクトlocal、ホームconfig、OS localeの順で解決します。プロジェクト固有の設定は `.dna-kernel.local.toml` に置き、Git管理しません。

## なぜ必要か

LLM への指示は「書き足す」ほど矛盾が増え、「完了した」は言葉で言うだけでは根拠になりません。
このカーネルは、その2つの問題を構造で解決します。

- **ルールの一本化**: 概念の正本を1か所に置き、他の指示は「それを参照する」形にする
- **完了の拘束**: ファイルへの書き込みと機械確認を済ませるまで「完了」と言わせない
- **追記だけの履歴**: 査証ログは上書き禁止にし、作業事実を改ざんさせない

## このカーネルに含まれるもの

```text
dna_kernel/
  README.md                  ← short entry (English, default display)
  README.ja.md               ← short entry (Japanese, editorial source)
  manifest.md                ← 各ファイルの役割と移植先での置き場
  rulesync.jsonc             ← rulesync 設定（targets・features）
    .rulesync/
    rules/                   ← 索引・概念・運用ルールの正本
      agents.md              ← 共有AGENTS.mdの薄い入口・ルーター
    skills/                  ← LLM 向けの実行手順
  docs/
    README.md                ← ドキュメント入口（EN リンク先頭）
    en/dna-kernel/           ← 英語（表示デフォルト・対訳）
    ja/dna-kernel/           ← 日本語（編集正本）
  config/
    rulesync_toolchain.json  ← Rulesync 15.0.1 の固定資産・SHA-256
  tools/
    README.md
    install_rulesync.py      ← 固定版バイナリの取得・検証
    rulesync.py              ← 固定版バイナリの実行ラッパー
    kernel/
      workspace_audit_log.py
      json_weighted_pick.py
      rulesync_router_metrics.py
      dna_kernel_import.py
```

## README の扱い

導入先プロジェクトでは、ルート `README.md` をプロジェクト自身の紹介・使い方のために残します。
dna_kernel の説明は `docs/ja/dna-kernel/` と `docs/en/dna-kernel/` へ置き、既存プロジェクトの README を勝手に移動・上書きしません。

新規プロジェクトで README がない場合だけ、作成するか確認します。

## よく使うコマンド

初回セットアップ:

```bash
uv run python init.py
```

ルール再生成:

```bash
python tools/install_rulesync.py
python tools/rulesync.py generate --dry-run
python tools/rulesync.py generate
python tools/rulesync.py generate --check
uv run python tools/kernel/user_prefs.py sync
```

ルーターの定量確認と既存リポジトリの導入計画:

```bash
uv run python tools/kernel/rulesync_router_metrics.py .rulesync/rules .rulesync/skills --base . --format json
uv run python tools/kernel/dna_kernel_import.py preflight <target-root>
uv run python tools/kernel/dna_kernel_import.py inventory <target-root> --format json
uv run python tools/kernel/dna_kernel_import.py plan <target-root> --profile governance --dry-run
uv run python tools/kernel/dna_kernel_import.py verify <target-root>
```

`dna_kernel_import.py` は読み取り専用です。承認前に既存リポジトリへ書き込まず、preflight・棚卸し・索引案・dry-runの結果を提示します。承認後はバックアップ、正本への最小注入、生成、`generate --check`、監査ログの順で進めます。

Rulesync は v15.0.1 の公式単体バイナリを Python ラッパーで取得・検証します。日常の生成に Node.js、npm、pnpm、Corepack は必要ありません。取得物は `.tools/` に保存され、Git 管理されません。

査証ログ追記:

```bash
uv run python tools/kernel/workspace_audit_log.py append "作業内容"
```

## 詳細

- 導入・注入フロー: [onboarding.md](onboarding.md)
- ガバナンスの考え方: [self-evolving-governance.md](self-evolving-governance.md)
- ファイル一覧: [../../../manifest.md](../../../manifest.md)
