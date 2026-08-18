# dna_kernel overview

English · [日本語](../../ja/dna-kernel/README.md)

dna_kernel is a minimal kernel for injecting **self-evolving rule governance** into creative and development projects that use LLM harnesses (Claude Code, Cursor, and similar tools).

The root `README.md` belongs to the host project.
Detailed dna_kernel documentation lives under `docs/en/dna-kernel/` (English, default display) and `docs/ja/dna-kernel/` (Japanese editorial source).

## Who it is for

dna_kernel is for teams that use several LLM tools in an existing development or creative repository, such as Codex, Claude Code, and Cursor. Injecting dna_kernel into the host repository reduces the need to repeat rules in each tool conversation or maintain separate instruction files by hand.

Status per AI tool:

| Tool | Rulesync target | Generation | Actual consumption |
|---|---|---|---|
| Claude Code | `claudecode` | Supported | Confirmed* |
| Cursor | `cursor` | Supported (Rulesync standard target) | Not verified |
| Codex CLI | `codexcli` | Supported (Rulesync standard target) | Not verified |
| Grok Build | `grokcli` | Supported (generates `.grok/skills/`) | Not verified (verify in the host repository) |

\* Confirmed as of 2026-08-18: the Claude Code session that authored this table is itself running on the generated `CLAUDE.md` (this session's `CLAUDE.md` and `.claude/rules/` were regenerated to include these edits; recorded in `_workingspace/log/202608.md`). Verify again in other host repositories.

Being able to generate a file is not the same as a tool actually reading it. Review this table whenever a target is added or updated.

## What it provides

| Problem | After adoption | Where to verify |
|---|---|---|
| Rules diverge between tools | Generate settings from `.rulesync/` sources | `AGENTS.md`, `CLAUDE.md`, `.cursor/`, and similar outputs |
| Completion claims lack evidence | Require saved files, reloads, and machine checks | `generate --check`, `plan_check.py` |
| Work history can be rewritten | Keep append-only audit logs | `_workingspace/log/` |
| Detailed plan status drifts | Check `[ ]` / `[x]`, versions, and change history | `_workingspace/plans/` |
| Each tool requires a separate environment | Generate with a Python-standard-library-centered setup | `tools/`, `config/` |

## Adoption profiles

Start with only the scope the host repository needs:

- **Rule-only**: unify canonical rules and settings for AI tools
- **Governance**: add completion checks, plan checks, and audit logs
- **Full**: also use onboarding, conversation-language, and related synchronization helpers

See [`manifest.md`](../../../manifest.md) and [onboarding.md](onboarding.md) for the concrete copy set for each profile.

## Dependencies

- Python `>=3.11` is the baseline. The main kernel tools have no external Python packages.
- uv is a recommended execution helper, but standard-library tools can also run with `python`.
- Node.js, npm, pnpm, and Corepack are not required for daily Rulesync generation.
- The Rulesync binary and network access are needed for the first download or a version update. Later runs use the `.tools/` cache.

Conversation language is resolved in this order: explicit chat instruction, project-local config, home config, then OS locale. Project-specific overrides live in `.dna-kernel.local.toml` and are not committed.

## Why it exists

The more instructions you add for an LLM, the more contradictions accumulate—and “done” spoken in chat is not evidence of completion.
This kernel addresses both problems structurally:

- **Single source of rules**: Put conceptual definitions in one place; other instructions reference them
- **Completion constraints**: Do not treat work as done until files are written and verified
- **Append-only history**: Audit logs forbid overwrites so work facts cannot be rewritten

## What the kernel includes

```text
dna_kernel/
  README.md                  ← short entry (English, default display)
  README.ja.md               ← short entry (Japanese, editorial source)
  manifest.md                ← file roles and transplant paths
  rulesync.jsonc             ← rulesync config (targets, features)
  .rulesync/
    rules/                   ← canonical concepts and governance rules
    skills/                  ← LLM execution procedures
  docs/
    README.md                ← documentation index (EN links first)
    en/dna-kernel/           ← English (default display, translation)
    ja/dna-kernel/           ← Japanese (editorial source)
  config/
    rulesync_toolchain.json  ← pinned Rulesync 15.0.1 assets and SHA-256
  tools/
    README.md
    install_rulesync.py      ← download and verify the pinned binary
    rulesync.py              ← execute the pinned binary
    kernel/
      workspace_audit_log.py
      json_weighted_pick.py
```

## README handling

In a host project, keep the root `README.md` for that project’s own introduction and usage.
Place dna_kernel docs under `docs/ja/dna-kernel/` and `docs/en/dna-kernel/` without moving or overwriting the host README.

For new projects without a README, ask whether to create one before proceeding.

## Common commands

Initial setup:

```bash
uv run python init.py
```

Regenerate rules:

```bash
python tools/install_rulesync.py
python tools/rulesync.py generate --dry-run
python tools/rulesync.py generate
python tools/rulesync.py generate --check
uv run python tools/kernel/user_prefs.py sync
```

Rulesync 15.0.1 is downloaded and verified by the Python wrapper. Node.js, npm, pnpm, and Corepack are not required for daily generation. The downloaded binary is stored under `.tools/` and is not tracked by Git.

Append an audit log entry:

```bash
uv run python tools/kernel/workspace_audit_log.py append "work summary"
```

## Further reading

- Onboarding and injection: [onboarding.md](onboarding.md)
- Governance pattern: [self-evolving-governance.md](self-evolving-governance.md)
- File manifest: [../../../manifest.md](../../../manifest.md)
