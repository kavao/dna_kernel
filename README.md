# dna_kernel

![dna_kernel — Self-Evolving Rule Governance](images/title.png)

English · [日本語](README.ja.md)

dna_kernel is a minimal kernel for injecting self-evolving rule governance into creative and development projects that use LLM harnesses.

Main roles:

- Keep canonical rules and skills in `.rulesync/`
- Generate per-tool configs with rulesync
- Record audit logs, diary entries, and plans under `_workingspace/`
- Support completion checks with small tools in `tools/kernel/`

Onboarding and injection guides:

- [Documentation (EN)](docs/en/dna-kernel/README.md)
- [ドキュメント（日本語）](docs/ja/dna-kernel/README.md)

## Acknowledgments

This project uses [rulesync](https://github.com/dyoshikawa/rulesync) to generate per-tool configurations from `.rulesync/`.  
Special thanks to [dyoshikawa](https://github.com/dyoshikawa), the author of rulesync.
