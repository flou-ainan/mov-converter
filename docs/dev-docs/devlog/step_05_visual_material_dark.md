# Step 05 — Material dark visual restyle of the GUI

**Date:** 2026-10-29
**Agent/author:** OpenCode (mimo-v2.6-flash-free)
**Related plan:** [planning/plan_02_visual_material_dark.md](../planning/plan_02_visual_material_dark.md)
**Commit(s):** pending (uncommitted at the time of writing)

## What was done

- Rewrote the visual layer of `gui.py` (807 lines) with a **Material Design 3 dark** theme, still 100% stdlib (ADR-002 intact):
  - palette constants at the top (owner-chosen hex: `PRIMARIA #D0BCFF`, `SUPERFICIE #1C1B1F`, …) — the only "design" section to edit;
  - helpers `misturar()` (hex blend — Tk has no alpha, so hover/press/elevation are pre-blended), `_rgb()`, `retangulo()` (rounded rectangle as a `smooth=True` polygon), `_familia_instalada()` (first installed font from a preference list — resolves to Cantarell + DejaVu Sans Mono on this box);
  - `class Botao(tk.Canvas)`: pill button in `primario` / `contornado` / `texto` variants, hover + pressed state layers, 3 px elevation strip on the filled variant;
  - `class BarraProgresso(tk.Canvas)`: rounded trough + fill + right-aligned percent label;
  - the log now sits on a **rounded card** (canvas redrawn on `<Configure>` behind the text widget);
  - both screens restyled (dark surface, Material spacing); start-screen content vertically centered between expanding spacers.
- **Bug found while reviewing the screenshots:** the two screens were `pack`ed, so they split the window vertically and `tkraise()` had no effect (it only works when widgets overlap). Fixed with `place(x=0, y=0, relwidth=1, relheight=1)` on both screens + `tkraise()`; each state now shows exactly one screen.
- Workers (`_trabalho_pasta`/`_trabalho_arquivo`), the event queue and the flow API are untouched.

## Why

Plan 02 (owner picked "Material escuro" in chat): the assessment called for levels 1–2 (theme/typography and colors/rounded controls). Tk ships no rounded corners, state layers or alpha, so the standard zero-dependency solution is drawing widgets on `tk.Canvas`. No new packages, no ADR change.

## Files touched

- `gui.py` (visual layer + screen-stacking fix)
- `docs/dev-docs/planning/plan_02_visual_material_dark.md` (status → done)
- `docs/dev-docs/devlog/step_05_visual_material_dark.md` (this file)
- `docs/PROJECT.md` (gui.py file map: 807 lines, new symbols, stack row)
- `docs/dev-docs/ROADMAP.md` (item moved to Done)
- `docs/dev-docs/chat-context.md`

## How it was tested

- `ruff check .` → clean; `ruff format --check .` → 18 files already formatted; `py_compile` OK.
- `xvfb-run -a python3 tests/smoke_gui.py` → **SMOKE TEST OK** (all four flows).
- Visual review: 6 screenshots under `xvfb-run -a --server-args="-screen 0 1024x768x24"` — start screen, hover, pressed, mid-conversion (bars + log), 100 % / verification, back to start. Hover/press verified by pixel sampling (idle `#D0BCFF` → lighter on hover → darker when pressed).

## Pending / next steps

- Commits still pending (docs scaffold + steps 03–05), awaiting the owner.

**Next task:** commit the pending work — tier: standard, effort: low — mechanical staging only.
