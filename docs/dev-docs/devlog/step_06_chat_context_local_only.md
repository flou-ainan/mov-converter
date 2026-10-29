# Step 06 — `chat-context.md` becomes local-only

**Date:** 2026-10-29
**Agent/author:** OpenCode (mimo-v2.6-flash-free)
**Related plan:** none (trivial repository-policy change, no plan — devlog kept per `dev-docs/README.md`)
**Commit(s):** pending at write time (committed and pushed right after, in the first push to origin)

## What was done

- Added `docs/dev-docs/chat-context.md` to `.gitignore` (with a comment explaining why). The file was never tracked, so nothing had to be removed from the index or from history — it simply never reaches `origin`.
- Updated the references so a cloned repo stays coherent: `AGENTS.md` (read step + hand-off rule now say the file is local-only instead of "public"), `docs/dev-docs/README.md` (layout line + a "Location" note), `docs/PROJECT.md` (folder tree annotation).

## Why

The owner asked for it: the hand-off file contains verbatim conversation and should stay on this machine while the repository is pushed to GitHub. The file keeps its role for agents working in the owner's checkout; clones just don't get it (the rest of `docs/` remains the public source of truth).

## Files touched

- `.gitignore` (new entry + comment)
- `AGENTS.md` (two wording fixes)
- `docs/dev-docs/README.md` (layout + location note)
- `docs/PROJECT.md` (tree annotation)
- `docs/dev-docs/ROADMAP.md` (Done + push status)
- `docs/dev-docs/devlog/step_06_chat_context_local_only.md` (this file)
- `docs/dev-docs/chat-context.md` (local note; not committed — it is gitignored)

## How it was tested

- `git check-ignore -v docs/dev-docs/chat-context.md` → matches the new `.gitignore` rule.
- `git status` no longer offers the file for staging; `git ls-files` stays clean of it after the commits.
- `ruff check . && ruff format --check .` still green (docs-only change).

## Pending / next steps

- None for this change; the first push to GitHub follows immediately (scaffold + steps 03–06 in two commits).

**Next task:** pick the next item from ROADMAP — tier: standard, effort: low.
