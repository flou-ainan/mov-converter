# Agent instructions

Applies to every agent (Claude Code, Gemini/Antigravity, OpenCode, Copilot, Codex, ...).

## Before you start

1. Read `docs/PROJECT.md`: overview, stack, decisions, and a file map with line counts and functions.
2. Read `docs/dev-docs/ROADMAP.md` (the one list of what is left; pick work from it, not from the latest plan), `docs/dev-docs/chat-context.md` (the conversation so far, condensed — local-only, present only in the owner's checkout), the latest step in `docs/dev-docs/devlog/`, and any open plan in `docs/dev-docs/planning/` to see what is in progress.
3. Only then open the source files related to the task. This is a small two-file project: `converter_mov.py` is the CLI and the shared core, `gui.py` is the tkinter front end (imported only by `converter-mov gui`), but the docs still answer "why" before the code answers "how".

## Documentation rules (mandatory)

Full conventions: `docs/dev-docs/README.md`. Summary:

- **Every plan becomes a file** in `docs/dev-docs/planning/` before implementation starts.
- **`docs/dev-docs/ROADMAP.md` is the single list of pending work.** Keep it in step with the plans: a new idea goes in a column, a finished item moves to "Done" with its step number, and a plan whose items are all done gets `Status: done`.
- **Every change is logged** as a step in `docs/dev-docs/devlog/`: what changed, why, files touched, how it was tested.
- **Every relevant technical decision** (library, codec, architecture, format) becomes an ADR in `docs/dev-docs/decisions/`.
- **`docs/PROJECT.md` always reflects the current code.** Any change to files, functions, stack, or folder layout updates `PROJECT.md` in the same commit, including line counts (`wc -l converter_mov.py`) and function line numbers (`grep -n "^def \|^class " converter_mov.py`).

- **Conversation hand-off:** keep `docs/dev-docs/chat-context.md` up to date: a lean summary of the whole conversation with the owner, plus your last two complete replies verbatim. Update it when the owner asks and after long stretches of work (hours). The file is **local-only** (listed in `.gitignore`, never committed or pushed — the conversation stays on this machine); still keep secrets and third-party private data out of it. Details: `docs/dev-docs/README.md`.

Goal: someone who clones the repository, with no access to any agent memory, can understand the project and what is going on just by reading `docs/`.

## Language policy

- **English** for everything developer-facing: dev docs, `PROJECT.md`, plans, devlogs, ADRs, code, identifiers, comments, commit messages, folder names.
- **User-facing content is pt-BR**: `README.md` is written for the owner in Brazilian Portuguese, because this is a personal tool. CLI output and prompts stay in Portuguese too — they are the user interface.
- Docstrings and code comments follow the code's existing language (Portuguese, matching the original script); do not mix styles inside the file.

## Engineering principles

- **Zero-install philosophy:** the program must run with Python stdlib + `ffmpeg`/`ffprobe` on the PATH. No pip dependencies unless an ADR justifies them.
- **Degrade gracefully:** GPU (NVENC + CUDA decode) → GPU (NVENC) → CPU (libx265). A missing capability must never block the conversion; log it and fall through.
- **Never lose the owner's footage:** originals are deleted only after the converted file passes verification, and only after explicit confirmation (or `-s`).
- **Hackable:** behavior that the owner might want to tweak (quality constants, fps list, output folder name) lives as named constants at the top of the file, not buried in logic.
- **Cross-platform paths:** use `os.path` / `pathlib`, never shell strings with hardcoded separators. Today the target is Linux, but keep Windows in mind.

## Cross-agent memory

This machine uses [ai-memory](https://github.com/akitaonrails/ai-memory) to carry context between agents. It is a complement: the source of truth for project state is always `docs/`.

## Recommending the model for the next task

When you finish a task, end your reply to the owner with the model tier and reasoning effort the **next** task needs, and write the same line in the plan's "next" item so it survives a hand-off. The owner prefers **low** or **medium** effort; propose **high** only for a specific reason.

Tiers are vendor-neutral; map them to your own family:

| Tier | Examples (2026) | Use it for |
|---|---|---|
| **standard** | Claude Sonnet, GPT standard / Codex default, Gemini Pro | Work with a written plan and an existing pattern to follow: features, flags, docs, bug fixes with a clear repro. |
| **top** | Claude Opus, GPT top reasoning tier, Gemini top "thinking" tier | FFmpeg filter-graph debugging, codec/HDR subtleties, concurrency, security-sensitive changes. |

| Effort | When |
|---|---|
| **low** | Mechanical edits, docs, renames, small fixes. |
| **medium** | The default for feature work. |
| **high** | Only when a wrong design is expensive to undo, or a bug resists a first investigation. Say why. |

Format: `**Next task:** <what> — tier: standard|top, effort: low|medium|high — <one-line reason>`.

## Branches and commits

`main` takes direct commits for now (personal project, single owner). Use **Conventional Commits**. If the project grows contributors, introduce branches + PR + CI and record the change in an ADR.

## General

- Never commit secrets, API keys, or files listed as local-only in `.gitignore`.
- Never commit test media (`.MOV`, `.mp4`, `converted/`, `converter_error_log.txt`) — they are gitignored for a reason.
- Quality gate: `ruff check . && ruff format --check .` (everything is formatted); smoke test: `xvfb-run -a python3 tests/smoke_gui.py`.
- Preserve local changes that are not yours.
- When done, report what was validated.
