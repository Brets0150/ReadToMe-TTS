import argparse
import logging
import sys


def main():
    parser = argparse.ArgumentParser(description="ReadToMe TTS")
    parser.add_argument(
        "--debug", action="store_true", help="Enable debug logging"
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    # Silence noisy third-party debug loggers
    logging.getLogger("PIL").setLevel(logging.INFO)

    from readtome.app import ReadToMeApp

    app = ReadToMeApp()
    app.run()


if __name__ == "__main__":
    main()
