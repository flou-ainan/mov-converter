# Project Map — MOV Converter

> A condensed map of the project, so agents and people can find what they need without rereading the code.
> **Update this file with every change to the project** (files, functions, stack, structure). Conventions: `docs/dev-docs/README.md`.

**Last updated:** 2026-10-29 — step 05 (Material dark visual restyle of the GUI).

---

## 1. Overview

**MOV Converter** (`converter-mov`) is a personal tool that batch-converts every `.MOV` video of a folder (typically iPhone footage) to `.MP4` (HEVC) in a `converted/` subfolder, with integrity verification before the originals can be deleted. It has a **CLI** (`converter-mov [pasta] [-s]`) and a **GUI** (`converter-mov gui`, tkinter).

What it does (both frontends share the same core):

- Converts every `.MOV` in the target folder (current folder by default, or one passed as argument) — or a single chosen file in the GUI — to `.MP4` in `converted/`.
- Uses the GPU (NVIDIA NVENC HEVC, plus CUDA decode when available) with automatic fallback to CPU (libx265).
- Preserves quality: constant-quality encoding, 10-bit/HDR kept when present, colour metadata carried over, audio copied losslessly when already AAC.
- Converts the iPhone's variable framerate into a **constant** framerate (exact 24000/1001, 30000/1001, 60000/1001 fractions where applicable).
- Verifies every converted file (opens, has video, same duration, decodes start and end) **before** offering to delete the originals; failures are kept and logged.
- Logs every failure with the full FFmpeg command and stderr to `converter_error_log.txt` in the processed folder.

GUI specifics (ADR-002): start screen (load folder / load file + GPU status), work screen with a **per-file** and a **total** progress bar plus a log, delete confirmation via dialog, back to the start screen at the end; in file mode the save location is asked first (default `converted/<name>.mp4`). Visual layer (step 05): Material 3 dark theme drawn with zero-install canvas widgets (pill buttons with hover/press states, rounded progress bars, rounded log card, runtime font probing — palette constants at the top of `gui.py`).

Goal: one global command (`converter-mov`) usable from any folder, no copy-pasting scripts around.

**Current state:** works end to end on the owner's machine (Linux Mint, RTX 2070 Super): installed as a global command via a symlink to this repo (`~/.local/bin/converter-mov → converter_mov.py`). Step 01 validated a full CLI round trip; step 03 validated the GUI flows headless (`xvfb-run -a python3 tests/smoke_gui.py`); step 05 reviewed screenshots of both screens (start, hover/press, mid-conversion, finish) under `xvfb-run`. This is a personal tool for the owner's course-video production, not a distributed package.

## 2. Architecture

Two files, no dependencies beyond the Python standard library (tkinter for the GUI); FFmpeg is the only external process:

```
converter-mov [pasta] [-s]                converter-mov gui
      │                                         │
      ▼                                         ▼
 main() (CLI)                            rodar_gui() ──► gui.py (tkinter)
      │                                                     │  tela inicial
      │                                                     │  (pasta ou arquivo)
      ▼                                                     ▼
 lista *.mov ──► info_video()             workers em thread (fila de eventos)
      │                    │                               │
      ▼                    ▼                               │ (usa o mesmo core)
 montar_comando()   Painel (barras CLI) ◄── progresso ── executar()/converter()
      │                                                  │
      ▼                                                  ▼
 executar()/converter() ── ffmpeg (NVENC → x265 fallback)
      │
      ▼
 verificar() ──► optional deletion of verified originals ──► tela inicial (GUI)
```

- **Global entry point:** `~/.local/bin/converter-mov` is a symlink to `converter_mov.py` in this repo, so edits here take effect on the command directly. `gui.py` is found via `dirname(realpath(__file__))` added to `sys.path` when the `gui` dispatch runs.
- **GUI threading:** workers (`_trabalho_pasta`, `_trabalho_arquivo`) run in a daemon thread, never touch tkinter, and post events to a `queue.Queue` polled with `root.after(80)`. `executar()`/`converter()` take an optional `progresso(frac, total)` callback: `None` keeps the CLI `Painel`, a callback feeds the GUI (ADR-002).
- **Target folder:** the current working directory by default, or the first positional argument (CLI); the folder/file picked in the dialog (GUI).
- **Output:** `converted/` inside the target folder; error log `converter_error_log.txt` (created only when an error occurs).

## 3. Technologies / stack

