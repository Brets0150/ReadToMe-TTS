# history/ — how this project's history is kept

Created 2026-11-18 by the documentation skill. This folder is the project's memory. It is plain Markdown so any
AI, tool or person can read and extend it. Nothing in the logs is ever rewritten or removed.

| File | What it is | Mutable? |
|---|---|---|
| `STATUS.md` | Current state, next steps, open problems, key facts. Rewritten at milestones and before a session ends. | yes (snapshot) |
| `SESSIONS.md` | One entry per work session: what was done, ids logged, what is unfinished. | append-only |
| `DECISIONS.md` | Every significant decision with its reasoning and outcome. | append-only |
| `PROBLEMS.md` | Every problem: symptoms, investigation, root cause, fix, result. | append-only |
| `sessions/` | Generated full transcripts (`YYYY-MM-DD_<id8>.md`), optional raw exports in `raw/`. | generated |
| `tools/` | `log-entry.sh` (append an entry), `history_tool.py` (transcript export/routing). | — |

## Entry format (what `tools/log-entry.sh` writes; copy it exactly if appending by hand)
```
### D-0007 — 2026-01-31 — Short title
- **Logged:** 2026-01-31 14:05 UTC by <tool/model>
- **Links:** supersedes D-0003            ← only when applicable
<body>
```
Ids are `D-`, `P-`, `S-` plus four digits, increasing by one within each file. Dates are UTC.
When an entry updates or supersedes an older one, a single pointer line is added directly under the old
entry's heading: `> Superseded by D-0007 (2026-01-31)` or `> Updated by P-0009 (…)`. That pointer is the
only change ever made to an existing entry.

### Decision body
- **Context:** the situation and constraints
- **Decision:** what was decided
- **Why:** the reasoning; what tipped it
- **Alternatives:** what else was considered and why not
- **Outcome:** what happened (or "pending"; log an update entry when known)

### Problem body
- **Symptoms:** what was observed, where, when; exact messages
- **Investigation:** what was checked, in order, and what each check showed
- **Root cause:** the actual cause (or "unknown")
- **Fix:** what was changed, and where
- **Result:** verified outcome; what remains
- **Status:** open | resolved | workaround | wontfix

### Session body
- **Tool/model:** e.g. Claude Code / <model>, or another assistant
- **Did:** what was done, in a few lines
- **Entries:** ids added this session (D-…, P-…)
- **Unfinished / next:** what the next session should pick up
- **Transcript:** `sessions/YYYY-MM-DD_<id8>.md` (if one was exported)

## Rules
- Log when it happens, not later. A session can end without warning.
- Never modify the logs except through `tools/log-entry.sh` or by appending in the format above.
- A changed decision or a disproved conclusion is a new entry that `--supersedes` / `--updates` the old id.
- Keep secrets out. Transcript export masks common credential patterns, but that is a safety net, not a guarantee.
- Transcripts are for grepping. Summaries live in `SESSIONS.md`; the handoff lives in `STATUS.md`.
