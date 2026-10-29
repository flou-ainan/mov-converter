# Plan 01 — GUI mode (`converter-mov gui`) + rename `convertidos` → `converted`

**Status:** done
**Date:** 2026-10-29

## Goal

Give the tool a lightweight graphical mode and unify the output folder name in English:

1. `converter-mov gui` opens a small tkinter window that accepts a **folder** or a **single file**.
2. Folder mode behaves exactly like the CLI: converts every `.MOV` into `converted/`, shows a **per-file** and a **total** progress bar, verifies, asks whether to delete the originals that passed, then returns to the start screen.
3. Single-file mode asks where to save (default suggestion `converted/<name>.mp4`), runs the same conversion + verification, asks whether to delete the original at the end, then returns to the start screen.
4. Rename the output folder `convertidos` → `converted` in the current code and docs (historical devlog/chat quotes stay verbatim).

## Context

- The owner runs the tool from the terminal today; repeated conversions of course footage would be simpler with a window (pick folder → watch bars → confirm delete).
- `AGENTS.md` principles apply: stdlib only (tkinter ships with Python; no pip deps), never lose footage (delete only after verification + explicit confirmation), hackable constants.
- tkinter 8.6 and `xvfb-run` are available on this machine, so the GUI can be smoke-tested headless.
- The CLI core (`info_video`, `montar_comando`, `converter`, `verificar`, `registrar_erro`) must be **reused**, not duplicated; only the presentation layer differs (queue + tkinter instead of the ANSI `Painel`).

## Proposed changes

| File | Change |
|---|---|
| `converter_mov.py` | Dispatch `converter-mov gui` at the top of `main()` (argparse untouched, so the CLI keeps working). `executar()`/`converter()` gain an optional `progresso` callback: `None` keeps the CLI `Painel` behaviour, a callback feeds the GUI queue. Rename `convertidos` → `converted` (docstring, argparse description, `SAIDA`, log line). Help epilog mentions `gui`. |
| `gui.py` (new) | tkinter app: start screen (load folder / load file buttons + GPU status), work screen (current-file label, two `ttk.Progressbar`s, read-only log). Workers (`_trabalho_pasta`, `_trabalho_arquivo`) run in a daemon thread and only talk to a `queue.Queue`; the main loop polls it with `root.after()`. End-of-run `messagebox.askyesno` for deletion, then back to the start screen. Dialogs go through module-level `messagebox`/`filedialog` so tests can patch them. |
| `tests/smoke_gui.py` (new) | Headless smoke test: generates synthetic MOVs with ffmpeg in a temp dir, runs the CLI flow (answer `n`, plus a `-s` run) and both GUI flows under `xvfb-run` with `askyesno` patched to `False`. No media committed. |
| `README.md` (pt-BR) | Usage gains `converter-mov gui`; `convertidos/` → `converted/`; structure section gains `gui.py` + `tests/`. |
| `AGENTS.md`, `docs/PROJECT.md`, `.gitignore`, `docs/dev-docs/ROADMAP.md` | Two-file reality, `converted/`, ADR row, plan/step entries. |
| `docs/dev-docs/decisions/ADR-002-tkinter-gui.md` (new) | Decision: tkinter (stdlib) over Qt/web alternatives. |
| `docs/dev-docs/devlog/step_03_gui_and_converted_rename.md` (new) | The change log for this step. |

Dispatch detail: `main()` checks `sys.argv[1] == "gui"` before argparse (a folder literally named `gui` is reached as `converter-mov ./gui`). Because the command is a symlink, `gui.py` is imported after inserting `dirname(realpath(__file__))` into `sys.path`.

Reused CLI behaviour in the GUI (parity checklist):

- discovery: `f.lower().endswith(".mov")`, alphabetical, `converted/` created with `makedirs(exist_ok=True)`;
- GPU probe (`tem_nvenc` → `tem_cuda_decode`) with the same log lines;
- fallback ladder GPU+CUDA → GPU → CPU; errors → `converter_error_log.txt` via `registrar_erro`;
- verification of every non-failed file; delete **only** verified files and **only** after `askyesno`;
- summary lines (`N convertido(s) com sucesso, M com problema`, failed list, log path).

## Open questions

- None blocking. Deletion in file mode is offered only when the converted file passed verification (never-lose-footage principle) — noted here as a deliberate reading of "pergunta se quer excluir no fim".
- Deferred (see ROADMAP): cancel button mid-conversion, drag-and-drop.

## Definition of done / how to test

1. `ruff check` clean on the repo; `python3 -m py_compile converter_mov.py gui.py`.
2. CLI regression: synthetic folder → `converter-mov <pasta>` writes to `converted/`, verifies, still asks before deleting; `-s` deletes verified originals.
3. `xvfb-run -a python3 tests/smoke_gui.py` passes: folder flow creates `converted/*.mp4` + keeps originals (patched `askyesno` → False); file flow writes to the chosen path and asks to delete.
4. `converter-mov --help` shows the `gui` hint; `converter-mov gui` opens the window on a real display.
5. Docs updated in the same commit (`PROJECT.md` line counts + function lines, `ROADMAP`, devlog step 03, ADR-002).

**Next task (after this plan):** `ruff format` decision — tier: standard, effort: low — mechanical, only needs the owner's style choice.
