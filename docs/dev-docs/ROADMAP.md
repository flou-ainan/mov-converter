# Roadmap

**The one list of what is left.** Start here, not in the latest plan. Each item points to the plan that holds its details. When an item is done, move it to "Done" with its step number; when a plan is finished, set its status line to `done`.

**Last updated:** 2026-10-29 (step 06: `chat-context.md` local-only + first push to GitHub). The "Next" column is a proposal; the owner confirms it.

## Next (proposed — owner confirms)

| Item | Plan | Notes |
|---|---|---|
| Delete the scattered copies of `converter_mov.py` the owner has around old folders | — | The global command makes them obsolete. Owner does this manually, folder by folder. |
| Optional: `.mov` rename/normalisation pass (iPhone files sometimes are `.MOV`/`.mov` mixed) | — | Already handled case-insensitively; only rename leftovers could matter. |

## Ideas (not decided)

| Idea | Plan |
|---|---|
| GUI polish: cancel button mid-conversion, drag-and-drop a folder onto the window | |
| `--keep` / auto-delete flags refinement (e.g. delete only after disk-space check) | |
| Parallel conversion of two files when VRAM allows | Needs an ADR: NVENC sessions + memory. |
| H.264 output option for platforms that choke on HEVC | Hotmart/YouTube usually fine with HEVC; check first. |
| Windows install instructions (PowerShell profile + symlink) | The owner works on Linux Mint today. |
| Packaging as a pip/uv tool (`uv tool install`) instead of a symlink | Symlink is enough for now. |

## Done (recent)

- **Steps 01–02:** global CLI installed (`~/.local/bin/converter-mov` symlink), git repo created at `/mnt/work/code-space/personal-projects/mov-converter`, agent development docs scaffolded (AGENTS.md, CLAUDE.md, docs/dev-docs/*, ruff.toml, .editorconfig).
- **Step 03:** GUI mode `converter-mov gui` (tkinter, ADR-002) with folder and single-file flows, per-file + total bars, delete confirmation and return to the start screen; headless smoke test `tests/smoke_gui.py`; output folder renamed `convertidos` → `converted`.
- **Step 04:** `ruff format converter_mov.py` — the whole repo now passes `ruff check .` and `ruff format --check .`.
- **Step 05:** Material 3 dark visual restyle of `gui.py` (zero-install canvas widgets: pill `Botao` with hover/press, rounded `BarraProgresso`, rounded log card, runtime font probing); screen switching fixed (`place` + `tkraise`); validated with the smoke test plus 6 screenshots under `xvfb-run`.
- **Step 06:** `chat-context.md` moved to local-only (`.gitignore`, never pushed); references updated in `AGENTS.md`/`README`/`PROJECT.md`. First push to GitHub: the whole work so far (docs scaffold + steps 03–06) committed and pushed to `github.com/flou-ainan/mov-converter`.

## Plans at a glance

| Plan | Status |
|---|---|
| [plan_01_gui.md](planning/plan_01_gui.md) — GUI mode + `converted` rename | done |
| [plan_02_visual_material_dark.md](planning/plan_02_visual_material_dark.md) — Material dark visual pass | done |
