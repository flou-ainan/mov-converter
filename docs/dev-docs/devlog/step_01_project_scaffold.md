# Step 01 — Project scaffold: global CLI + git repository

**Date:** 2026-10-28
**Agent/author:** OpenCode (mimo-v2.6-flash-free)
**Related plan:** none (owner request)
**Commit(s):** d5042c5

## What was done

- Took the owner's `converter_mov.py` (previously copy-pasted into every video folder) and made it a **global command**:
  - the folder to process became the **current working directory** by default, with an optional positional argument for any other folder;
  - argparse was added (`pasta`, `-s/--sim` to delete verified originals without prompting);
  - installed as `~/.local/bin/converter-mov`, a symlink to the repo copy, so edits here apply to the command directly.
- Created the git repository at `/mnt/work/code-space/personal-projects/mov-converter` with `main` as the default branch and the Conventional Commit style used in the owner's other projects.
- Files: `converter_mov.py` (469 lines), `README.md` (pt-BR), `.gitignore` (`__pycache__/`, `*.pyc`, `converter_error_log.txt`, `convertidos/`).

## Why

The owner said (translated): "I want to turn my converter_mov.py script into a global program, because I am copy-pasting it into every folder where I need it."

## Files touched

- `converter_mov.py` (moved + CLI flags added)
- `README.md`
- `.gitignore`
- `~/.local/bin/converter-mov` (symlink, outside the repo)

## How it was tested

- `converter-mov --help` and a nonexistent-folder argument (clean exit 1 with message).
- Full round trip with a synthetic 2 s 640×480 MOV in a temp folder: NVENC + CUDA decode detected, converted to `convertidos/teste.mp4`, verification passed (`hevc, framerate constante`), originals deleted with `-s`. Temp folder removed afterwards.

## Pending / next steps

- The owner may delete the old scattered copies of the script folder by folder (ROADMAP "Next").
