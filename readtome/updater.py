import ctypes
import json
import logging
import os
import subprocess
import sys
import tempfile
import urllib.request
import webbrowser

from readtome import __version__, GITHUB_REPO

logger = logging.getLogger(__name__)

# GitHub API endpoint for latest release
_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
_RELEASES_URL = f"https://github.com/{GITHUB_REPO}/releases/latest"

# Windows MessageBox styles
_MB_OK = 0x00000000
_MB_YESNO = 0x00000004
_MB_ICONINFORMATION = 0x00000040
_MB_ICONWARNING = 0x00000030
_MB_ICONERROR = 0x00000010
_IDYES = 6


def _parse_version(version_str: str) -> tuple[int, ...]:
    """Parse a version string like '0.2.0' or 'v0.2.0' into a tuple of ints."""
    v = version_str.strip().lstrip("v")
    try:
        return tuple(int(x) for x in v.split("."))
    except (ValueError, AttributeError):
        return (0,)


def _message_box(title: str, text: str, style: int) -> int:
    """Show a Windows message box. Returns button ID clicked."""
    try:
        return ctypes.windll.user32.MessageBoxW(0, text, title, style)
    except Exception:
        logger.error("Failed to show message box: %s", text)
        return 0


def check_for_update() -> None:
    """Check GitHub for a newer release and prompt the user if one is found."""
    logger.info("Checking for updates at %s", _API_URL)

    try:
        req = urllib.request.Request(
            _API_URL,
            headers={"Accept": "application/vnd.github.v3+json",
                      "User-Agent": "ReadToMe-TTS"},
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        logger.error("Update check failed: %s", e)
        _message_box(
            "ReadToMe - Update Check",
            f"Could not check for updates.\n\n{e}",
            _MB_OK | _MB_ICONWARNING,
        )
        return

    remote_tag = data.get("tag_name", "")
    remote_version = _parse_version(remote_tag)
    local_version = _parse_version(__version__)

    logger.info("Local version: %s, Remote version: %s", __version__, remote_tag)

    if remote_version <= local_version:
        _message_box(
            "ReadToMe - Up to Date",
            f"You are running the latest version (v{__version__}).",
            _MB_OK | _MB_ICONINFORMATION,
        )
        return

    # Newer version available
    release_name = data.get("name", remote_tag)
    release_url = data.get("html_url", _RELEASES_URL)

    _prompt_and_install(data, release_name, remote_tag, release_url)


def _prompt_and_install(
    release_data: dict, release_name: str, remote_tag: str, release_url: str
) -> None:
    """Ask the user if they want to update, then handle download/install."""
    is_installed = getattr(sys, "frozen", False)

    if is_installed:
        msg = (
            f"A new version of ReadToMe is available!\n\n"
            f"Current version: v{__version__}\n"
            f"New version: {remote_tag}\n\n"
            f"Would you like to download and install the update?\n\n"
            f"The installer will close ReadToMe, install the update,\n"
            f"and offer to relaunch when finished."
        )
    else:
        msg = (
            f"A new version of ReadToMe is available!\n\n"
            f"Current version: v{__version__}\n"
            f"New version: {remote_tag}\n\n"
            f"Would you like to open the download page?"
        )

    result = _message_box(
        "ReadToMe - Update Available",
        msg,
        _MB_YESNO | _MB_ICONINFORMATION,
    )

    if result != _IDYES:
        logger.info("User declined update")
        return

    if not is_installed:
        logger.info("Opening releases page: %s", release_url)
        webbrowser.open(release_url)
        return

    # Find the installer asset in the release
    installer_asset = _find_installer_asset(release_data)
    if not installer_asset:
        logger.warning("No installer asset found in release, opening browser")
        _message_box(
            "ReadToMe - Update",
            "Could not find the installer in this release.\n\n"
            "Opening the download page instead.",
            _MB_OK | _MB_ICONWARNING,
        )
        webbrowser.open(release_url)
        return

    # Download and launch the installer
    _download_and_launch(installer_asset)


def _find_installer_asset(release_data: dict) -> dict | None:
    """Find the ReadToMe_Setup_*.exe asset in the release."""
    for asset in release_data.get("assets", []):
        name = asset.get("name", "")
        if name.startswith("ReadToMe_Setup_") and name.endswith(".exe"):
            return asset
    return None


def _download_and_launch(asset: dict) -> None:
    """Download the installer to %TEMP% and launch it, then exit."""
    download_url = asset.get("browser_download_url", "")
    file_name = asset.get("name", "ReadToMe_Setup.exe")
    dest_path = os.path.join(tempfile.gettempdir(), file_name)

    logger.info("Downloading update: %s -> %s", download_url, dest_path)

    try:
        req = urllib.request.Request(
            download_url,
            headers={"User-Agent": "ReadToMe-TTS"},
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            with open(dest_path, "wb") as f:
                while True:
                    chunk = resp.read(65536)
                    if not chunk:
                        break
                    f.write(chunk)
    except Exception as e:
        logger.error("Download failed: %s", e)
        _message_box(
            "ReadToMe - Update Failed",
            f"Failed to download the update.\n\n{e}",
            _MB_OK | _MB_ICONERROR,
        )
        return

    logger.info("Download complete, launching installer: %s", dest_path)

    try:
        subprocess.Popen([dest_path], creationflags=subprocess.DETACHED_PROCESS)
    except Exception as e:
        logger.error("Failed to launch installer: %s", e)
        _message_box(
            "ReadToMe - Update Failed",
            f"Downloaded the update but failed to launch the installer.\n\n"
            f"The installer is saved at:\n{dest_path}\n\n"
            f"You can run it manually.",
            _MB_OK | _MB_ICONERROR,
        )
        return

    logger.info("Installer launched, exiting ReadToMe")
    sys.exit(0)