| Layer | Technology |
|---|---|
| Language | Python 3.10+ (stdlib only, no pip dependencies) |
| Media tooling | `ffmpeg` + `ffprobe` on the PATH (external processes) |
| GPU | NVIDIA NVENC (HEVC, p7/hq, VBR constant-quality), CUDA decode when the build supports it |
| CPU fallback | libx265, CRF 18, preset medium |
| CLI progress UI | ANSI-terminal panel (per-file bar + total bar), redrawn in place |
| GUI | tkinter 8.6 (custom `tk.Canvas` widgets — `Botao`, `BarraProgresso` —, `messagebox`/`filedialog`), queue + `root.after` polling |
| Install | symlink `~/.local/bin/converter-mov` → repo copy |
| Quality gate | ruff (lint + format), config in `ruff.toml` |
| Tests | `tests/smoke_gui.py` (ffmpeg-generated synthetic clips; GUI flows under `xvfb-run`) |
| Reference hardware | RTX 2070 Super 8 GB, Linux Mint 22 |
| Targets | Linux (primary); paths built with `os.path`, Windows-friendly in principle |

## 4. Technical decisions

| ADR | Decision | Status |
|---|---|---|
| [001](dev-docs/decisions/ADR-001-hevc-nvenc-constant-fps.md) | HEVC via NVENC with CPU fallback, constant framerate, verify-before-delete | accepted |
| [002](dev-docs/decisions/ADR-002-tkinter-gui.md) | tkinter GUI in a separate lazily-imported file, thread + queue, `progresso` callback | accepted |

## 5. Folder structure

```
mov-converter/
├── converter_mov.py        # CLI + shared core (entry point of the symlink)
├── gui.py                  # tkinter GUI (imported only by `converter-mov gui`)
├── AGENTS.md               # instructions for every coding agent
├── CLAUDE.md               # → AGENTS.md
├── README.md               # user-facing doc (pt-BR)
├── ruff.toml               # lint + format config
├── .editorconfig
├── .gitignore              # ignores converted/, logs, media
├── tests/
│   └── smoke_gui.py        # headless smoke test (CLI + both GUI flows)
└── docs/
    ├── PROJECT.md          # this file
    └── dev-docs/
        ├── README.md       # documentation conventions
        ├── ROADMAP.md      # the one list of pending work
        ├── chat-context.md # owner ↔ agent conversation hand-off (local only, gitignored)
        ├── planning/       # plans, written before implementing
        ├── devlog/         # one step per change
        ├── decisions/      # ADRs
        └── references/     # background material
```

## 6. File map

### `converter_mov.py` — 602 lines

The CLI and the shared core: log utilities, media probing helpers, terminal UI, FFmpeg command building and execution, verification, GUI dispatch, main flow. Style: fully `ruff format`-ed (step 04) and lint-clean.

| Line | Symbol | Description |
|---|---|---|
| 46 | `registrar_erro(titulo, detalhes)` | Appends an error to `converter_error_log.txt`, writing a system/FFmpeg/GPU header on the first error of the run |
| 84 | `ffprobe_json(arquivo)` | Runs `ffprobe -print_format json` and parses the result (empty dict on failure) |
| 105 | `info_video(arquivo)` | Extracts duration, average fps, 10-bit flag, colour metadata and audio codec of a video |
| 132 | `fps_constante(fps_medio)` | Snaps a variable fps to the nearest standard (exact fractions for 23.976/29.97/59.94) |
| 143 | `tem_nvenc()` | Probes whether `hevc_nvenc` actually encodes a test clip on this machine |
| 167 | `tem_cuda_decode()` | Checks whether `cuda` appears in `ffmpeg -hwaccels` |
| 175 | `barra(fracao, largura)` | Renders one `[###---] 42%` progress bar |
| 181 | `class Painel` | Fixed terminal block: header line, per-file bar, total bar; messages print above it and it redraws in place |
| 249 | `montar_comando(entrada, saida, info, usar_gpu, decodificar_gpu)` | Builds the full FFmpeg command (fps fix, NVENC/x265, HDR/colour flags, audio, hvc1 tag, faststart, progress pipe) |
| 326 | `executar(cmd, nome, dur, feito_antes, dur_total, progresso=None)` | Runs FFmpeg, parsing `-progress pipe:1`; updates the `Painel` or calls `progresso(frac, total)` (GUI) |
| 348 | `converter(entrada, saida, nome, info, feito_antes, dur_total, gpu, cuda, progresso=None)` | Tries GPU+CUDA → GPU → CPU, logging each failed attempt with the exact command |
| 383 | `verificar(original, convertido)` | Post-conversion check: exists, has video, same duration, decodes 2 s from start and end, constant framerate |
| 432 | `perguntar_sim_nao(pergunta)` | Yes/no prompt with validation |
| 445 | `rodar_gui()` | Dispatch target for `converter-mov gui`: sys.path bootstrap, tkinter check with install hint, imports `gui.rodar_interface` |
| 460 | `main()` | Entry: `gui` dispatch first, then argparse (`pasta`, `-s`), discovery, conversion loop, verification, optional deletion |

