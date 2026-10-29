# ADR 002 — tkinter for the GUI

**Status:** accepted
**Date:** 2026-10-29

## Context

The owner wants a lightweight graphical mode (`converter-mov gui`) that accepts a folder or a single file, shows per-file and total progress, confirms deletion of verified originals and returns to the start screen. The project's standing rule (AGENTS.md, "Zero-install philosophy") is Python stdlib + `ffmpeg`/`ffprobe` on the PATH, no pip dependencies.

## Decision

Use **tkinter** (8.6 on the owner's machine, ships with Python). The GUI lives in a new file `gui.py` next to `converter_mov.py` and is imported **lazily**, only when `sys.argv[1] == "gui"` — the CLI never touches tkinter, and on a machine without `python3-tk` the entry point prints `sudo apt install python3-tk` and exits instead of crashing.

Threading model: the conversion workers (`_trabalho_pasta`, `_trabalho_arquivo`) run in a daemon thread and only post events to a `queue.Queue`, which the Tk main loop drains with `root.after()` (POLL_MS = 80). Workers never call tkinter; widgets are only touched from the main loop. The CLI's ANSI `Painel` is bypassed through a new optional `progresso` callback on `executar()`/`converter()` — `None` (the CLI) keeps the old behaviour.

## Alternatives considered

- **PySide6 / Qt:** better widgets, but hundreds of MB of dependencies — breaks zero-install for a two-button tool.
- **Web UI (Flask + browser):** a server process, a port and a browser round-trip just to pick a folder; more moving parts and more to secure.
- **Textual / rich (TUI):** pretty and terminal-native, but pip dependencies, and the owner explicitly asked for a graphical interface.
- **Everything inside `converter_mov.py`:** would roughly double the file the docs call "the whole program"; a second file keeps the CLI readable and lets tests `import gui` directly.

## Consequences

- `python3-tk` must be installed for the GUI only; the CLI keeps working without it, with a clear error message when missing.
- Dialogs are invoked through module-level `messagebox`/`filedialog`, so `tests/smoke_gui.py` can replace them with stubs and drive both flows headless under `xvfb-run`.
- The "single-file project" statement in `AGENTS.md`/`docs/PROJECT.md` became "two files: CLI core + GUI".
- A folder literally named `gui` must be passed as `converter-mov ./gui` (documented in `--help`).
