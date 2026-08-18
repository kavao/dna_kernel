# dna_kernel onboarding and injection

English · [日本語](../../ja/dna-kernel/onboarding.md)

dna_kernel supports three work modes:

| Mode | Purpose | README handling |
|------|---------|-----------------|
| New project setup | Bootstrap a location without overview or README yet | Ask before creating a project README |
| Existing project injection | Add dna_kernel to an existing project | Do not touch the existing README; put dna_kernel docs under `docs/ja/dna-kernel/` and `docs/en/dna-kernel/` |
| DNA_KERNEL development | Modify the dna_kernel package itself | Skip onboarding questions; edit directly |

## Adoption profiles and tool switching

Choose the smallest scope that fits the host repository:

| Profile | Scope | Best for |
|---|---|---|
| Rule-only | Canonical rules, Rulesync config/wrappers, and generated settings for AI tools | Aligning instructions across Codex, Claude Code, Cursor, and similar tools |
| Governance | Rule-only plus completion discipline, plan checks, audit logs, and `_workingspace/` | Keeping evidence for completion and work history |
| Full | Governance plus onboarding, user-locale, and selected helper skills/tools | Multi-person, multi-machine, or multi-tool operation |

Because settings come from one canonical source, switching tools costs less: rules, completion conditions, plan state, and conversation language do not need to be re-explained each time. The current standard targets are `claudecode`, `cursor`, `codexcli`, and `grokcli`. Rulesync 15.0.1 generates `.grok/skills/` for `grokcli`; verify actual Grok Build consumption in the host repository.

## Existing project injection

Preserving the existing layout takes priority.

When the user specifies an injection root directory, treat that directory as the root.
Do not automatically expand to a monorepo parent or Git root.

Example:

```text
K:\projects\my-app\packages\discord-bot\
```

If that path is given, place the following under `packages/discord-bot/`:

```text
.rulesync/
rulesync.jsonc
config/rulesync_toolchain.json
docs/ja/dna-kernel/
docs/en/dna-kernel/
tools/install_rulesync.py
tools/rulesync.py
tools/kernel/
_workingspace/
```

Principles:

- Do not overwrite the existing `README.md`
- Do not copy `images/title.png` into the host project; it is for the dna_kernel repository README title only
- Review `.gitignore`, `pyproject.toml`, `tools/`, and `docs/` before appending
- Put detailed dna_kernel docs in `docs/ja/dna-kernel/` (source) and sync `docs/en/dna-kernel/` (translation)
- Add `.rulesync/`, `rulesync.jsonc`, `config/rulesync_toolchain.json`, `tools/install_rulesync.py`, `tools/rulesync.py`, and `tools/kernel/` as canonical sources and working tools
- Ignore rulesync outputs (`.claude/`, `.cursor/`, `.codex/`, `.agents/`, `.grok/`, `.kilo/`, `AGENTS.md`, `CLAUDE.md`)

The dependency baseline is Python `>=3.11` with standard-library-centered kernel tools. uv is recommended but optional, and Node.js, npm, pnpm, and Corepack are not required for daily Rulesync generation. The Rulesync binary and network are needed only for the first download or a version update.

Recommended flow:

1. Check for existing README, docs, tools, `.rulesync/`, and `rulesync.jsonc`
2. Present the Rule-only / Governance / Full profile choice
3. Present the planned changes and obtain approval
4. Place docs in `docs/ja/dna-kernel/` and sync English under `docs/en/dna-kernel/`
5. Add or merge `.rulesync/` and `rulesync.jsonc`
6. Add required tools under `tools/kernel/`
7. Update `.gitignore` for rulesync outputs, the Rulesync cache, and `_workingspace/`
8. Run `python tools/install_rulesync.py` to download and verify Rulesync 15.0.1
9. Run `python tools/rulesync.py generate --dry-run` and review the output
10. After approval, run `python tools/rulesync.py generate`
11. Run `python tools/rulesync.py generate --check` and `uv run python tools/kernel/user_prefs.py sync`
12. If needed, ask whether to create `overview.md` and gather project purpose, deliverables, and constraints

## New project setup

First check whether `overview.md` exists.
If not, ask before creating it, then confirm rulesync and uv setup after approval.

Basic commands:

```bash
uv run python init.py
python tools/install_rulesync.py
python tools/rulesync.py generate --dry-run
python tools/rulesync.py generate
python tools/rulesync.py generate --check
uv run python tools/kernel/user_prefs.py sync
```

The Python wrapper downloads and verifies the official Rulesync 15.0.1 binary.
Node.js, npm, pnpm, and Corepack are not required for daily generation. Use the `generate` subcommand to produce outputs, then run `generate --check` and `user_prefs.py sync` **after** `generate`.

Check plan and design-document progress:

```bash
uv run python tools/kernel/plan_check.py _workingspace/plans
```

Plans and design documents also include a `Version: MAJOR.MINOR` header and an append-only `## Change History` section in addition to progress checkboxes. When updating a plan, increment the version, append the change to the history, and then run the check.

## Conversation language and home config

**Conversation language** (chat with the LLM) is separate from **docs editorial source** (`docs/ja/` then sync to `docs/en/`). Even when chatting in Japanese, follow the bilingual docs policy in `docs-writing`.

| Setting | Location | In git |
|---------|----------|--------|
| Conversation language and authoring defaults | `~/.config/dna-kernel/config.toml` | No (per machine) |
| Project override | `.dna-kernel.local.toml` | No (gitignore) |
| API keys, secrets | `.env` | No |

Create the home config template:

```bash
uv run python tools/kernel/user_prefs.py init-config
```

Check resolved conversation language:

```bash
uv run python tools/kernel/user_prefs.py show conversation.language
```

Before writing files, declare placement with the `content-placement` skill (use together with `user-locale`).

## .gitignore example

```gitignore
# rulesync outputs
# Canonical sources live in rulesync.jsonc and .rulesync/; exclude generated tool configs
.claude/
.cursor/
.codex/
.kilo/
.agents/
.grok/
AGENTS.md
CLAUDE.md

# workspace (plans are shared; logs and diary remain local)
_workingspace/**
!_workingspace/**/
!_workingspace/**/.gitkeep
!_workingspace/plans/
!_workingspace/plans/*.md
_backup/
_old/

# pinned Rulesync cache (downloaded by the Python wrapper)
.tools/

# user-locale: project-local override
.dna-kernel.local.toml
```
