# Self-evolving rule governance

English · [日本語](../../ja/dna-kernel/self-evolving-governance.md)

## What this is

An operating pattern for LLM-harness projects where **rules do not bloat or contradict**, **completion stays unambiguous**, and **history is not rewritten**.

Instead of relying on “keep saying it in chat and it will be followed,” three structures constrain LLM behavior.

## Three structures

### 1. Conceptual source (Policy-as-Code)

Put only “short definitions, prohibitions, and completion conditions” in `rules/concepts.md`.
Skills and other rules link to those concepts and describe “how they apply in this task” only.

**Effect**: Contradictions have one origin; change impact stays manageable.

For the difference between conversation language (home config) and editorial sources, see [Conversation language and home config in onboarding.md](onboarding.md#conversation-language-and-home-config).

### 2. Completion constraints

“Done” means the artifact exists on disk and is confirmed by re-read or automated verification.
Even if the LLM says it wrote something, do not treat the task as complete until write and verification finish.

**Effect**: Prevents “shown in chat but not saved” and “production run before dry-run.”

### 3. Progress checks for plans and design documents

Plans and design documents include a `## Progress` section and track progress with `- [ ]` / `- [x]` checkboxes. Leave work that is not started, in progress, partially complete, awaiting confirmation, or on hold as `[ ]`, with the remaining work explained. Use `[x]` only for completed work.

Detailed checklists under sections such as `## Implementation phases` are also progress records. Mark completed detailed items `[x]`, leave unfinished or awaiting-confirmation items `[ ]`, and keep the detailed states consistent with the `## Progress` summary.

After creating or updating a plan or design document, run the following machine check:

```bash
uv run python tools/kernel/plan_check.py _workingspace/plans
```

Pass a design-document file or directory as the argument when checking another location. Treat the work as complete only after confirming exit code 0.

**Effect**: Remaining and completed work stays readable in one format across sessions and computers.

Plans and design documents also include a `Version: MAJOR.MINOR` header and an append-only `## Change History` table. When a document changes, update the header version and append the date, version, and change description to the end of the history. `plan_check.py` checks the version format, the history table, and agreement between the header and the latest history row.

### 4. Append-only audit log

After work, append to `_workingspace/log/YYYYMM.md`. Overwrites and deletions are forbidden.
Using `workspace_audit_log.py` appends via a command that cannot alter existing lines.

**Effect**: Work facts remain; disputes over “did it or not” are reduced.

## How rules evolve

1. When a new work pattern appears, add a short definition to `concepts.md`
2. Replace duplicated text in skills and instructions with links to that definition
3. Record the change in the audit log

Repeating this makes the rule set **thinner as it grows**: concept text stays in one place; each skill only references it.

## LLM-assisted, user-governed rule growth

Users should not have to hand-classify Markdown rules every time. The LLM extracts repeated fixes, decisions, and project habits from conversation, implementation, and review, then checks scope and duplication against existing rules. The LLM must not save anything to Rulesync without approval.

When a candidate appears, make the choice explicit:

```text
Should this decision be saved to Rulesync?
Candidates: project rule / work skill / user setting / one-off (do not save)
```

Only after approval, update canonical sources according to `backup-before-edit` and `content-placement`, then run Rulesync generation, `generate --check`, relevant tests, and audit logging. Rejected or held candidates do not change persistent sources. “Learning” means saving approved knowledge to canonical sources and regenerating targets; it does not mean model retraining.

## Index and layered rules

`.rulesync/rules/agents.md` is the short entry point for shared `AGENTS.md`. It does not duplicate detailed rule bodies; it provides conditions, references, canonical sources, and completion checks. Keep one owner per shared entry point and explicitly separate standard rules with `targets` and `globs`.

During injection, inventory existing rules, skills, and generated outputs with Python, then register each item in an index route, as always-applicable, or as an explicit exclusion. Check that standard rules do not enter the shared entry point and that combined-target generation does not change content through last-writer-wins behavior. Generation confirmation and confirmation that Claude Code, Codex, Cursor, or another tool actually loaded the result are separate evidence.

## Temporary tools and compliant plugins

Create one-off investigation or measurement helpers in a Python-standard-library-only temporary directory or the Git-ignored `_workingspace/tmp-tools/`. Promote a tool to `tools/kernel/` only after reuse, input/output contracts, ownership, tests, dependencies, and Windows/macOS/Linux behavior are established. Optional functionality outside the standard profiles goes under `tools/plugins/` only after approval.

For promotion or plugin intake, verify the manifest, targets, canonical-source boundary, dependencies, tests, docs, and rollback. Do not make a tool permanent merely because it was convenient once, and do not add unapproved dependencies or generated outputs.

## Minimal kernel (what to transplant)

| Element | File | Role |
|---------|------|------|
| Concept source | `rules/concepts.md` | Unified definitions, prohibitions, completion conditions |
| Rule authoring | `rules/rule-authoring.md` | How to add rules without duplication |
| Plan/design check | `tools/kernel/plan_check.py` | Machine-check status formatting |
| Audit log | `tools/kernel/workspace_audit_log.py` | Append-only work record |
| Automated checks | `tools/kernel/novel_project_check.py` | Optional completion verification |

**Minimum**: Concept source plus audit log tool already helps.
Automated check tools strengthen completion constraints.

## What to put in LLM entry files

Add these two lines to `CLAUDE.md` / `AGENTS.md`:

```
- The rule source is `rules/concepts.md` (or the equivalent path after transplant). Update it first.
- After work, append to the audit log with `tools/kernel/workspace_audit_log.py`.
```

Then follow “completion conditions” and “audit log principles” in `concepts.md`.
