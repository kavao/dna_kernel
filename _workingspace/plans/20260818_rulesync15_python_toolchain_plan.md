# Rulesync 15 固定版・Python ラッパー運用計画

作成日: 2026-08-18
バージョン: 1.0

## 結論

実現可能です。`rulesync` を npm / `corepack pnpm dlx` で取得せず、Python 標準ライブラリだけで固定版の公式単体バイナリを取得・検証・実行する方式へ拡張できます。

ただし、参照ブランチの実装は現状 `windows-x64` のみを設定しているため、そのままでは「プラットフォームを問わない」実装ではありません。Rulesync v15.0.1 の公式リリースにある OS・CPU 別バイナリを選択する層を追加します。

## 調査根拠

- 参照実装: [monogatari-coach `feature/structure_2_1`](https://github.com/kavao/monogatari-coach/tree/feature/structure_2_1)
- 参照の取得処理: [`tools/install_rulesync.py`](https://github.com/kavao/monogatari-coach/blob/feature/structure_2_1/tools/install_rulesync.py)
- 参照の実行ラッパー: [`tools/rulesync.py`](https://github.com/kavao/monogatari-coach/blob/feature/structure_2_1/tools/rulesync.py)
- 参照の固定設定: [`config/rulesync_toolchain.json`](https://github.com/kavao/monogatari-coach/blob/feature/structure_2_1/config/rulesync_toolchain.json)
- Rulesync v15.0.1 のリリース: [`dyoshikawa/rulesync` v15.0.1](https://github.com/dyoshikawa/rulesync/releases/tag/v15.0.1)

参照実装が採用している要素は次のとおりです。

1. `version`、ダウンロード URL、SHA-256、キャッシュ先を設定ファイルへ固定する。
2. Python の `urllib` で取得し、SHA-256 を検証する。
3. 実行後の `--version` が期待値と一致することを検証する。
4. 一時ファイルへ保存してから `os.replace` で配置する。
5. 日常の生成は、リポジトリ内のローカルバイナリを Python ラッパーから実行する。

## 現状との差分

| 項目 | 現在の dna_kernel | 参照方式へ移行後 |
|------|------------------|------------------|
| Rulesync の取得 | `corepack pnpm dlx rulesync` が都度解決するため、今回の実行では 16.13.0 | v15.0.1 を固定し、SHA-256 とバージョンを検証 |
| Node.js | Rulesync 実行に必要 | 不要 |
| Python | 3.11 以上、依存なし | 同じ前提で取得・実行ラッパーを動かす |
| キャッシュ | なし | Git 管理外の `.tools/rulesync/15.0.1/<platform>/` |
| OS 対応 | pnpm 側に委ねる | v15.0.1 の公式バイナリ対応範囲を明示 |
| 正本 | `.rulesync/` と `rulesync.jsonc` | 変更しない |
| 現行の生成設定 | 実装前は `delete: true` | `delete: false` に変更し、user-locale 副本を含む不要ファイルの削除は別作業に分離 |

## 対応プラットフォーム

v15.0.1 のリリース資産に基づき、次の 5 組み合わせを初期対応範囲とします。

| OS | CPU | リリース資産 | SHA-256 |
|----|-----|--------------|---------|
| Windows | x64 | `rulesync-windows-x64.exe` | `e8d25ac6111d7d24159439da68c22d922219c087eec808a66a3992ceb4aa64bc` |
| macOS | x64 | `rulesync-darwin-x64` | `917e100447621cfaea390cfc3e26f5f1cf84151554685c90644b9e3845d0cae1` |
| macOS | arm64 | `rulesync-darwin-arm64` | `bb1eedab590f4ef3075315dec1df27cebeb49debe545bd084f7746d7d330e4fc` |
| Linux | x64 | `rulesync-linux-x64` | `78663aee6d4892b63f5c56e46cd2e8f175901bb6cea2d7825172290d583e6701` |
| Linux | arm64 | `rulesync-linux-arm64` | `1f61978418e4704c9243fca929fc07986b6238d1c1888d9e9c3ab267049fc51d` |

Windows arm64、Linux の未掲載 CPU、FreeBSD 等は初期対応外とし、取得を試みず対応範囲と実行環境を示すエラーにします。「プラットフォームを問わない」は、無制限にすべての OS・CPU を保証する意味ではなく、この対応表の範囲で Node.js の有無や OS ごとの npm 手順に依存しない意味で定義します。

## 目標構成

### 追加するファイル

- `config/rulesync_toolchain.json`
  - 固定バージョン `15.0.1`
  - OS・CPU からリリース資産へ解決する情報
  - 各資産の URL、SHA-256、実行ファイル名、キャッシュ相対パス
- `tools/install_rulesync.py`
  - OS・CPU の正規化
  - 対応資産の選択
  - HTTPS ダウンロード、SHA-256 検証、実行権限設定、バージョン検証
  - `--force` による再取得
- `tools/rulesync.py`
  - 固定版バイナリの存在確認
  - CLI 引数の透過転送
  - 終了コード・標準出力・標準エラーの透過
  - 未導入時の `install_rulesync.py` 案内
- `tests/test_rulesync_toolchain.py`
  - OS・CPU マッピング、未対応環境、設定読込、検証失敗時の挙動をネットワークなしで検査

### 更新するファイル

- `.gitignore`: `.tools/` を追加し、取得したバイナリをコミットしない。
- `init.py`: 初期セットアップ後に案内する Rulesync コマンドを Python ラッパーへ変更する。
- `manifest.md`、`tools/README.md`: 固定版ツールチェーンと取得・実行ラッパーの役割を追加する。
- `docs/ja/dna-kernel/README.md`、`docs/en/dna-kernel/README.md`: 日常操作を日本語正本から英語副本へ同期する。
- `docs/ja/dna-kernel/onboarding.md`、`docs/en/dna-kernel/onboarding.md`: Node.js / Corepack を前提にしない初回取得、dry-run、生成、check の順へ更新する。
- `.rulesync/skills/project-onboarding/SKILL.md`、`.rulesync/skills/user-locale/SKILL.md`: 正本側のコマンドを更新する。生成済みの `.agents/`、`.claude/`、`.cursor/` は直接編集しない。
- 必要に応じて `.rulesync/rules/concepts.md` の「Rulesync の導入・固定版・生成確認」への参照を更新する。ただし概念正本に手順本文を重複させない。

### 日常コマンド

```bash
# 初回取得または壊れたキャッシュの修復
python tools/install_rulesync.py

# 生成内容を確認
python tools/rulesync.py generate --dry-run

# 生成
python tools/rulesync.py generate

# 正本と生成物の整合確認
python tools/rulesync.py generate --check

# user-locale の副本を会話言語設定に同期
uv run python tools/kernel/user_prefs.py sync
```

`tools/rulesync.py` は自動的に最新版へ更新せず、設定された v15.0.1 だけを実行します。Rulesync の版を更新するときは、資産・SHA-256・生成差分を改めて確認します。

## 実装フェーズ

### 1. 固定ツールチェーンの仕様確定

- [x] v15.0.1 の 5 資産、URL、SHA-256、キャッシュ配置を設定ファイルへ定義する。
- [x] `platform.system()` / `platform.machine()` の実値を OS・CPU キーへ正規化する。
- [x] Unix の実行権限、Windows の `.exe`、未対応環境のエラー文を仕様化する。
- [x] バイナリを Git 管理せず、初回取得時だけリポジトリ外キャッシュへ置くことを明記する。

### 2. Python 取得・実行ラッパーの実装

- [x] 参照実装の取得・SHA-256・`--version` 検証・一時ファイル置換を移植する。
- [x] OS・CPU 別設定の選択と、対応外環境の安全な失敗を実装する。
- [x] 実行ラッパーが全引数と終了コードを透過することを実装する。
- [x] 取得済みキャッシュの再検証を毎回行い、壊れたキャッシュを再取得できるようにする。
- [x] 参照実装の `agentsmd` 専用通知フィルタは、現行 target に `agentsmd` がないため持ち込まず、必要になった時点で別途判断する。

### 3. テストの追加

- [x] 対応する 5 組み合わせが正しい資産へ解決されることをテストする。
- [x] `x86_64` / `amd64` / `aarch64` / `arm64` などの代表的な CPU 名を正規化することをテストする。
- [x] 未対応 OS・CPU ではダウンロードせず、終了コード付きで案内することをテストする。
- [x] SHA-256 不一致、`--version` 不一致、キャッシュ再利用・`--force` の挙動をネットワークなしでテストする。
- [x] Python の通常テストを実行し、終了コード 0 を確認する。

### 4. コマンド・ドキュメントの移行

- [x] 既存の `corepack pnpm dlx rulesync` 参照を、初回取得・dry-run・generate・check の新手順へ更新する。
- [x] `uv run python tools/kernel/user_prefs.py sync` を generate 後に実行する現行ルールを維持する。
- [x] `delete: false` を採用し、生成物の自動削除を別作業に分離する方針と、生成物を直接編集しない原則を反映する。
- [x] 日本語正本を先に更新し、英語 docs を同じ相対パスへ同期する。
- [x] 参照ブランチの `sync_rules.py` は、現行リポジトリに旧コマンド利用箇所がないため初期導入では追加しない。互換入口が必要になった場合のみ追加する。

### 5. v15.0.1 生成結果の検証

- [x] 現在の `rulesync.jsonc`（`claudecode`、`cursor`、`codexcli`、`rules`、`skills`）を v15.0.1 で dry-run する。
- [ ] 未実施: 既存の 16.13.0 生成物との差分を一時ディレクトリで比較し、意図しない target・feature 欠落を確認する。
- [x] v15.0.1 で `generate` と `generate --check` を実行する。
- [x] generate 後に user-locale sync を行い、`.claude/` と `.cursor/` の副本が期待どおり残ることを確認する。
- [x] 実装・テスト・文書・生成確認の結果を査証ログへ追記する。

## 受け入れ条件

- Node.js、npm、pnpm、Corepack が未導入でも、対応 OS・CPU 上で Python から v15.0.1 を取得・検証・実行できる。
- `python tools/rulesync.py --version` 相当の実行で `15.0.1` を確認できる。
- `generate --dry-run`、`generate`、`generate --check` が現行 target / feature 設定で成立する。
- SHA-256 不一致や未対応環境を成功扱いにしない。
- バイナリは Git 管理されず、固定 URL・固定 SHA-256・固定版から再現できる。
- Python ツールのテスト、既存テスト、計画書の進捗チェックが終了コード 0 になる。
- docs は `docs/ja/` を編集正本、`docs/en/` を同期副本として整合している。

## リスクと判断

- Rulesync v15 と v16 では生成物の仕様差があり得るため、実装後に生成物差分を確認する。差分がある場合は、v15 採用に伴う意図的差分として記録する。
- v15.0.1 が公式に提供する資産は 5 組み合わせのため、Windows arm64 などを無理にエミュレーションせず、初期対応外として明示する。
- SHA-256 は `SHA256SUMS` の取得結果をそのまま実行時に信頼するのではなく、設定へ固定した値と比較する。更新時だけリリース資産と照合する。
- `delete: false` を採用した。user-locale sync 後も `generate --check` が副本を削除対象にしないため、通常生成と整合確認を安全に連続実行できる。不要な生成物の削除は対象を確認した別作業とする。
- 参照ブランチは Windows x64 を前提としているため、macOS / Linux の実機または CI マトリクスで各バイナリの起動確認を行う。

## 変更履歴

| 日付 | バージョン | 変更内容 |
|---|---|---|
| 2026-08-18 | 1.0 | Rulesync v15.0.1固定版のPythonラッパー導入計画を作成。 |

## 進捗

- [x] 作業前の必須ファイル、既存計画書、未コミット変更を確認した。
- [x] 参照ブランチの固定版取得・実行方式を確認した。
- [x] v15.0.1 の公式資産と SHA-256 を確認した。
- [x] 現行 dna_kernel の Rulesync 設定、コマンド参照、生成後 sync の依存関係を確認した。
- [x] 固定版ツールチェーンの仕様を実装する。
- [x] Python 取得・実行ラッパーと対応テストを実装する（ユニットテスト33件が成功）。
- [x] コマンド・ドキュメント・正本スキルを新方式へ移行する。
- [x] v15.0.1 の現行ホスト（darwin-x64）で取得・`--version`・dry-run・generate・`generate --check`・user-locale sync を検証する。
- [ ] Windows x64、macOS arm64、Linux x64/arm64 の各実機またはCI環境で、取得後のネイティブ起動検証を追加実施する。
