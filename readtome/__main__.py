import argparse
import logging
import sys
import traceback
from pathlib import Path


def _get_log_dir() -> Path:
    """Return the ReadToMe config/log directory, creating it if needed."""
    log_dir = Path.home() / ".readtome"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir


def main():
    parser = argparse.ArgumentParser(description="ReadToMe TTS")
    parser.add_argument(
        "--debug", "-d", action="store_true", help="Enable debug logging"
    )
    args = parser.parse_args()

    log_level = logging.DEBUG if args.debug else logging.INFO
    log_file = _get_log_dir() / "readtome.log"

    handlers: list[logging.Handler] = [
        logging.FileHandler(log_file, encoding="utf-8"),
    ]

    # If launched from a console (e.g. cmd /k ReadToMe.exe --debug),
    # also print to stdout so the user can see output in real time.
    if args.debug:
        handlers.append(logging.StreamHandler(sys.stdout))

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=handlers,
    )

    # Silence noisy third-party debug loggers
    logging.getLogger("PIL").setLevel(logging.INFO)

    logger = logging.getLogger(__name__)
    logger.info("ReadToMe starting (debug=%s, log=%s)", args.debug, log_file)

    from readtome.app import ReadToMeApp

    app = ReadToMeApp()
    app.run()


if __name__ == "__main__":
    try:
        main()
    except Exception:
        # Last-resort: write the traceback to the log file even if logging
        # hasn't been configured yet (e.g. crash during early startup).
        try:
            log_file = _get_log_dir() / "readtome.log"
            with open(log_file, "a", encoding="utf-8") as f:
                f.write("\n=== FATAL ERROR ===\n")
                traceback.print_exc(file=f)
        except Exception:
            pass
        raise
