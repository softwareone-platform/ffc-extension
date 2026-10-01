# Documentation

Navigation index for everything under `docs/`. Three groups: conventions
(how we write code), architecture (how things run), dev (how to set up).

For the AI-agent entry point — including precedence, skills, and workflow
pointers — see [`../AGENTS.md`](../AGENTS.md).

## Conventions (how we write code)

Human-authored, canonical. These win on drift against every AI skill and
Copilot instruction mirror.

| Doc                                    | What it covers                                                                 |
| -------------------------------------- | ------------------------------------------------------------------------------ |
| [`conventions/naming.md`](conventions/naming.md)             | Folder / file / hook / companion-file casing; path alias → folder mapping; rename recipe. |
| [`conventions/api-hooks.md`](conventions/api-hooks.md)       | `useFooApi.tsx` vs `useFooDetailsApi.ts`; stable `["<Entity>", "Details", id]` query-key shape; `api/` barrel layout. |
| [`conventions/i18n.md`](conventions/i18n.md)                 | `useFixedT`, `:` key separator, `<feature>` / `shared` namespaces, snake_case vs camelCase leaf keys, dynamic-key enumeration, adding a locale. |
| [`conventions/modals.md`](conventions/modals.md)             | In-app modals, `useModalToggle` close contract, simple-form vs wizard flavours, `use<Entity>FormController` plumbing. |
| [`conventions/design-system.md`](conventions/design-system.md) | DS subpath imports (bundle size + mock resolution), verified DS gap table (multi-select, DonutChart height, strict `Icon.name`, etc.), icon-name hygiene, SCSS token vocabulary, `.ffc-*` shared classes, chart palettes. |
| [`conventions/testing.md`](conventions/testing.md)           | Jest stack facts, `.spec.tsx` / `.spec.mocks` layout, 85% coverage floor, DS full-path mocking + no-spread rule, pre-mocked modules, typed-spy table, `~test-utils/*` inventory, spec-scoped ESLint, when-not-to-test, test-name style. |

## Architecture (how things run)

| Doc | What it covers |
| --- | -------------- |
| [`architecture/mpt-host.md`](architecture/mpt-host.md) | Iframe-as-extension runtime, how the host bridge is detected, `useHasMPTHost` vs `useIsRootPage` (they are **not** interchangeable). |

## Dev (how to set up)

| Doc | What it covers |
| --- | -------------- |
| [`dev/devcontainer.md`](dev/devcontainer.md) | Devcontainer workflow (VS Code + JetBrains screenshots in `dev/images/`). |

## See also

- Root [`../README.md`](../README.md) — stack badges, run commands, repo layout.
- [`../AGENTS.md`](../AGENTS.md) — the AI-agent index (skills, workflow, precedence rules).
- [`../.claude/skills/`](../.claude/skills/) — Claude Code lazy-loaded skills that layer recipes on top of these conventions.
