# ReadToMe-TTS — Problems (append-only)

Each entry: symptoms, investigation, root cause, fix, result, status. New entries go at the end via
`history/tools/log-entry.sh <project> problem "<title>"`. Progress on an open problem is a new entry that
`--updates` the old id; the old entry stays. Format: `history/README.md`.

### P-0001 — 2026-11-18 — Wine build env lost piper-tts; installer shipped without TTS engine
- **Logged:** 2026-11-18 17:48 UTC by Claude Code / Fable 5
- **Symptoms:** Freshly built v0.3.3 installer worked but the app hung forever at "Loading model" in the tray status after install. The build itself exited 0 and produced a normal-looking installer (269 MB).
- **Investigation:** The app's status text shows "Loading model..." both when loading hangs AND when the load thread throws, so it gave no clue. The PyInstaller build log had the real evidence: `ERROR: Hidden import 'piper.voice' not found` and `WARNING: collect_data_files - skipping data collection for module 'piper'` — but PyInstaller treats missing hidden imports as NON-FATAL warnings, so the build "succeeded". `wine python -m pip list` in the ~/.wine-readtome prefix showed piper-tts was gone and `kokoro-onnx 0.5.0` + `numpy 2.4.2` present instead: a Kokoro TTS experiment at some point modified the shared Wine build prefix, removing piper-tts and pulling numpy 2.x (project pins numpy<2 for PyInstaller compatibility).
- **Root cause:** The Wine build environment (~/.wine-readtome, used by build-linux.sh) is shared mutable state. setup-wine.sh installed unpinned packages, and nothing in build-linux.sh verified that the packages the app needs are importable before building or present in the bundle after building.
- **Fix:** (1) Reinstalled `piper-tts==1.4.1` and `numpy==1.26.4` into the Wine Python. (2) build-linux.sh now fails preflight if `import piper.voice` fails or numpy>=2 in the Wine Python, and fails post-build if `_internal/piper`, `_internal/piper/espeak-ng-data`, `_internal/models`, or `_internal/onnxruntime` are missing from the bundle. (3) setup-wine.sh now pins `piper-tts==1.4.1` and `numpy<2`. (4) Verification procedure: run the frozen exe headless with `xvfb-run wine dist/ReadToMe/ReadToMe.exe -d` and check `~/.wine-readtome/drive_c/users/<user>/.readtome/readtome.log` for "Voice loaded" + "Model loaded, ready to use" before shipping.
- **Result:** Rebuilt installer grew 269→293 MB (the missing engine), smoke test under Wine showed the full healthy startup sequence, and the user confirmed the reinstalled 0.3.3 works. Future builds now fail loudly instead of shipping silently broken.
- **Status:** resolved


### P-0002 — 2026-11-18 — Tray right-click menu appeared broken after 0.4.0 install
- **Logged:** 2026-11-18 21:03 UTC by Claude Code / Fable 5
- **Symptoms:** After installing v0.4.0, right-clicking the tray icon showed no menu at all on the user's machine.
- **Investigation:** Verified the menu code with the real pystray 0.19.5 win32 backend under Wine: walked the full menu tree (all items, checkmarks, submenus evaluate cleanly) and forced the native HMENU build (`icon._update_menu()`), which succeeded with all 63 callbacks. Useful to know: pystray's win32 right-click handler is `elif self._menu_handle and lparam == WM_RBUTTONUP` — if the HMENU failed to build, right-click silently does nothing; and Windows leaves "ghost" tray icons for dead processes that ignore clicks until hovered. Neither applied here.
- **Root cause:** Not a ReadToMe bug — a third-party screen overlay on the user's machine was intercepting/blocking the popup menu.
- **Fix:** None needed in ReadToMe; user resolved the overlay conflict locally.
- **Result:** Menu works; user confirmed v0.4.0 functions correctly. The Wine menu-realization test script pattern is worth reusing when tray/menu regressions are suspected (pystray menus can't be exercised by just launching the app headless).
- **Status:** resolved

