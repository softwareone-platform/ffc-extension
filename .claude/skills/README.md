# Claude Code skills

Lazy-loaded skills for Claude Code sessions in this repo. Each `SKILL.md`
layers code recipes and Claude-coaching metadata on top of the canonical
project documentation at [`../../docs/conventions/`](../../docs/conventions/).

Audience for this README: **skill maintainers**. Daily contributors browse
`docs/conventions/` instead. Claude Code loads skills by matching the
`description:` frontmatter against the user's task — not by reading this file.

## Skills in this repo

The `mpt-*` skills are **portable across MPT frontend projects** — they contain no project-specific concrete values. Project bindings (alias names, CSS prefix, wrapper paths, entity list) live in a sibling **project-local skill** (`ffc-local` in this repo; `vikings-local` / `<project>-local` in another).

| Skill                                              | Triggers on                                                                                 | Layered on top of                                                                                                                                           |
| -------------------------------------------------- | ------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [`mpt-frontend-standards/`](mpt-frontend-standards/SKILL.md) | Any frontend code touch that isn't clearly POC, test, or DS-component work                 | All of [`docs/conventions/*`](../../docs/conventions/) + the active project's `*-local`. Adds TS derivation discipline, Fast-Refresh file-split, verification commands, extraction thresholds, post-task test prompt. |
| [`mpt-design-system/`](mpt-design-system/SKILL.md)         | Any task touching `@swo/design-system/*` imports or the project's shared DS wrappers        | [`docs/conventions/design-system.md`](../../docs/conventions/design-system.md) + [`design-system-components.md`](../../docs/conventions/design-system-components.md) + [`modals.md`](../../docs/conventions/modals.md) + the active project's `*-local`. Adds wrapper-first ordering, composition coaching, gap-table workflow, when-to-promote-to-shared-wrapper. |
| [`mpt-poc-builder/`](mpt-poc-builder/SKILL.md)             | Prototyping a dashboard, tab, panel, grid, chart, side-nav, filter sidebar, mock-driven view | [`docs/conventions/design-system.md`](../../docs/conventions/design-system.md), [`design-system-components.md`](../../docs/conventions/design-system-components.md), [`api-hooks.md`](../../docs/conventions/api-hooks.md), [`modals.md`](../../docs/conventions/modals.md) + the active project's `*-local`. Adds feature folder layout, mock data layer, 12-column panel grid, scaling patterns, POC checklist, iteration rhythm. |
| [`mpt-module-testing/`](mpt-module-testing/SKILL.md)       | Writing or refactoring a `*.spec.{ts,tsx}` for an MPT frontend                              | [`docs/conventions/testing.md`](../../docs/conventions/testing.md) + the active project's `*-local`. Adds spec-file layout, Grid wrapper / Container / Modal callback / mutation-controller / Wizard-step recipes, the `<Link>`-router gotcha, AAA structure, final-pass coaching. |
| [`ffc-local/`](ffc-local/SKILL.md)                 | **Always loads with any frontend task in this repo**. Resolves project-specific concrete values the `mpt-*` skills reference abstractly. | Project-specific knowledge only — no doc layer below. In another MPT project this file is replaced by that project's own `*-local` skill. |

Workflow skills (branches, PRs, backports, JIRA, devcontainer) live in a
separate plugin: [`mpt-ignite-skills`](../../../mpt-skills/plugins/mpt-ignite-skills/).
Those are code-shipping skills; the three in this folder are code-writing
skills.

## Drift precedence

**[`docs/conventions/*`](../../docs/conventions/) wins on drift.** If a
skill contradicts a convention doc, the doc is right and the skill is stale.
The [`.github/copilot-instructions.md`](../../.github/copilot-instructions.md)
inline mirrors are the lowest priority — they exist because Copilot can't
lazy-load skills, and they're explicitly flagged with "when updating a rule,
edit all three."

Chain:

```
docs/conventions/*.md         (human-authored, team-wide, wins on drift)
  └── .claude/skills/*/SKILL.md   (Claude-only, layers recipes + coaching)
        └── .github/copilot-instructions.md   (Copilot-only inline mirror)
```

## Adding a new skill

1. Create `.claude/skills/<name>/SKILL.md` with frontmatter:
   ```yaml
   ---
   name: <skill-name>
   description: <one line that Claude Code matches against user tasks>
   ---
   ```
2. If the content overlaps a `docs/conventions/*` doc, open with a
   pointer at the top: "Canonical rules live in `docs/conventions/<topic>.md` —
   that doc wins on drift. This skill layers X on top."
3. If the skill introduces a **new** canonical topic humans should see,
   promote it to `docs/conventions/` first; the skill then defers.
4. **If the skill is portable across MPT projects, keep concrete values
   out.** Reference the project's `*-local` skill for anything repo-specific
   (aliases, paths, entity names). Mark it `mpt-*` only when it's truly MPT-wide.
5. Add a row to the table above.
6. If humans need to know the skill exists, link it from
   [`../../AGENTS.md`](../../AGENTS.md).

## Porting to another MPT project

1. Copy the four `mpt-*` skills verbatim (they contain no ffc specifics).
2. Write a `<project>-local` SKILL.md with that project's aliases, CSS
   prefix, shared wrapper paths, entity list, test-utils inventory,
   i18n namespaces, scripts. Use [`ffc-local`](ffc-local/SKILL.md) as the
   template.
3. Rewrite `docs/conventions/*.md` for that project (the convention docs
   are project-maintained canonical).

## Updating a rule

- **Canonical topic (naming, api-hooks, i18n, modals, design-system, testing):**
  edit `docs/conventions/<topic>.md` first. Then propagate down to any SKILL
  pointer wording and (for testing) the Copilot inline mirror.
- **Skill-only content (recipes, scaling patterns, iteration rhythm, POC
  checklist, Claude coaching):** edit the SKILL only. These have no
  convention doc counterpart by design.
