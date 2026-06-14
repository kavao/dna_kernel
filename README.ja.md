# dna_kernel

![dna_kernel — Self-Evolving Rule Governance](images/title.png)

[English](README.md) · 日本語

dna_kernel は、LLM ハーネスを使う創作・開発プロジェクトに、
自己発展型ルールガバナンスを注入するための最小カーネルです。

主な役割:

- `.rulesync/` にルールとスキルの正本を置く
- rulesync で各 LLM ツール向け設定を生成する
- `_workingspace/` に査証ログ・日記・計画を残す
- `tools/kernel/` の小さな実働ツールで完了確認を支える

詳しい導入・注入手順:

- [Documentation (EN)](docs/en/dna-kernel/README.md)
- [ドキュメント（日本語）](docs/ja/dna-kernel/README.md)

## 謝辞

このプロジェクトは、複数の LLM ツール向け設定を `.rulesync/` から生成する [rulesync](https://github.com/dyoshikawa/rulesync) を利用しています。  
作者の [dyoshikawa](https://github.com/dyoshikawa) さんに感謝します。
