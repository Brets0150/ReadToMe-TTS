# Changelog

All notable changes to ReadToMe-TTS will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/), and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.4.0] - 2026-11-18

### Added
- **Stop Speaking shortcut** — a second global hotkey (default **Ctrl+Alt**) that stops the current speech without exiting the app. Configurable via the new "Configure Stop Shortcut" tray menu item; a "Stop Speaking" tray menu item does the same on click
- **Pause length menus** — "Sentence Pause" and "Comma Pause" tray submenus with presets from None to Very Long, replacing the config-file-only `sentence_pause_ms` / `comma_pause_ms` settings added in 0.3.3 (custom values can still be set in `config.json`)
- Shortcut conflict protection — the read and stop shortcuts cannot be set to combinations that would trigger each other (including a modifier-only shortcut that is a subset of the other)
- Tray tooltip now shows both the read and stop shortcuts
- Build scripts now verify the build environment (piper-tts present, numpy < 2) before building and verify the TTS engine actually made it into the bundle after building, failing loudly instead of producing a broken installer

### Changed
- "Configure Shortcut" tray menu item renamed to "Configure Read Shortcut"

## [0.3.3] - 2026-11-18

### Changed
- Much lower latency from hotkey press to speech:
  - Clipboard capture now polls for the copied text instead of a fixed 150ms wait, typically saving 100ms+ per hotkey press
  - A short warmup synthesis runs right after the voice model loads, so the first hotkey press no longer pays ONNX Runtime's slow first-inference cost
- Much shorter pauses between sentences:
  - Synthesis now runs ahead of playback in a pipeline — the next sentence is already synthesized when the current one finishes playing
  - Audio playback keeps one output stream open for the whole utterance instead of opening a new audio device per sentence (which cost 100ms+ each on Windows)
  - Long silences the voice model generates are automatically shortened: pauses at sentence ends/newlines are capped at 150ms and pauses around commas at 100ms (tunable via `sentence_pause_ms` and `comma_pause_ms` in `config.json`)
- Long selections start speaking sooner: text is fed to the synthesizer line by line, so phonemization of the whole selection no longer has to finish before the first sentence plays

## [0.3.2] - 2026-03-10

### Fixed
- Installer now silently uninstalls any previous version before installing, preventing duplicate entries in Programs and Features when the install directory changed (e.g. upgrading from a version that installed to Program Files (x86))
- Debug log no longer records any content of the highlighted text — only character count is logged

## [0.3.1] - 2026-02-23

### Fixed
- Hotkey now preserves the user's clipboard — original clipboard content is saved before Ctrl+C text capture and restored afterward

### Added
- "Goal of This Project" section in README

## [0.3.0] - 2026-02-21

### Added
- Check for Updates — menu option in system tray to check GitHub for newer releases, with automatic download and install for installed builds
- Configurable `GITHUB_REPO` constant in `readtome/__init__.py` so forks can point to their own repository
- File logging — application always writes to `%USERPROFILE%\.readtome\readtome.log` for troubleshooting
- Debug mode (`--debug` / `-d` flag) for verbose console and file logging
- Top-level exception handler captures fatal startup errors to the log file
- Microsoft Visual C++ Redistributable bundled in installer (installed silently, skipped if already present)
- Auto-install Python 3.12 — build scripts prompt to download and install if not found
- Portable zip builds: full (all 4 voices) and lite (Kristin only)
- "Lightweight by Design" and "What the Installer Does" transparency sections in README
- CHANGELOG.md for tracking version history

### Changed
- Default hotkey changed from Ctrl+Shift+S to Alt+Shift (modifier-only)
- Build process now 6 steps (added portable zips and VC++ Redistributable download)
- Version number read from pyproject.toml instead of hardcoded in build script
- Build scripts now require Python 3.12 (3.14+ has NumPy crash on target systems)
- Installer `AppSupportURL` corrected to point to the right GitHub repository

### Fixed
- Speech permanently stops working after interrupting playback with a rapid double hotkey press (stop event was never cleared between speech attempts)
- Application crash on clean systems due to Python 3.14 NumPy native extension incompatibility
- Application crash on target systems caused by NumPy 2.x ABI incompatibility with onnxruntime (pinned NumPy < 2.0)
- Installer now installs to `C:\Program Files\` instead of `C:\Program Files (x86)\` on 64-bit systems

## [0.2.0] - 2026-02-20

### Added
- System tray application with right-click configuration menu
- Global hotkey to capture highlighted text and read it aloud
- Support for any 2+ key combination as a hotkey, including modifier-only combos (e.g. Alt+Shift, Ctrl+Alt)
- Custom modifier-only hotkey detection via low-level keyboard hook
- Streaming TTS — audio playback begins as soon as the first sentence is synthesized
- Interrupt support — pressing the hotkey while speaking stops current speech and starts new
- Voice selection menu with checkmark for current voice
- Speed adjustment (0.75x to 2.0x)
- Pitch adjustment (Very Low to Very High)
- Pause/resume toggle
- Configure Shortcut — press any key combination to rebind the hotkey
- Start on Login toggle (Windows registry integration)
- Four bundled medium-quality US English voices: Amy (default), Kristin, Kusal, Ryan
- Voice model download scripts for all available Piper US English voices
- Windows installer built with Inno Setup (Start Menu, optional desktop icon, optional startup, uninstaller)
- Portable `.exe` build via PyInstaller (no installation required)
- Uninstaller cleans up config files and log files
- Cross-compilation support from Linux using Wine
- Developer setup scripts (`run-dev.ps1`, `run-dev.sh`) with automatic dependency and voice model setup

### Technical
- Built on Piper TTS for local neural text-to-speech (CPU only, no GPU required)
- PyInstaller packaging with targeted onnxruntime collection to minimize build size
- Builds to local temp directory to avoid UNC network share locking issues
- Path comparison using `Path.resolve()` for reliable behavior on network drives
- Wait-for-key-release before Ctrl+C send to fix text capture with modifier-only hotkeys

## [0.1.0] - 2026-02-19

### Added
- Initial prototype with basic hotkey and TTS functionality
