# ReadToMe-TTS

A Windows system tray application that reads highlighted text aloud using a local neural text-to-speech engine. Highlight text anywhere on your screen, press a keyboard shortcut, and hear it spoken back to you — no internet connection required.

Built with [Piper TTS](https://github.com/rhasspy/piper) for fast, high-quality local speech synthesis.

> **Windows only.** This application was designed and tested exclusively for Windows. It has not been written for or tested on Linux or macOS.

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

## Developer Setup

### Prerequisites

- Python 3.10 or newer
- Windows (for running the app)

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
# Create and activate virtual environment
python -m venv .venv
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
3. Download and install [Inno Setup 6](https://jrsoftware.org/isinfo.php) if not found (silent install)
4. Build the Windows installer with Inno Setup

Output:
- `dist\ReadToMe\ReadToMe.exe` — Portable application (no install needed, just run it)
- `dist\installer\ReadToMe_Setup_0.2.0.exe` — Windows installer with setup wizard

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
├── installer/
│   └── ReadToMe_Setup.iss     # Inno Setup installer script
├── pyproject.toml             # Python project config and dependencies
└── readtome.spec              # PyInstaller build spec
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
