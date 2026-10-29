# Step 02 — Agent development docs scaffold

**Date:** 2026-10-29
**Agent/author:** OpenCode (mimo-v2.6-flash-free)
**Related plan:** none (owner request)
**Commit(s):** (this commit)

## What was done

Replicated the agent-development conventions of the owner's `Open-Subtitler` project, scaled down to this single-file tool:

- `AGENTS.md` — instructions for every coding agent: read `docs/` before code, mandatory documentation rules, language policy (English for dev docs/code, pt-BR for README and CLI output), engineering principles (zero pip dependencies, graceful GPU→CPU fallback, never lose the original footage, constants at the top), ai-memory note, model-tier recommendation protocol, commit policy.
- `CLAUDE.md` — imports `AGENTS.md`.
- `docs/PROJECT.md` — project map: overview, architecture diagram, stack, ADR table, folder structure, and a full file map of `converter_mov.py` (469 lines) with every function and its line number.
- `docs/dev-docs/README.md` — the documentation conventions (layout, `chat-context.md` policy, plans, devlogs, ADRs, flow of a change).
- `docs/dev-docs/ROADMAP.md` — the single list of pending work (proposals only; owner confirms).
- `docs/dev-docs/chat-context.md` — conversation hand-off snapshot.
- `docs/dev-docs/decisions/ADR-001-hevc-nvenc-constant-fps.md` — records the codec/fallback/verification decisions already baked into the script.
- `docs/dev-docs/devlog/step_01_project_scaffold.md` — logs the previous change retroactively.
- `ruff.toml` (lint + format, same rules as Open-Subtitler) and `.editorconfig`.

## Why

The owner asked (translated): "Just set up a docs/dev-docs folder there in mov-converter and the auxiliary files that carry the same agent development rules as in the Open-Subtitler project." Goal: any agent, in any future session, can pick up the project from `docs/` alone.

## Files touched

- `AGENTS.md`, `CLAUDE.md`, `ruff.toml`, `.editorconfig` (new)
- `docs/PROJECT.md` (new)
- `docs/dev-docs/README.md`, `ROADMAP.md`, `chat-context.md` (new)
- `docs/dev-docs/decisions/ADR-001-hevc-nvenc-constant-fps.md` (new)
- `docs/dev-docs/devlog/step_01_project_scaffold.md` (new)

## How it was tested

- Cross-checked structure and templates against `/mnt/work/Trabalhos/Projetos Flou/Open-Subtitler/docs/dev-docs/`.
- `grep -n`/`wc -l` on `converter_mov.py` generated the PROJECT.md file map.
- First quality-gate run: `ruff check` found 2 issues in `converter_mov.py`, fixed in this step:
  - `SIM105`: `try/except ValueError: pass` → `contextlib.suppress(ValueError)` in `info_video`;
  - `E741`: ambiguous variable `l` → `linha` in `Painel._desenhar`.
- After the fixes: `ruff check` clean; `python3 -m py_compile` OK; `converter-mov --help` OK.
- `ruff format --check` still reports the file as unformatted (the original compact style expands under the formatter). Left for the owner to decide — see ROADMAP.

## Pending / next steps

- Owner decision: run `ruff format` on `converter_mov.py` (mechanical reformat, large diff) or relax the format gate.
- Owner confirms or rewrites the proposals in ROADMAP "Next".
