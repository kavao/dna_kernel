# dna_kernel

![dna_kernel — Self-Evolving Rule Governance](images/title.png)

English · [日本語](README.ja.md)

dna_kernel is a minimal kernel for injecting self-evolving rule governance into creative and development projects that use LLM harnesses.

It is not a standalone application. Copy or integrate it into an existing repository as a rule system that combines canonical rules, AI procedures, generated tool-specific settings, completion checks, and work evidence.

With one canonical source, switching between Codex, Claude Code, Cursor, Grok Build, and similar tools costs less: teams do not need to repeat the same rules and completion conditions or maintain separate instruction files by hand. Rulesync 15.0.1 recognizes the `grokcli` target and can generate `.grok/skills/`; whether a specific Grok Build environment consumes that location must still be verified in the host repository.

Main benefits:

- Generate settings for multiple AI tools from `.rulesync/` sources
- Keep evidence for completion through saved files, machine checks, and checklists
- Track work facts in append-only audit logs
- Operate daily Rulesync generation without Node.js, using a Python-standard-library-centered setup

Start with the [onboarding and injection flow](docs/en/dna-kernel/onboarding.md) to choose an adoption profile.

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
