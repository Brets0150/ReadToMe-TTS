# ReadToMe-TTS — Sessions (append-only)

One entry per work session: tool/model, what was done, ids logged, unfinished work, transcript file.
Append via `history/tools/log-entry.sh <project> session "<title>"`. Format: `history/README.md`.

### S-0001 — 2026-11-18 — v0.3.3 latency overhaul shipped; v0.4.0 features built, awaiting user test
- **Logged:** 2026-11-18 17:57 UTC by Claude Code / Fable 5
- **Tool/model:** Claude Code / Fable 5
- **Did:** Profiled and fixed hotkey-to-speech latency and inter-sentence pauses (v0.3.3: clipboard polling, synthesis/playback pipeline, persistent output stream, silence caps, model warmup). Diagnosed and fixed broken v0.3.3 installer (P-0001: Wine env had lost piper-tts). Implemented v0.4.0: stop shortcut (ctrl+alt default) + Stop Speaking tray item, Sentence/Comma Pause tray menus, shortcut conflict validation, build env guards. All unit tests pass (scratchpad suites); 0.4.0 installer built and smoke-tested under Wine (model loads, both hotkeys register).
- **Entries:** P-0001, D-0001, D-0002
- **Unfinished/next:** User to install+test dist/installer/ReadToMe_Setup_0.4.0.exe. On approval: commit all changes, tag v0.4.0, create GitHub release with installer+portable zips, push. Nothing committed yet.
- **Transcript file:** (Claude Code session 96140cbb, hooks not installed)

