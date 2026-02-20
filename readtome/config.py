import json
import logging
import sys
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

# Default Piper voice model (high-quality US English female)
DEFAULT_MODEL = "en_US-amy-medium.onnx"

# Pitch is applied as a sample rate multiplier during playback.
# > 1.0 = higher pitch, < 1.0 = lower pitch.
PITCH_PRESETS = {
    "Very Low": 0.80,
    "Low": 0.90,
    "Normal": 1.00,
    "High": 1.10,
    "Very High": 1.20,
}

SPEED_PRESETS = {
    "0.75x": 0.75,
    "1.0x": 1.0,
    "1.25x": 1.25,
    "1.5x": 1.5,
    "2.0x": 2.0,
}


@dataclass
class Config:
    hotkey: str = "alt+shift"
    speed: float = 1.0
    pitch: float = 1.0
    model_path: str = ""

    @classmethod
    def load(cls) -> "Config":
        config_path = cls._config_file()
        if config_path.exists():
            try:
                data = json.loads(config_path.read_text())
                return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
            except Exception as e:
                logger.warning("Failed to load config: %s, using defaults", e)
        return cls()

    def save(self):
        config_file = self._config_file()
        config_file.parent.mkdir(parents=True, exist_ok=True)
        config_file.write_text(json.dumps(self.__dict__, indent=2))

    @staticmethod
    def _config_file() -> Path:
        return Path.home() / ".readtome" / "config.json"

    def resolve_model_paths(self, base_dir: Path):
        default = str(base_dir / "models" / DEFAULT_MODEL)
        if not self.model_path or not Path(self.model_path).exists():
            self.model_path = default

    @staticmethod
    def get_base_dir() -> Path:
        if getattr(sys, "frozen", False):
            # PyInstaller 6.x extracts bundled data into _MEIPASS (_internal/)
            return Path(sys._MEIPASS)
        return Path(__file__).parent.parent

    @staticmethod
    def get_models_dir() -> Path:
        return Config.get_base_dir() / "models"

    @staticmethod
    def list_available_voices() -> list[Path]:
        """List all .onnx voice files in the models directory."""
        models_dir = Config.get_models_dir()
        if not models_dir.exists():
            return []
        voices = sorted(models_dir.glob("*.onnx"))
        return voices

    def get_voice_display_name(self) -> str:
        """Get a human-readable name from the model path."""
        return Path(self.model_path).stem if self.model_path else "Unknown"

    # ── Start on Login (Windows registry) ─────────────────────────────

    _REGISTRY_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
    _REGISTRY_NAME = "ReadToMe"

    @staticmethod
    def get_startup_enabled() -> bool:
        """Check if ReadToMe is set to start on login."""
        if sys.platform != "win32":
            return False
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, Config._REGISTRY_KEY, 0, winreg.KEY_READ)
            try:
                winreg.QueryValueEx(key, Config._REGISTRY_NAME)
                return True
            except FileNotFoundError:
                return False
            finally:
                winreg.CloseKey(key)
        except Exception:
            return False

    @staticmethod
    def set_startup_enabled(enabled: bool):
        """Add or remove ReadToMe from Windows startup."""
        if sys.platform != "win32":
            return
        import winreg
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, Config._REGISTRY_KEY, 0, winreg.KEY_SET_VALUE)
        try:
            if enabled:
                exe_path = sys.executable
                if getattr(sys, "frozen", False):
                    winreg.SetValueEx(key, Config._REGISTRY_NAME, 0, winreg.REG_SZ, f'"{exe_path}"')
                else:
                    # Dev mode: launch via python -m readtome
                    winreg.SetValueEx(key, Config._REGISTRY_NAME, 0, winreg.REG_SZ,
                                      f'"{exe_path}" -m readtome')
            else:
                try:
                    winreg.DeleteValue(key, Config._REGISTRY_NAME)
                except FileNotFoundError:
                    pass
        finally:
            winreg.CloseKey(key)
