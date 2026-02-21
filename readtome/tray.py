import logging
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
import pystray

from readtome.config import Config, PITCH_PRESETS, SPEED_PRESETS

logger = logging.getLogger(__name__)


class TrayIcon:
    def __init__(
        self,
        on_quit,
        on_toggle_pause,
        on_configure_shortcut,
        on_change_voice,
        on_change_speed,
        on_change_pitch,
        on_toggle_startup,
        on_check_update,
        is_paused,
        get_status,
        get_voices,
        get_current_voice,
        get_current_speed,
        get_current_pitch,
    ):
        self._on_quit = on_quit
        self._on_toggle_pause = on_toggle_pause
        self._on_configure_shortcut = on_configure_shortcut
        self._on_change_voice = on_change_voice
        self._on_change_speed = on_change_speed
        self._on_change_pitch = on_change_pitch
        self._on_toggle_startup = on_toggle_startup
        self._on_check_update = on_check_update
        self._is_paused = is_paused
        self._get_status = get_status
        self._get_voices = get_voices
        self._get_current_voice = get_current_voice
        self._get_current_speed = get_current_speed
        self._get_current_pitch = get_current_pitch
        self._icon: pystray.Icon | None = None

    def _create_icon_image(self) -> Image.Image:
        if getattr(sys, "frozen", False):
            base = Path(sys._MEIPASS)
        else:
            base = Path(__file__).parent
        icon_path = base / "resources" / "icon.png"
        if icon_path.exists():
            return Image.open(icon_path)
        return self._generate_icon()

    @staticmethod
    def _generate_icon() -> Image.Image:
        img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.ellipse([4, 4, 60, 60], fill=(0, 120, 215))
        try:
            font = ImageFont.truetype("arial.ttf", 32)
        except OSError:
            font = ImageFont.load_default()
        draw.text((32, 32), "R", fill="white", font=font, anchor="mm")
        return img

    def _build_voice_menu(self):
        """Build submenu of available voice models."""
        voices = self._get_voices()
        if not voices:
            return pystray.Menu(
                pystray.MenuItem("No voices found", None, enabled=False),
            )

        items = []
        for voice_path in voices:
            name = voice_path.stem
            path_str = str(voice_path)

            def make_action(p):
                return lambda icon, item: self._on_change_voice(p)

            def make_checked(p):
                return lambda item: Path(self._get_current_voice()).resolve() == Path(p).resolve()

            items.append(
                pystray.MenuItem(
                    name,
                    make_action(path_str),
                    checked=make_checked(path_str),
                )
            )
        return pystray.Menu(*items)

    def _build_speed_menu(self):
        """Build submenu of speed presets."""
        items = []
        for label, value in SPEED_PRESETS.items():
            def make_action(v):
                return lambda icon, item: self._on_change_speed(v)

            def make_checked(v):
                return lambda item: abs(self._get_current_speed() - v) < 0.01

            items.append(
                pystray.MenuItem(
                    label,
                    make_action(value),
                    checked=make_checked(value),
                )
            )
        return pystray.Menu(*items)

    def _build_pitch_menu(self):
        """Build submenu of pitch presets."""
        items = []
        for label, value in PITCH_PRESETS.items():
            def make_action(v):
                return lambda icon, item: self._on_change_pitch(v)

            def make_checked(v):
                return lambda item: abs(self._get_current_pitch() - v) < 0.01

            items.append(
                pystray.MenuItem(
                    label,
                    make_action(value),
                    checked=make_checked(value),
                )
            )
        return pystray.Menu(*items)

    def _build_menu(self):
        return pystray.Menu(
            pystray.MenuItem(
                lambda item: self._get_status(), enabled=False, action=None
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Voice", self._build_voice_menu()),
            pystray.MenuItem("Speed", self._build_speed_menu()),
            pystray.MenuItem("Pitch", self._build_pitch_menu()),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                "Pause",
                self._on_toggle_pause,
                checked=lambda item: self._is_paused(),
            ),
            pystray.MenuItem("Configure Shortcut", self._on_configure_shortcut),
            pystray.MenuItem(
                "Start on Login",
                self._on_toggle_startup,
                checked=lambda item: Config.get_startup_enabled(),
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Check for Updates", self._on_check_update),
            pystray.MenuItem("Quit", self._on_quit),
        )

    def run(self):
        """Blocking call. Runs the tray icon event loop on the main thread."""
        self._icon = pystray.Icon(
            name="ReadToMe",
            icon=self._create_icon_image(),
            title="ReadToMe TTS",
            menu=self._build_menu(),
        )
        self._icon.run()

    def stop(self):
        if self._icon:
            self._icon.stop()

    def update_tooltip(self, text: str):
        if self._icon:
            # Windows tray tooltips have a 128 character limit
            self._icon.title = text[:127]

    def update_menu(self):
        """Rebuild the menu (e.g. after voice list changes)."""
        if self._icon:
            self._icon.menu = self._build_menu()
            self._icon.update_menu()
