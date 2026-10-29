# Development documentation conventions

The whole history of the project lives as markdown inside the repository. This is a contingency: even without ai-memory or any agent memory, anyone who clones the project can see what exists, what was done, and what is in progress.

All developer-facing files here are written in **English** (user-facing `README.md` and CLI output stay in pt-BR — see `AGENTS.md`, "Language policy").

## Layout

```
docs/
├── PROJECT.md              # project map, always up to date
└── dev-docs/
    ├── README.md           # this file
    ├── ROADMAP.md          # the one list of what is left (start here to pick work)
    ├── chat-context.md     # lean summary of the owner ↔ agent conversation + last two full replies (local only, gitignored)
    ├── planning/           # plans, written before implementing
    ├── devlog/             # one step per change or executed stage
    ├── decisions/          # ADRs: technical decisions and their reasons
    └── references/         # background material (e.g. benchmark notes)
```

## `chat-context.md`: conversation hand-off

Long agent conversations consume a lot of tokens. `chat-context.md` lets a new session, or another agent, pick up the conversation without the full transcript.

**Location:** local-only — listed in `.gitignore`. It exists in the owner's checkout but is never committed or pushed, so a cloned repo does not include it (step 06).

- **Contents:**
  - a lean summary of the whole owner ↔ agent conversation: what was asked and decided, the owner's preferences, open questions, and what is in progress;
  - the **last two complete replies** of the agent, verbatim. They stay in the language they were written in; the rest is in English.
- **When to update:**
  - when the owner asks;
  - after long stretches of work (hours);
  - before ending a long session.
  - Replace the file. Do not append: it is a snapshot, and git keeps the history.
- **Privacy:** it is a public file. No secrets or API keys, no private data about third parties, no content from local-only files (`.gitignore`). Refer to the owner's media generically, for example "the owner's course footage".
- It does not replace plans, devlogs or ADRs. Decisions still go there; the summary only links to them.

## `docs/PROJECT.md`

A condensed file that helps agents and people find what they need fast, without rereading the code. It contains:

1. Project overview and current state
2. Chosen architecture
3. Technologies / stack
4. Technical decisions (summary linking to each ADR)
5. Folder structure
6. File map: for every source file, its line count and a short description of each function or class, with the line where it starts

**Rule:** every change to the project updates `PROJECT.md` in the same commit. Count lines with `wc -l converter_mov.py` and functions with `grep -n "^def \|^class " converter_mov.py`.

## Plans — `planning/plan_NN_<topic>.md`

Written **before** implementing. Sequential numbering (`plan_02_gpu_decode_fallback.md`).

```markdown
# Plan NN — <topic>

**Status:** proposed | approved | in progress | done | abandoned
**Date:** YYYY-MM-DD

## Goal
## Context
## Proposed changes   (files to create/change and what changes in each)
## Open questions
## Definition of done / how to test
```

Update the status as it changes.

## Devlog — `devlog/step_NN_<topic>.md`

One file per change or executed stage, sequential numbering (`step_03_global_symlink.md`). It records what **was done**, not what is intended.

```markdown
# Step NN — <topic>

**Date:** YYYY-MM-DD
**Agent/author:** <who>
**Related plan:** planning/plan_NN_<topic>.md (if any)
**Commit(s):** <hash>

## What was done
## Why
## Files touched
## How it was tested
## Pending / next steps
```

## Technical decisions — `decisions/ADR-NNN-<topic>.md`

For choices someone may question later: codec, library, architecture, change of approach.

```markdown
# ADR NNN — <title>

**Status:** proposed | accepted | superseded by ADR-XXX
**Date:** YYYY-MM-DD

## Context
## Decision
## Alternatives considered
## Consequences
```

When you create an ADR, add a row to the "Technical decisions" table in `PROJECT.md`.

## Flow of a change

1. Plan → `planning/plan_NN_*.md`
2. If there is a technical decision → `decisions/ADR-NNN-*.md`
3. Implement
4. Log → `devlog/step_NN_*.md`
5. Update `PROJECT.md`
6. Commit code and docs together

Trivial changes (a typo, a constant tweak) may skip the plan, but never the devlog step and the `PROJECT.md` update.
