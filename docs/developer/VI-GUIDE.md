# Axiara VI Guide — Visual Identity for Diagrams & Assets

> Developer-facing spec. Source of truth for the look of Axiara's README
> diagrams, logos, and any new asset. Applies to everything under `assets/`.

---

## 1. Brand palette (light)

Semantic role → exact hex. These are the **only** colors allowed in diagrams.

| Role | Fill (block bg) | Border | Title text | Body text |
| --- | --- | --- | --- | --- |
| Brand / header (primary green) | `#E1F5EE` | `#1D9E75` | `#04342C` | `#0F6E56` |
| `main_db` / official baseline (green) | `#EAF3DE` | `#639922` | `#27500A` | `#3B6D11` |
| `learn_db` / learned reference (purple) | `#EEEDFE` | `#7F77DD` | `#3C3489` | `#534AB7` |
| `market_db` / market prices (amber) | `#FAEEDA` | `#BA7517` | `#633806` | `#854F0B` |
| Neutral (labels, arrows, captions) | — | `#888780` | `#888780` | `#888780` |

**Rule**: one diagram = header (brand green) + at most the four semantic
blocks. Do not introduce new hues.

## 2. Dark variants

Every light SVG ships a dark twin (`-dark.svg`). Exact palette mapping
(light → dark):

| Light | Dark | Use |
| --- | --- | --- |
| `#E1F5EE` | `#04342C` | header bg |
| `#1D9E75` | `#5DCAA5` | header border |
| `#04342C` | `#E1F5EE` | header title text |
| `#0F6E56` | `#9FE1CB` | header body text |
| `#EAF3DE` | `#173404` | green block bg |
| `#639922` | `#97C459` | green block border |
| `#27500A` | `#C0DD97` | green title text |
| `#3B6D11` | `#97C459` | green body text |
| `#F6F9EE` | `#0E2402` | green input/output bg |
| `#A8C97E` | `#618D3A` | green input/output border |
| `#EEEDFE` | `#26215C` | purple block bg |
| `#7F77DD` | `#AFA9EC` | purple block border |
| `#3C3489` | `#CECBF6` | purple title text |
| `#534AB7` | `#AFA9EC` | purple body text |
| `#F7F6FE` | `#1C1848` | purple input/output bg |
| `#B3ADEB` | `#7A71C9` | purple input/output border |
| `#FAEEDA` | `#412402` | amber block bg |
| `#BA7517` | `#EF9F27` | amber block border |
| `#633806` | `#FAC775` | amber title text |
| `#854F0B` | `#EF9F27` | amber body text |
| `#FDF6EA` | `#2F1B02` | amber input/output bg |
| `#D6A96B` | `#B97B2A` | amber input/output border |
| `#EFFAF6` | `#04241C` | review input/output bg |
| `#6EC6A6` | `#3E9C7D` | review input/output border |
| `#888780` | `#9E9D98` | labels / captions |

> ⚠️ **Generate, don't hand-edit**: run a placeholder two-phase swap (light →
> `__D0__`… → dark) — a naive one-pass `str.replace` chain re-maps
> `#E1F5EE → #04342C` and then `#04342C → #E1F5EE`, corrupting headers.
> In dark SVGs `#E1F5EE` legitimately remains as *title text* color.

## 3. Canvas & geometry

| Property | Spec |
| --- | --- |
| Width (all README diagrams) | `1280px` (img `width: 1280px`; viewBox `0 0 1280 …`) |
| Corner radius | `rx="10"` blocks, `rx="12"` headers |
| Border width | `stroke-width="1"` |
| Arrow marker | custom `#arrow` marker, `stroke="#888780"` (dark `#9E9D98`), `stroke-width="1.5"` |
| Padding | content inset ≥ 20px from viewBox edge |

## 4. Typography scale (README diagrams)

Font sizes are tuned so that, at 1280px display width, text reads as large as
the architecture diagram (a 680px viewBox stretched ~1.88×). Approved scale:

| Role | Size |
| --- | --- |
| Header title | `28px`, weight 600 |
| Step / mode title | `22px`, weight 600 |
| Option title (setup decision) | `20px`, weight 600 |
| Body text | `16px` |
| Labels (INPUT / PROCESS / OUTPUT) & captions | `14px` |

**Layout rules** (these prevent the overlap bug from 2026-08):
- Every `<text>` baseline must sit inside its container `<rect>` (check:
  `top = y - font-size`, `bottom = y + 0.3·size` both within the rect).
- Keep ≥ 22px line spacing between body lines; blocks must be tall enough
  for their line count (e.g. 4-line process block ≥ 112px tall).
- Side-by-side boxes must not overlap: verify rect extents after any move.

## 5. README integration pattern

Use the `<picture>` element with a `prefers-color-scheme` dark source
(matching the architecture image):

```html
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/<name>-dark.svg" />
  <img src="assets/<name>.svg" alt="…" style="max-width: 100%; height: auto; width: 1280px;" />
</picture>
```

Locale READMEs (9 non-English) reuse the **English** diagrams; only
`README.zh-CN.md` has its own Chinese SVG pair (`-zh.svg` / `-zh-dark.svg`).

## 6. Asset inventory

Every diagram ships in all 10 locales. Naming: `<name>.<locale>.svg` /
`<name>.<locale>-dark.svg` (EN is the bare `<name>.svg`; zh-CN uses `-zh`).
Locale suffix set: `zh` (zh-CN), `zh-TW`, `ja-JP`, `ko-KR`, `de-DE`, `es-ES`,
`fr-FR`, `pt-BR`, `ru-RU`.

| File | Description |
| --- | --- |
| `axiara-logo.svg` / `-dark.svg` | Logo mark |
| `axiara-lockup.svg` / `-dark.svg` | Logo + wordmark |
| `axiara-architecture*.svg` | Three data-layer architecture (10 locales) |
| `axiara-modes*.svg` | Four modes flow (10 locales) |
| `axiara-setup-decision*.svg` | Onboarding decision tree (10 locales) |

**Localization workflow** (repeatable, automated):
`scripts/dev/i18n_svg.py` regenerates the 8 derived locales (all except
zh-CN, which is a hand-written baseline) from the EN sources:

```bash
python scripts/dev/i18n_svg.py            # regenerate all managed locales
python scripts/dev/i18n_svg.py --locale de-DE
python scripts/dev/i18n_svg.py --extract  # re-derive i18n_dicts.py from committed SVGs
```

- Translation strings live in `scripts/dev/i18n_dicts.py` — the single
  source of truth. Edit there, then run the generator.
- The generator regex-replaces `<text>` bodies and ET-round-trips to match
  the committed byte format (no format churn); dark twins come from the §2
  palette map; files are written with LF line endings.
- Container geometry stays untouched — keep translations short enough to
  fit the boxes. zh-CN (`-zh`) SVGs are hand-written and not regenerated.

---

*Keep diagrams consistent: when you change one asset, regenerate all
variants (EN/ZH × light/dark) and re-verify geometry.*
