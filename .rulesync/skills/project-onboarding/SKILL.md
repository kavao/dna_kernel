---
name: project-onboarding
description: "新規プロジェクトへ dna_kernel を導入し、overview.md を起点に作業支援スケルトンを立ち上げる"
targets: ["*"]
---

## 目的

新しいプロジェクトで dna_kernel を使い始めるときに、最初の会話と初期化を迷わせない。
`overview.md` をプロジェクト概要の正本候補として作り、rulesync・uv・ワークスペースを整えてから、プロジェクト内容を聞く。

## 適用する場面

- ユーザーが新規プロジェクトへ dna_kernel を導入したいと言ったとき
- ルールやスキルはあるが、プロジェクト概要がまだ見当たらないとき
- 「開発を進める際の支援スケルトン」を作る依頼を受けたとき

## 適用しない場面

- dna_kernel 本体を開発・修正しているとき
- ユーザーが明示的に「DNA_KERNEL 開発モード」と言ったとき
- 既存の `overview.md` があり、ユーザーが通常の作業を依頼しているとき

## 基本フロー

### 1. overview.md の有無を確認する

プロジェクトルートで `overview.md` を探す。

存在する場合:

- 内容を読み、プロジェクトの目的・制約・現在地を短く要約する。
- 不足があれば、必要な最小限の質問だけを行う。

存在しない場合:

- `overview.md` を作成するかユーザーに確認する。
- 作成しないと言われた場合は、導入作業を止め、通常の依頼として扱う。

確認文の例:

```text
このプロジェクトには overview.md がまだありません。プロジェクト概要の正本として作成しますか？
```

### 2. rulesync と uv の導入状況を確認する

`overview.md` を作成する了承を得たら、次を確認する。

```bash
npx rulesync --version
uv --version
```

未導入または実行できないものがある場合は、導入案を提示してから明示了承を得る。

導入案の例:

```text
rulesync または uv が未導入です。初期化に必要なので、こちらで導入してよいですか？
実行予定:
- npm install -g rulesync
- uv の公式インストーラを実行
- uv run python init.py
- npx rulesync generate --dry-run
- npx rulesync generate
```

### 3. 了承後に自動導入する

ユーザーが明示的に了承したら実行する。

推奨順:

Windows PowerShell:

```powershell
npm install -g rulesync
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
uv run python init.py
npx rulesync generate --dry-run
npx rulesync generate
```

macOS / Linux:

```bash
npm install -g rulesync
curl -LsSf https://astral.sh/uv/install.sh | sh
uv run python init.py
npx rulesync generate --dry-run
npx rulesync generate
```

既に導入済みのコマンドは再導入しなくてよい。
uv インストール直後に `uv` が見つからない場合は、PATH 反映のために新しいシェルで再確認する。
実行後は、生成先と終了コードを確認してから次へ進む。

### 4. プロジェクト内容を聞く

導入・初期化が終わってから、どのようなプロジェクトかを聞く。
最初の質問は絞る。

質問例:

```text
このプロジェクトでは、何を作る・進める予定ですか？
分かる範囲で、目的、成果物、守りたい制約を教えてください。
```

必要に応じて追加で聞く項目:

- 成果物の種類
- 想定ユーザーまたは読者
- 使う技術・ツール
- 変更してはいけない制約
- 完了確認の方法

### 5. overview.md を作成する

回答をもとに、`overview.md` を作成する。
初期テンプレート:

```markdown
# Project Overview

## 目的

未定

## 成果物

未定

## 制約

未定

## 作業方針

- 正本を先に更新し、派生物は再生成する。
- ファイル保存と確認が終わるまで完了扱いにしない。

## 完了確認

未定
```

作成後は読み直して保存確認を行い、更新ファイルパスを報告する。

## DNA_KERNEL 開発モード

dna_kernel 本体を直していると判断できる場合は、このスキルの質問フローを使わない。

判断例:

- `.rulesync/` のルールやスキルを修正する依頼
- `README.md` や `manifest.md` の導入説明を直す依頼
- `tools/kernel/` や `init.py` を修正する依頼

この場合は、既存ファイルを読んで直接修正し、必要に応じて `npx rulesync generate --dry-run` または `npx rulesync generate --check` で確認する。

## 関連

- 概念正本: `rules/concepts.md`（プロジェクト導入モード、DNA_KERNEL 開発モード）
- 承認フロー: `skills/approval-flow/SKILL.md`
- 出力規律: `skills/output-discipline/SKILL.md`
