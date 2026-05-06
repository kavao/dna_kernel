# dna_kernel

dna_kernel は、LLM ハーネスを使う創作・開発プロジェクトに、
自己発展型ルールガバナンスを注入するための最小カーネルです。

主な役割:

- `.rulesync/` にルールとスキルの正本を置く
- rulesync で各 LLM ツール向け設定を生成する
- `_workingspace/` に査証ログ・日記・計画を残す
- `tools/kernel/` の小さな実働ツールで完了確認を支える

詳しい導入・注入手順は [docs/dna-kernel/README.md](docs/dna-kernel/README.md) を参照してください。

