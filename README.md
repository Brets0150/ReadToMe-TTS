# ReadToMe-TTS

A Windows system tray application that reads highlighted text aloud using a local neural text-to-speech engine. Highlight text anywhere on your screen, press a keyboard shortcut, and hear it spoken back to you — no internet connection required.

Built with [Piper TTS](https://github.com/rhasspy/piper) for fast, high-quality local speech synthesis.

> **Windows only.** This application was designed and tested exclusively for Windows. It has not been written for or tested on Linux or macOS.

## Table of Contents

- [Lightweight by Design](#lightweight-by-design)
- [Quick Start](#quick-start)
- [How It Works](#how-it-works)
- [Configuration](#configuration)
  - [Hotkey Tips](#hotkey-tips)
- [What the Installer Does](#what-the-installer-does)
  - [Files Installed](#files-installed)
  - [Third-Party Software Installed](#third-party-software-installed)
  - [Registry Entries](#registry-entries)
  - [Optional Shortcuts](#optional-shortcuts)
  - [What the Uninstaller Removes](#what-the-uninstaller-removes)
  - [What ReadToMe Does NOT Do](#what-readtome-does-not-do)
- [Troubleshooting](#troubleshooting)
- [Developer Setup](#developer-setup)
  - [Quick Start (Developer Mode)](#quick-start-developer-mode)
  - [Manual Setup](#manual-setup)
- [Building the Installer](#building-the-installer)
  - [Building on Windows](#building-on-windows)
  - [Cross-Compiling from Linux](#cross-compiling-from-linux)
- [Voice Models](#voice-models)
  - [Bundled Voices](#bundled-voices)
  - [Downloading Additional Voices](#downloading-additional-voices)
  - [Repackaging with Different Voices](#repackaging-with-different-voices)
- [Project Scripts](#project-scripts)
- [Project Structure](#project-structure)
- [Dependencies](#dependencies)
- [License](#license)

### Lightweight by Design

ReadToMe was designed to run on **CPU only** — no GPU or dedicated graphics hardware is required. One of the core goals of this project is to make text-to-speech accessible on as many systems as possible, including resource-constrained environments.

In testing, ReadToMe runs well on:
- **Virtual machines** (including cloud-hosted VMs with no GPU passthrough)
- **Desktops and servers with no dedicated graphics card**
- **Systems with limited CPU resources**

Even on modest hardware, the time from pressing the hotkey to hearing speech is **one second or less**. The Piper TTS engine is optimized for fast CPU inference, so you get near-instant, natural-sounding speech without heavy resource demands.

## Quick Start

The fastest way to get started is to download the installer from the [Releases](../../releases) page and run it on your Windows system. The installer includes four bundled voice models and everything you need — no Python or additional setup required.

## How It Works

ReadToMe works by simulating a **Ctrl+C** copy when you press the configured hotkey. It copies whatever text you have highlighted, sends it through a local Piper TTS voice model, and plays the audio through your speakers.

**This means it works anywhere Ctrl+C works to copy text:** web browsers, text editors, PDF viewers, Word documents, email clients, and most standard Windows applications.

### Known Limitation

Because the app relies on Ctrl+C to capture text, **it will not work in applications where Ctrl+C does something other than copy.** The most common example is terminal/command prompt windows, where Ctrl+C sends an interrupt signal to stop a running command rather than copying text. In these environments, the hotkey will not capture any text. As a rule of thumb: if you can highlight text and press Ctrl+C to copy it to your clipboard, ReadToMe will work there.

## Configuration

There is **no standalone settings window or GUI.** All configuration is done through the **system tray icon**.

After launching ReadToMe, look for the icon in your Windows system tray (bottom-right of the taskbar, you may need to click the up arrow to expand hidden icons). **Right-click** the icon to access the settings menu:

| Menu Item | Description |
|---|---|
| **Voice** | Choose from available Piper voice models (checkmark shows current) |
| **Speed** | Adjust reading speed (0.75x to 2.0x) |
| **Pitch** | Adjust voice pitch (Very Low to Very High) |
| **Pause** | Temporarily disable the hotkey (toggle) |
| **Configure Shortcut** | Set a new hotkey — any 2+ key combination, including modifier-only combos |
| **Start on Login** | Toggle automatic startup when you log into Windows |
| **Quit** | Exit the application |

The default hotkey is **Alt+Shift**. Your settings are saved to `%USERPROFILE%\.readtome\config.json` and persist across restarts.

### Hotkey Tips

ReadToMe supports any key combination with at least two keys, including **modifier-only** combinations like Alt+Shift or Ctrl+Alt.

Using modifier-only hotkeys is recommended because many applications — especially **remote desktop clients** (RDP, Citrix, VMware Horizon, etc.) — perform full keystroke capture and forward all key combinations to the remote system. This means a hotkey like Ctrl+Shift+S pressed locally would be sent to the remote machine instead of triggering ReadToMe. Modifier keys on their own, however, are typically not forwarded in the same way, so a modifier-only hotkey like Alt+Shift will reliably trigger ReadToMe on the local machine regardless of what application has focus.

## What the Installer Does

ReadToMe is fully open source and we believe in complete transparency about what gets installed on your system. Here is everything the installer does and why.

### Files Installed

| What | Location | Why |
|---|---|---|
| ReadToMe application | `C:\Program Files\ReadToMe\` | The main application and all of its bundled dependencies (see [Dependencies](#dependencies) below). This is a self-contained build — **no Python installation is required**. The application, the Python runtime, and all libraries are packaged together by [PyInstaller](https://pyinstaller.org/). |
| Voice model files | `C:\Program Files\ReadToMe\models\` | Four [Piper TTS](https://github.com/rhasspy/piper) neural voice models (`.onnx` files). These are the AI models that convert text to speech locally on your machine. No data is sent to the internet. |
| Tray icon | `C:\Program Files\ReadToMe\readtome\resources\` | The system tray icon image displayed in your taskbar. |
| User config | `%USERPROFILE%\.readtome\config.json` | Your settings (selected voice, hotkey, speed, pitch). Created on first launch, not by the installer. |
| Log file | `%USERPROFILE%\.readtome\readtome.log` | Application log for troubleshooting. Created on first launch. |

### Third-Party Software Installed

| What | Why | Details |
|---|---|---|
| **Microsoft Visual C++ Redistributable** | Required runtime for Python and the ONNX neural network engine that powers text-to-speech. Without it, the application will silently fail to start on systems that don't already have it. | This is the official Microsoft package (`vc_redist.x64.exe`) downloaded from [Microsoft's website](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist). It is installed silently and only if your system doesn't already have it. Most Windows systems already have this installed by other software — in that case, the installer skips it entirely. |

### Registry Entries

| Key | Purpose | When |
|---|---|---|
| `HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\{...}` | Standard Windows uninstaller entry so ReadToMe appears in "Add or Remove Programs" | Always (created by Inno Setup) |
| `HKCU\Software\Microsoft\Windows\CurrentVersion\Run\ReadToMe` | Starts ReadToMe automatically when you log in | Only if you check "Start ReadToMe when Windows starts" during install |

### Optional Shortcuts

| Shortcut | When |
|---|---|
| Start Menu entry | Always |
| Desktop shortcut | Only if you check "Create a desktop icon" during install |

### What the Uninstaller Removes

The uninstaller (accessible from "Add or Remove Programs") will:
1. Stop any running ReadToMe process
2. Remove all files from the installation directory (`C:\Program Files\ReadToMe\`)
3. Remove the Start Menu and desktop shortcuts
4. Remove the Windows startup registry entry (if it was created)
5. Delete your config file and log file from `%USERPROFILE%\.readtome\`

The uninstaller does **not** remove the Microsoft Visual C++ Redistributable, as other software on your system may depend on it.

### What ReadToMe Does NOT Do

- Does **not** send any data over the internet — all text-to-speech processing happens locally on your machine
- Does **not** install any background services or drivers
- Does **not** modify any system files
- Does **not** collect telemetry, analytics, or usage data

## Troubleshooting

### Application won't start / silently exits

ReadToMe always writes a log file to `%USERPROFILE%\.readtome\readtome.log`. Check this file for error details.

For more verbose output, open a Command Prompt and run:

```cmd
"C:\Program Files\ReadToMe\ReadToMe.exe" -d
```

The `-d` (debug) flag enables detailed logging to both the log file and the console window.

### Speech stops working after changing settings

Occasionally, changing the voice, hotkey, or speed while the application is running may cause it to stop reading aloud. If this happens, close ReadToMe from the system tray and reopen it. Your configuration changes are saved automatically and will persist — the app should work normally after restarting.

### Debug mode from a portable build

If you're using the portable `.exe` (not the installer), open a Command Prompt in the same directory and run:

```cmd
ReadToMe.exe -d
```

## Developer Setup

### Prerequisites

- **Python 3.12** (required — see note below)
- Windows (for running the app)

> **Why Python 3.12?** The built executable bundles the Python runtime and all native extensions. Python 3.14+ has known compatibility issues with NumPy's native libraries that cause the packaged application to crash on target systems. Python 3.12 is the most widely deployed version with the best library compatibility for PyInstaller builds. The build scripts enforce this version automatically.

### Quick Start (Developer Mode)

The easiest way to get a fully working development environment:

```powershell
.\run-dev.ps1
```

This script will:
1. Create a Python virtual environment (`.venv/`)
2. Install all dependencies including dev/build tools (PyInstaller, pytest)
3. Download the 4 bundled voice models (amy, kristin, kusal, ryan) if missing
4. Check for and install [Inno Setup](https://jrsoftware.org/isinfo.php) if not present (needed by `build.bat` to create the Windows installer — see [Building the Installer](#building-the-installer) for details)
5. Launch ReadToMe in debug mode with verbose logging

Optional flags:
- `.\run-dev.ps1 -NoBuild` — skip the Inno Setup check
- `.\run-dev.ps1 -NoLaunch` — set up the environment without launching the app

On Linux:

```bash
./run-dev.sh                # Full setup + launch
./run-dev.sh --no-launch    # Setup only
```

### Manual Setup

If you prefer to set things up manually:

```powershell
# Create and activate virtual environment (must use Python 3.12)
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install in editable mode with dev dependencies
pip install -e ".[dev]"

# Download the 4 bundled voice models
.\download-voices.ps1
# Or download just one manually — each voice needs both .onnx and .onnx.json files
# placed in the models/ directory

# Run in debug mode
python -m readtome --debug
```

## Building the Installer

The build process has two stages:

1. **PyInstaller** packages the Python application and all its dependencies into a standalone portable `.exe` with no Python installation required. This is installed automatically as a Python dev dependency.
2. **[Inno Setup](https://jrsoftware.org/isinfo.php)** takes that portable build and wraps it into a proper Windows installer (`.exe`) with Start Menu shortcuts, optional desktop icon, optional startup entry, and an uninstaller. Inno Setup is a free, standalone Windows program — it is not a Python package and must be installed separately.

If you only need the portable `.exe`, you can skip Inno Setup. The build script will still produce `dist\ReadToMe\ReadToMe.exe`. The installer is only needed if you want to distribute a setup wizard that installs ReadToMe into Program Files.

### Building on Windows

The build script handles everything automatically, including setting up a virtual environment and installing Inno Setup if needed:

```powershell
.\build.bat
```

The build script will:
1. Create a `.venv` and install all dependencies (if not already present)
2. Build the portable `.exe` with PyInstaller (builds to a local temp directory for speed)
3. Create portable zip files — a full zip with all 4 voices and a lite zip with only the Kristin voice
4. Download the [Microsoft Visual C++ Redistributable](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist) (`vc_redist.x64.exe`) to `redist/` if not already present — this is bundled into the installer so end users don't need to install it separately
5. Download and install [Inno Setup 6](https://jrsoftware.org/isinfo.php) if not found (silent install)
6. Build the Windows installer with Inno Setup

Output:
- `dist\ReadToMe\ReadToMe.exe` — Portable application (no install needed, just run it)
- `dist\ReadToMe_Portable_<version>.zip` — Full portable zip with all 4 bundled voices
- `dist\ReadToMe_Portable_lite_<version>.zip` — Lite portable zip with Kristin voice only
- `dist\installer\ReadToMe_Setup_<version>.exe` — Windows installer with setup wizard

> **Note:** If the build reports that `dist\ReadToMe` is locked, close any running `ReadToMe.exe` or File Explorer windows that have the dist folder open, then re-run `build.bat`.

### Cross-Compiling from Linux

You can build the Windows installer from a Linux machine using Wine:

```bash
# One-time setup (installs Wine, Python, Inno Setup, dependencies)
./setup-wine.sh

# Build the installer
./build-linux.sh
```

The setup script installs everything into an isolated Wine prefix at `~/.wine-readtome/`.

## Voice Models

ReadToMe uses [Piper](https://github.com/rhasspy/piper) voice models. Each voice requires two files: an `.onnx` model file and its corresponding `.onnx.json` config file. These are placed in the `models/` directory.

### Bundled Voices

The installer ships with four medium-quality US English voices:

| Voice | Description |
|---|---|
| Amy | Female voice (default) |
| Kristin | Female voice |
| Kusal | Male voice |
| Ryan | Male voice |

### Downloading Additional Voices

To download all 20 available US English voices (27 variants across low/medium/high quality):

```powershell
# Windows
.\download-voices.ps1

# Linux/macOS
./download-voices.sh
```

These scripts download from the [Piper voices repository](https://huggingface.co/rhasspy/piper-voices/tree/main/en/en_US) on Hugging Face. Already-downloaded voices are skipped.

### Repackaging with Different Voices

If you want to build a custom installer with a different set of bundled voices:

1. Place the desired `.onnx` and `.onnx.json` files in the `models/` directory
2. Edit `readtome.spec` to list the voice files you want bundled in the `datas` section:
   ```python
   datas=[
       (os.path.join("models", "en_US-yourvoice-medium.onnx"), "models"),
       (os.path.join("models", "en_US-yourvoice-medium.onnx.json"), "models"),
       # ... add more voices as needed
   ]
   ```
3. Optionally update the default voice in `readtome/config.py` by changing `DEFAULT_MODEL`
4. Build the installer with `build.bat` or `./build-linux.sh`

Voice models can be browsed at: https://huggingface.co/rhasspy/piper-voices/tree/main/en/en_US

Each voice subdirectory contains quality variants (low, medium, high). Medium quality offers the best balance of file size and audio quality for most use cases.

## Project Scripts

| Script | Platform | Purpose |
|---|---|---|
| `run-dev.ps1` / `run-dev.sh` | Windows / Linux | Full developer setup: venv, deps, 4 bundled voices, Inno Setup, launch in debug mode |
| `download-voices.ps1` / `download-voices.sh` | Windows / Linux | Download all available Piper US English voice models |
| `build.bat` | Windows | Build the portable .exe and installer (auto-installs build tools) |
| `build-linux.sh` | Linux | Cross-compile the Windows installer using Wine |
| `setup-wine.sh` | Linux | One-time setup of Wine build environment for cross-compilation |

## Project Structure

```
ReadToMe-TTS/
├── readtome/
│   ├── __init__.py            # Version
│   ├── __main__.py            # Entry point, --debug flag
│   ├── app.py                 # Main orchestrator, wires all components
│   ├── tray.py                # System tray icon and menu
│   ├── hotkey.py              # Global hotkey and clipboard text capture
│   ├── tts_engine.py          # Piper TTS model wrapper
│   ├── audio_player.py        # Audio playback via sounddevice
│   ├── config.py              # Settings, presets, startup registry
│   └── resources/             # Tray icon assets
├── hooks/
│   └── hook-sounddevice.py    # PyInstaller hook for sounddevice module
├── models/                    # Voice model files (git-ignored)
├── redist/                    # VC++ Redistributable for installer (git-ignored)
├── installer/
│   └── ReadToMe_Setup.iss     # Inno Setup installer script
├── pyproject.toml             # Python project config and dependencies
├── readtome.spec              # PyInstaller build spec
└── CHANGELOG.md               # Version history and release notes
```

## Dependencies

| Package | Purpose |
|---|---|
| `piper-tts` | Local neural text-to-speech engine |
| `sounddevice` | Audio playback |
| `keyboard` | Global hotkey listener |
| `pyperclip` | Clipboard access |
| `pystray` | Windows system tray icon |
| `Pillow` | Tray icon image handling |
| `numpy` | Audio sample processing |

Dev/build dependencies (installed via `pip install -e ".[dev]"`):

| Package | Purpose |
|---|---|
| `pyinstaller` | Package app into standalone Windows .exe |
| `pytest` | Testing framework |

## License

This project is provided as-is for personal use.
