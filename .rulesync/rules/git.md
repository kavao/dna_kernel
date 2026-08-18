---
targets: ["claudecode", "cursor"]
description: "git 運用ルール（コミットメッセージ等）"
globs: ["**/*"]
---

# git 運用ルール

## コミットメッセージ

### 言語

- **git に記録するコミットメッセージは、常に英語で書く**（決め打ち）。話者の会話言語に合わせて日本語等にしない。
- ユーザーへメッセージ案を提示するときは、**英語のコミット本文の直下**に、話者の**会話言語（ネイティブ言語）**での説明を付ける。説明は `git commit` には含めない（確認・理解用）。
- 会話言語の解決は `skills/user-locale/SKILL.md` と同じ優先順位（チャット明示 → local → ホーム config → OS locale）。
- **docs の編集正本**（`docs/ja/` 等）や **ハーネス正本**（`.rulesync/` の日本語）とは別。コミットは git 履歴用の英語ログ、会話言語の説明はその場の補助。

### 形式（git に記録する英語）

- 1行目（subject）は変更の要旨を簡潔に（約 50〜72 文字目安）
- 複数の変更を含む場合は、1行目の後に空行を入れてから箇条書きで内訳を書く（英語）
- ユーザーからコミットメッセージ案を聞かれた場合は、**英語の 1行案**と**英語の複数行案**の両方を提示し、その**下**に会話言語での説明を付ける

### 形式の例（git commit 用・英語）

```
feat: add user_prefs and locale skills for conversation language

- Add tools/kernel/user_prefs.py with init-config, show, and sync
- Add user-locale and content-placement skills under .rulesync/
- Document home config in docs/ja and docs/en onboarding
```

### 提示の例（日本語話者への案）

git に入れる英語:

```
feat: add GitHub Actions workflow for unit tests

- Add .github/workflows/test.yml for Python 3.11 and 3.12
- Document test command in code-testing skill
```

その下に会話言語（日本語）での説明:

```
（説明・日本語）
GitHub Actions で unittest を回す CI を追加しました。
Python 3.11 / 3.12 で同じコマンドを実行します。
```

### プレフィックス（任意）

変更の種類を先頭に付けると分類しやすい。

| プレフィックス | 用途 |
|--------------|------|
| `docs:` | ドキュメントの追加・更新 |
| `feat:` | 新機能・新スクリプトの追加 |
| `fix:` | バグ修正・誤記修正 |
| `refactor:` | リファクタリング（動作変更なし） |
| `chore:` | 設定ファイル・依存関係の更新 |
| `rules:` | `.rulesync/` 内のルール・スキル変更 |

プレフィックスは省略してもよい。付ける場合は一貫して使い続ける。

## ブランチ運用

プロジェクト側で決める。最低限の指針として:

- `main` / `master` には直接コミットしない（チーム運用の場合）
- 作業ブランチは `feat/`, `fix/`, `chore/` などプレフィックスで分類する
- ルール・スキルの変更は `rules/` ブランチで行い、動作確認後にマージする
