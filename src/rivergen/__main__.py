import sys
import rivergen.tests as tests

from argparse import ArgumentParser
from rivergen.utils import ConfigFile, logger

def main():
    parser = ArgumentParser()

    parser.add_argument(
        "-c","--config",
        help=(
            "Generate a new river according to provided configuration "
            "file path. Use './configs/example.yaml' for an example."
        )
    )
    parser.add_argument(
        "-t", "--test", action="store_true",
        help=(
            "Constructs, visualizes and deletes a river "
            "from the provided configuration file."
        )
    )
    parser.add_argument(
        "-v","--visualize", action="store_true",
        help=(
            "If used together with '-c' a new "
            "river will be contructed, saved and immediately "
            "visualized."
        )
    )

    args = parser.parse_args()

    if not sys.argv[1:]:
        msg = "No arguments supplied. See '--help' for info."
        logger.error(msg)
        raise RuntimeError(msg)

    if args.config is None:
        msg = (
            "No configuration file provided. See '--help' "
            "for additional info."
        )
        logger.error(msg)
        raise RuntimeError(msg)

    if args.test:
        tests.rivergen_rndm_viz(args.config)

    elif args.visualize:
        cfile = ConfigFile(args.config)
        CONFIG = cfile.config
        exporter = cfile.parse()
        path = exporter.export_to_file()
        logger.info(
            f"River successfully constructed at '{path}'."
        )
        tests.visualize(path,CONFIG)

    elif not args.test and not args.visualize:
        exporter = ConfigFile(args.config).parse()
        path = exporter.export_to_file()
        logger.info(
            f"River successfully constructed at '{path}'."
        )

    else:
        msg = (
            "Invalid argument combination. "
            "See '--help' for additional info."
        )
        logger.error(msg)
        raise RuntimeError(msg)