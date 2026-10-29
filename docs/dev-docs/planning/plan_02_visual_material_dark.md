# Plan 02 — Visual pass: Material dark (levels 1 + 2, zero install)

**Status:** done
**Date:** 2026-10-29

## Goal

Restyle the GUI with a Material Design **dark** look (owner's palette choice) using only the Python stdlib — levels 1 (theme, fonts, padding) and 2 (colors, rounded buttons, custom progress bars) from the visual assessment, keeping ADR-002 (zero install) intact.

## Context

- The GUI currently uses stock ttk/`tk.Button` (square, system look, light font).
- Tk gives no rounded corners and no state-layer colors out of the box; the standard zero-dep solution is drawing the widgets on `tk.Canvas`: rounded polygons (`smooth=True`), color blending for hover/press/elevation (no alpha channel in Tk, so blends are computed from hex), canvas-sized progress bars.
- Palette selected by the owner: **Material 3 dark** (`#D0BCFF` primary, `#1C1B1F` surface).

## Proposed changes

| File | Change |
|---|---|
| `gui.py` | Palette constants at the top (hackable hex, per AGENTS.md); helpers `misturar()` + `retangulo()` (rounded polygon); new `Botao` canvas widget (pill, hover/pressed states, subtle elevation for the filled variant); new `BarraProgresso` canvas widget (rounded trough + fill); log inside a rounded card; fonts picked at runtime (Roboto → DejaVu Sans fallback, mono fallback); both screens restyled (dark surface, Material typography/padding). Workers and event flow untouched. |
| `tests/smoke_gui.py` | Unchanged — must still pass (it only uses the public flow API). |
| `docs/*` | devlog step 05, PROJECT.md file map, ROADMAP Done. |

## Open questions

None — palette decided in chat ("Material escuro"). No ripple animations / real alpha shadows (impossible without deps); elevation on the filled button is a 3 px blended offset strip, cards use outline + surface tint (the M3 dark elevation language).

## Definition of done / how to test

1. `ruff check . && ruff format --check .` green; `py_compile` OK.
2. `xvfb-run -a python3 tests/smoke_gui.py` → SMOKE TEST OK (all four flows).
3. Screenshot of both screens if a screenshot tool exists on the box; otherwise the owner opens `converter-mov gui` and confirms.
4. PROJECT.md/ROADMAP/devlog updated.

**Next task (after this plan):** commit all pending work — tier: standard, effort: low — mechanical staging only.

## Result (2026-10-29)

All four DoD items met: gates green (18 files formatted), smoke test OK, screenshots reviewed (start, hover, press, mid-run, finish, back to start — 6 PNGs under `/tmp/opencode/visual/`, outside the repo). Two issues found and fixed during visual review: the screens were `pack`ed so `tkraise()` never switched them (now `place` + `tkraise`), and the start screen's content is vertically centered with expanding spacers. Logged in `devlog/step_05_visual_material_dark.md`.
