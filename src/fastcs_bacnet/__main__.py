"""Interface for ``python -m fastcs_bacnet``."""

import asyncio
from argparse import ArgumentParser
from collections.abc import Sequence

from fastcs_bacnet.core.csv_parser import parse_csv
from fastcs_bacnet.core.fastcs_bacnet import fastcs_bacnet

from . import __version__

__all__ = ["main"]


def main(args: Sequence[str] | None = None) -> None:
    """Argument parser for the CLI."""
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
        help="Filepath to the EDE file (or dummy equivalent)",
    )
    python_argument_object = parser.parse_args(args)

    if python_argument_object.file_path is None:
        print("file path cannot be None")
        return

    subscription_ids = parse_csv(python_argument_object.file_path)
    if len(subscription_ids) == 0:
        return

    asyncio.run(fastcs_bacnet(subscription_ids))


if __name__ == "__main__":
    main()
