import json
import argparse
import logging
import spectrum_instruments.driver as driver
from sipyco.pc_rpc import simple_server_loop
from sipyco import common_args


def add_common_args(parser):
    parser.add_argument("--debug", action="store_true")
    parser.add_argument(
        "--serial-number",
        type=int,
        required=True,
        help="Spectrum card serial number",
    )
    parser.add_argument(
        "--output-voltage",
        type=float,
        default=0.15,
        help="Maximum output voltage in V (default: 0.15 V)",
    )
    parser.add_argument(
        "--sample-rate", type=float, default=1e9, help="Sampling rate in Hz"
    )


def get_argparser():
    parser = argparse.ArgumentParser()

    subparsers = parser.add_subparsers(dest="command", required=True)

    subparser_list = subparsers.add_parser("list")
    subparser_list.add_argument(
        "-o", "--output", choices=["json"], default="json", help="Output format"
    )

    subparser_tone = subparsers.add_parser("tone", help="Generate a continuous tone")
    add_common_args(subparser_tone)
    subparser_tone.add_argument(
        "--frequency", "-f", type=float, required=True, help="Tone frequency in Hz"
    )

    subparser_sweep = subparsers.add_parser("sweep", help="Generate a frequency sweep")
    add_common_args(subparser_sweep)
    subparser_sweep.add_argument(
        "--center", type=float, required=True, help="Center freq (Hz)"
    )
    subparser_sweep.add_argument(
        "--span", type=float, required=True, help="Span freq (Hz)"
    )
    subparser_sweep.add_argument(
        "--duration", "-d", type=float, required=True, help="Duration (s)"
    )

    subparser_pulse = subparsers.add_parser("pulse", help="Generate a single pulse")
    add_common_args(subparser_pulse)
    subparser_pulse.add_argument(
        "--duration", "-d", type=float, required=True, help="Pulse duration (s)"
    )
    subparser_pulse.add_argument(
        "--frequency", "-f", type=float, default=200e6, help="Carrier frequency (Hz)"
    )

    subparser_rpc = subparsers.add_parser("rpc", help="Run the RPC server")
    common_args.simple_network_args(subparser_rpc, 3249)
    common_args.verbosity_args(subparser_rpc)
    add_common_args(subparser_rpc)

    return parser


def main():
    args = get_argparser().parse_args()

    level = logging.DEBUG if args.debug else logging.WARNING
    logging.basicConfig(level=level, format="%(asctime)s %(levelname)s: %(message)s")

    if args.command == "list":
        devices = driver.list_devices()
        if args.output == "json":
            print(json.dumps(devices, indent=2))
    else:
        try:
            siggen = driver.SignalGenerator(
                serial_number=args.serial_number,
                sample_rate=args.sample_rate,
                output_voltage=args.output_voltage,
                verbose=args.debug,
            )

            if args.command in ["tone", "sweep", "pulse"]:
                if args.command == "tone":
                    siggen.tone(frequency=args.frequency)
                elif args.command == "sweep":
                    siggen.sweep(
                        center=args.center,
                        span=args.span,
                        duration=args.duration,
                    )
                elif args.command == "pulse":
                    siggen.pulse(frequency=args.frequency, duration=args.duration)

                logging.info("Configured playback")
                input("Exit with Enter")

                siggen.stop_playback()
                logging.info("Playback stopped")
            if args.command == "rpc":
                common_args.init_logger_from_args(args)
                simple_server_loop(
                    {"siggen": siggen},
                    common_args.bind_address_from_args(args),
                    args.port,
                )
        finally:
            siggen.close()


if __name__ == "__main__":
    main()
