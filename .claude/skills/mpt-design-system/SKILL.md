---
name: mpt-design-system
description: Use @swo/design-system components (Grid, Modal, Panel, Charts, Chip, Popover, Icon, DatePicker, Navigation) and the ~shared/components/* wrappers around them. Covers assembly recipes, composition gotchas, when to reach for the shared wrapper vs the raw DS component, and the "if the DS doesn't fit, don't invent — ask or compose from primitives" rule. Use whenever a task touches @swo/design-system/* imports, feature-local chart / grid / panel compositions, or ~shared/components/{panel, charts, modal} wrappers — in POC work or production.
---

# MPT Design System usage

**Canonical rules live in two docs** — this skill defers to them on drift:

- [`docs/conventions/design-system.md`](../../../docs/conventions/design-system.md) — meta rules: subpath imports (bundle size + mock resolution), verified DS gaps + workarounds, icon-name hygiene, SCSS token vocabulary, `.ffc-*` layout classes, chart palettes.
- [`docs/conventions/design-system-components.md`](../../../docs/conventions/design-system-components.md) — component-specific usage recipes: Panel + KpiTile, Grid (in-memory with sort/filter), Modal (DS vs app wrapper), Charts (XyChart / DonutChart / ChartLegend with module-scope series), Multi-select composition, Navigation shell, Chip, DatePicker.

Modals have their own canonical doc at [`docs/conventions/modals.md`](../../../docs/conventions/modals.md) (`useModalToggle`, `use<Entity>FormController`, simple-form vs wizard layouts). Testing patterns for DS components live in [`docs/conventions/testing.md`](../../../docs/conventions/testing.md).

This skill layers Claude-level composition coaching on top: which wrapper to reach for first, how to compose multi-component widgets, how to spot DS-gap situations, and how to prepare a feature for the eventual real-API swap.

## Reach for the wrapper first, raw DS second

Order of preference when picking an import source:

1. **Shared wrapper** (`~shared/components/{panel, charts, modal, …}`) — these already apply the project's defaults (sizing, cancel/submit action buttons, SCSS tokens) and compose with `.ffc-*` layout classes. Use these in feature code.
2. **Raw DS subpath** (`@swo/design-system/<component>`) — reach for these when assembling a new composition the shared wrappers don't cover, or when writing a NEW shared wrapper. Never import from the root `@swo/design-system`.
3. **Compose from DS primitives** — only when the DS has no fitting component (see the gap table in [`design-system.md`](../../../docs/conventions/design-system.md)). The Multi-select recipe (Popover + Checkbox) is the canonical example.

If you're about to call `@swo/design-system/modal` directly from feature code, stop — go through `~shared/components/modal/Modal.tsx` instead.

## Composition patterns worth internalising

- **Chart series + colour arrays live at module scope.** amCharts rebuilds its root whenever `series` / `colors` identity changes — building them inside the component body tears down + rebuilds on every render. If two or more tabs declare the same series, lift them to a feature-local `chartConfig.ts` ([`mpt-poc-builder`](../mpt-poc-builder/SKILL.md) covers the scaling pattern).
- **Grid `fields` are mandatory for sort/filter.** `useGridInMemory` needs both `columns` (how to render) and `fields` (how to compare values). Forget `fields` and the grid renders but the toolbar can't sort. See the recipe in [`design-system-components.md`](../../../docs/conventions/design-system-components.md#in-memory-grid-with-initial-sort).
- **Grid `list` filter type compares as a string.** For a numeric column with named buckets (e.g. maturity level 0-4), use `type: "number"` and let the user sort / filter numerically — don't try `list` with stringified options.
- **DonutChart default height (`150`) is tiny.** In a wide panel pass `height={240}` or higher.
- **Navigation collapsed-by-default has no prop.** Mount a tiny helper that `requestAnimationFrame`s then clicks `[data-testid="navigation__collapse-button"]`. This hack is tracked in the DS gap table so it survives DS updates.

## When the DS doesn't fit

The gap table in [`design-system.md`](../../../docs/conventions/design-system.md#verified-ds-gaps-and-the-workarounds) is the canonical list of "the DS gives you X but not Y". If a situation matches an entry, use the workaround.

If you hit a gap **not** in the table:

1. Stop and ask the user — "The DS component gives you X but not Y — do you want a custom wrapper, a different DS recipe, or should we open a design-system request?"
2. If you build a workaround, **add a row to the gap table** so the next session doesn't rediscover it.

Never silently invent styles that mimic a DS component. If it looks like a `Navigation.CollapseButton` it must be one — otherwise raise it.

## When writing a NEW shared wrapper

If a composition pattern lives in a single feature today but will clearly reappear (e.g. a status chip with a trend arrow, a KPI tile with a sparkline), the threshold rules from [`mpt-frontend-standards`](../mpt-frontend-standards/SKILL.md) apply: promote to `~shared/components/*` on the second duplicate, not the first.

A new shared wrapper means:

1. Co-locate with existing wrappers (`~shared/components/<name>/`).
2. Export both the component and its props type (`export type FooProps = { … }`) so specs can derive via `ComponentProps<typeof Foo>`.
3. If the wrapper owns SCSS, use the project's token vocabulary — see [`design-system.md`](../../../docs/conventions/design-system.md#scss-token-vocabulary).
4. Add a short recipe to [`design-system-components.md`](../../../docs/conventions/design-system-components.md) so humans discover it.

## See also

- [`mpt-frontend-standards`](../mpt-frontend-standards/SKILL.md) — baseline conventions (path aliases, TS discipline, Fast Refresh, verification).
- [`mpt-poc-builder`](../mpt-poc-builder/SKILL.md) — POC-specific scaling patterns that build on DS components (chart config, `<MetricPanel>` extraction, filter sidebar wiring).
- [`mpt-module-testing`](../mpt-module-testing/SKILL.md) — how DS components are mocked in specs (full subpath, shared `~test-utils/mocks/designSystemGrid`, modal callback capture).
