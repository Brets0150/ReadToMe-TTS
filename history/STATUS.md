# STATUS — ReadToMe-TTS

_Last updated: 2026-11-18 by Claude Code / Fable 5_

## Current state
- v0.4.0 complete: user installed and confirmed working (latency overhaul, stop shortcut, pause menus). Tray-menu scare was an external overlay on the user's machine, not a bug (P-0002).
- Committed and tagged v0.4.0 locally. Release assets built and verified in `dist/`:
  `ReadToMe_Setup_0.4.0.exe`, `ReadToMe_Portable_0.4.0.zip` (all 4 voices), `ReadToMe_Portable_lite_0.4.0.zip` (Kristin only) — same pattern as the v0.3.2 GitHub release.
- **Pending: push + GitHub release.** This machine has no GitHub credentials (no gh CLI, no stored token), so the push and release upload need the user's auth. Release notes draft: `dist/release_notes_0.4.0.md`.

## Next steps
1. Push `main` + tag `v0.4.0` to origin (needs user credentials).
2. Create GitHub release v0.4.0 (name = tag, short prose body from `dist/release_notes_0.4.0.md`) and upload the three `dist/` assets.
3. Consider committing a `tests/` directory (standalone suites currently live only in the Claude session scratchpad).

## Key facts
- Build: `./build-linux.sh` — now also creates the portable zips (parity with build.bat) and verifies the build env + bundle contents (see P-0001; do NOT let other experiments touch `~/.wine-readtome`).
- Release pattern: tag `vX.Y.Z` = release name; 3 assets (setup exe, portable zip, lite zip with Kristin only, exe+_internal at zip root); short prose body referencing the CHANGELOG.
- Version lives in: pyproject.toml, readtome/__init__.py, installer/ReadToMe_Setup.iss (build scripts read pyproject).
- Pre-ship smoke test: `xvfb-run wine dist/ReadToMe/ReadToMe.exe -d`, then check `~/.wine-readtome/drive_c/users/<user>/.readtome/readtome.log` for "Voice loaded" / "ready to use" / both hotkeys registered.
- Debug mode (`-d`) leaks synthesized text via piper's own logger (undermines 0.3.2 privacy fix) — known, unfixed.

## Open problems
- None (P-0001, P-0002 resolved).
