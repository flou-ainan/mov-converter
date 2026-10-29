# Step 03 — GUI mode (`converter-mov gui`) + rename `convertidos` → `converted`

**Date:** 2026-10-29
**Agent/author:** OpenCode (mimo-v2.6-flash-free)
**Related plan:** planning/plan_01_gui.md
**Commit(s):** pending (uncommitted at the time of writing)

## What was done

1. **`converter_mov.py`** (468 → 499 lines):
   - new `rodar_gui()` + dispatch: `sys.argv[1] == "gui"` opens the GUI before argparse (CLI untouched); friendly message if `tkinter` is missing (`sudo apt install python3-tk`); `sys.path` bootstrapped with `dirname(realpath(__file__))` so the symlinked command finds `gui.py` in the repo;
   - `executar()` and `converter()` gained an optional `progresso` callback: `None` keeps the CLI `Painel`, a callback feeds the GUI queue (no stdout writes from the GUI path);
   - rename `convertidos` → `converted` (module docstring, argparse description, `SAIDA`, OK log line);
   - argparse epilog with examples (`RawDescriptionHelpFormatter`).
2. **`gui.py`** (new, 471 lines): tkinter app with two stacked screens — start (load folder / load file buttons + GPU status label) and work (current-file header, `ttk.Progressbar` for the file and for the total, read-only log `Text`). Folder flow mirrors the CLI worker line by line (discovery, GPU probe, conversion loop with the GPU+CUDA → GPU → CPU ladder, verification, summary, delete confirmation for verified files only, back to start). File flow asks where to save (`asksaveasfilename`, default dir `converted/`, default name `<stem>.mp4`), converts, verifies, asks whether to delete the original, back to start. Workers run in a daemon thread and only post events to a `queue.Queue` drained by `root.after(80)`; dialogs go through module-level `messagebox`/`filedialog` so tests can stub them; `destroy()` cancels the poll timer (avoids a Tcl "invalid command" after close).
3. **`tests/smoke_gui.py`** (new): generates synthetic MOVs with ffmpeg in a temp dir (no media in the repo) and checks the CLI flow (answer `n`, plus a `-s` run) and both GUI flows with `askyesno`/`asksaveasfilename` stubbed, headless under `xvfb-run`.
4. **Rename in current docs/config:** `README.md` (pt-BR), `AGENTS.md`, `.gitignore`.
5. **Docs:** ADR-002 (tkinter decision), this devlog, `PLAN 01`, `PROJECT.md`, `ROADMAP.md`.

## Why

The owner converts course footage repeatedly and wants a window: pick a folder (or one file), watch the two bars, confirm deletion, land back on the start screen. Unifying the output folder name to `converted` makes the folder name English like the rest of the code (language policy: folder names are developer-facing).

## Files touched

- `converter_mov.py` (dispatch, `progresso` callback, rename, help)
- `gui.py` (new)
- `tests/smoke_gui.py` (new)
- `README.md`, `AGENTS.md`, `.gitignore` (rename + gui references)
- `docs/PROJECT.md`, `docs/dev-docs/{ROADMAP.md, planning/plan_01_gui.md, devlog/step_03_*.md, decisions/ADR-002-tkinter-gui.md}`

## How it was tested

- `ruff check .` clean; `ruff format --check gui.py tests/smoke_gui.py` clean (`converter_mov.py` still unformatted — pending the owner's decision in the ROADMAP); `py_compile` on all three files.
- `xvfb-run -a python3 tests/smoke_gui.py` → **SMOKE TEST OK**: CLI confirms + keeps originals on `n`, `-s` deletes verified originals, GUI folder flow writes `converted/*.mp4` and returns to the start screen with originals kept (stubbed `askyesno → False`), GUI file flow writes the chosen `converted/x.mp4` and keeps the original.
- `converter-mov --help` shows the `gui` example; `xvfb-run timeout 4 converter-mov gui` exits 124 (window opened and `mainloop` kept running).

## Pending / next steps

- Commit code + docs together (this step was uncommitted when written).
- Owner decision on `ruff format converter_mov.py` (ROADMAP).
- GUI ideas deferred: cancel button mid-conversion, drag-and-drop of a folder.

**Next task:** commit this step + the docs scaffold — tier: standard, effort: low — mechanical staging only.