Module-level constants (lines 29–35): `LARGURA_BARRA = 30`, `QUALIDADE_GPU = 19`, `QUALIDADE_CPU = 18`, `FPS_PADRAO` list; global run state `PASTA`/`SAIDA`/`LOG`.

### `gui.py` — 807 lines

tkinter front end (ADR-002) with the Material dark visual layer (step 05). Workers run in a daemon thread and only post events to a queue; the Tk loop polls it. Dialogs go through module-level `messagebox`/`filedialog` so tests can stub them. The two screens are `place()`d to overlap the whole window and switched with `tkraise()`.

| Line | Symbol | Description |
|---|---|---|
| 58 | `_rgb(cor)` | `#rrggbb` → `(r, g, b)` tuple |
| 63 | `misturar(cor1, cor2, t)` | Blends two hex colours (Tk has no alpha: hover/press/elevation are pre-blended) |
| 73 | `retangulo(canvas, x1, y1, x2, y2, raio, **kwargs)` | Rounded rectangle as a `smooth=True` polygon |
| 107 | `_familia_instalada(candidatas)` | First installed font family from a preference list (Roboto → Cantarell → DejaVu Sans) |
| 113 | `class Botao(tk.Canvas)` | Pill button: `primario`/`contornado`/`texto` variants, hover + pressed state layers, 3 px elevation strip on the filled variant |
| 221 | `class BarraProgresso(tk.Canvas)` | Rounded progress bar: trough + fill + right-aligned percent label, `definir(fracao)` |
| 263 | `_trabalho_pasta(pasta, *, avisar)` | Thread worker: the CLI folder routine — discovery, GPU probe, conversion loop, verification, summary; emits `log`/`cabecalho`/`progresso`/`fim`/`sem_arquivos` events |
| 364 | `_trabalho_arquivo(entrada, saida, *, avisar)` | Thread worker for one file: converts to the chosen `saida`, verifies, emits the same events |
| 441 | `class Aplicacao(tk.Tk)` | Two overlapping screens (start / work via `place` + `tkraise`), event polling, GPU status thread, deletion dialog + return to start |
| 611 | `_desenhar_cartao(evento)` | Redraws the rounded canvas card behind the log on `<Configure>` |
| 801 | `rodar_interface()` | Entry point: `Aplicacao().mainloop()` (also runs via `python3 gui.py`) |

`Aplicacao` key methods: `_construir_inicio`/`_construir_trabalho` (build both screens; start content vertically centered between expanding spacers), `_mostrar_inicio`, `_escolher_pasta`/`_escolher_arquivo` (dialogs), `iniciar_pasta`/`iniciar_arquivo` (public flow entry points, used by the smoke test), `_iniciar`/`_rodar` (thread start), `_poll`/`_processar` (queue → widgets), `_finalizar` (summary, delete question, back to start), `_log`, `_desenhar_cartao`, `destroy` (cancels the poll timer).

Palette constants at the top (lines 38–49): `PRIMARIA`, `SOBRE_PRIMARIA`, `CONTAINER`, `SUPERFICIE`, `CONTAINER2`, `VARIAVEL`, `TEXTO`, `TEXTO_FOFO`, `CONTORNO`, `ERRO`, `OK`, `PRETO`; font preference lists in `FONTES_TEXTO`/`FONTES_MONO` (lines 51–52), first installed family wins.

### `tests/smoke_gui.py` — 135 lines

Headless smoke test: `gerar_mov` (ffmpeg synthetic clip in a temp dir), `teste_cli` (confirm + `n` path, `-s` path), `teste_gui` (folder flow and file flow with stubbed dialogs), `_esperar` (pumps `update()` until `app.terminou`). Run: `xvfb-run -a python3 tests/smoke_gui.py`.
