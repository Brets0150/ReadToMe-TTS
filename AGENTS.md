# ReadToMe-TTS — guide for any AI agent or person resuming this project

This project keeps its complete history inside the project directory, in `history/`, so that work can
continue in any future session, with any AI model, provider or tool, without losing context.

## Read first, in this order
1. `history/STATUS.md` — what the project is, where it stands now, next steps, open problems.
2. The last few entries of `history/SESSIONS.md` — what recent sessions did and left unfinished.
3. `history/DECISIONS.md` and `history/PROBLEMS.md` — append-only logs; grep by id (`D-0007`, `P-0003`)
   or by keyword. Follow "Superseded by" / "Updated by" pointers to the latest word on a topic.
4. `history/sessions/` — full transcripts of past sessions. Grep them for details; do not load one whole.

## Logging protocol (do it when it happens, not at the end; sessions can end abruptly)
- **Decision made** → append a `decision` entry: context, decision, why, alternatives, expected outcome.
- **Problem met** → append a `problem` entry: symptoms, investigation, root cause, fix, result, status.
- **Something changed or turned out wrong** → append a new entry that `--updates` or `--supersedes` the
  old id. Never edit, rewrite or delete an existing entry.
- **Before you stop** (and after each milestone) → append a `session` entry and refresh `history/STATUS.md`.
- Command: `history/tools/log-entry.sh . decision|problem|session "<title>" [--updates ID] [--supersedes ID] [--by "<tool/model>"] <<'EOF' … EOF`
  (no shell? append by hand in the exact format shown in `history/README.md`).
- Never put credentials or secrets into any history file.

Formats, rules and the reasoning behind them: `history/README.md`.
