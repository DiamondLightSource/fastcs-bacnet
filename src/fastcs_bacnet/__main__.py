"""Interface for ``python -m fastcs_bacnet``."""

import asyncio
from argparse import ArgumentParser
from collections.abc import Sequence

from fastcs_bacnet.core.csv_parser import parse_csv
from fastcs_bacnet.core.fastcs_bacnet import fastcs_bacnet

from . import __version__

__all__ = ["main"]


def main(args: Sequence[str] | None = None) -> None:
    """
    Entrypoint for the fastcs-bacnet program

    Use option -f to specify filepath of the EDE file
    This will automatically subscribe to bacnet devices
    and create an IOC to query Bacnet objects
    """
    parser = ArgumentParser()
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=__version__,
    )
    parser.add_argument(
        "-f",
        "--file_path",
        type=str,
        help="Filepath to the EDE file",
    )
    args_dict = parser.parse_args(args)

    if args_dict.file_path is None:
        raise ValueError("Must specify an input file")

    subscription_ids = parse_csv(args_dict.file_path)

    asyncio.run(fastcs_bacnet(subscription_ids))


if __name__ == "__main__":
    main()
