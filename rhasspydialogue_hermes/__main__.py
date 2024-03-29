"""Hermes MQTT dialogue manager for Rhasspy"""
import argparse
import asyncio
import logging
import typing
from pathlib import Path

import paho.mqtt.client as mqtt
import rhasspyhermes.cli as hermes_cli

from . import DialogueHermesMqtt

_LOGGER = logging.getLogger("rhasspydialogue_hermes")

# -----------------------------------------------------------------------------


def main():
    """Main method."""
    parser = argparse.ArgumentParser(prog="rhasspy-dialogue-hermes")
    parser.add_argument(
        "--wakeword-id",
        action="append",
        help="Wakeword ID(s) to listen for (default=all)",
    )
    parser.add_argument(
        "--session-timeout",
        type=float,
        default=30.0,
        help="Seconds before a dialogue session times out (default: 30)",
    )
    parser.add_argument(
        "--sound",
        nargs=2,
        action="append",
        help="Add WAV id/path or directory of WAV files",
    )
    parser.add_argument(
        "--no-sound", action="append", help="Disable notification sounds for site id"
    )
    parser.add_argument(
        "--volume",
        type=float,
        help="Volume scalar for feedback sounds (0-1, default: 1)",
    )
    parser.add_argument(
        "--group-separator",
        help="String that separates site group from the rest of the site id (default: none)",
    )
    parser.add_argument(
        "--min-asr-confidence",
        type=float,
        help="Minimum ASR confidence/likelihood value before nluNotRecognized is produced",
    )
    parser.add_argument(
        "--say-chars-per-second",
        type=float,
        default=33.0,
        help="Number of characters to per second of speech for estimating TTS timeout",
    )
    parser.add_argument(
        "--sound-suffix",
        action="append",
        help="Add file extension (suffix) to search for with feedback sound path is a directory (e.g. '.wav')",
    )

    hermes_cli.add_hermes_args(parser)
    args = parser.parse_args()

    hermes_cli.setup_logging(args)
    _LOGGER.debug(args)

    sound_paths: typing.Dict[str, Path] = {
        sound[0]: Path(sound[1]) for sound in args.sound or []
    }

    if args.no_sound:
        _LOGGER.debug("Sound is disabled for sites %s", args.no_sound)

    if args.sound_suffix:
        args.sound_suffix = set(args.sound_suffix)

    # Listen for messages
    client = mqtt.Client()
    hermes = DialogueHermesMqtt(
        client,
        site_ids=args.site_id,
        wakeword_ids=args.wakeword_id,
        session_timeout=args.session_timeout,
        sound_paths=sound_paths,
        no_sound=args.no_sound,
        volume=args.volume,
        group_separator=args.group_separator,
        min_asr_confidence=args.min_asr_confidence,
        say_chars_per_second=args.say_chars_per_second,
        sound_suffixes=args.sound_suffix,
    )

    _LOGGER.debug("Connecting to %s:%s", args.host, args.port)
    hermes_cli.connect(client, args)
    client.loop_start()

    try:
        # Run event loop
        asyncio.run(hermes.handle_messages_async())
    except KeyboardInterrupt:
        pass
    finally:
        _LOGGER.debug("Shutting down")
        client.loop_stop()


# -----------------------------------------------------------------------------

if __name__ == "__main__":
    main()
