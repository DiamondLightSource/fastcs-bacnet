"""Interface for ``python -m fastcs_bacnet``."""

import asyncio
from argparse import ArgumentParser
from collections.abc import Sequence

import BAC0

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
    parser.parse_args(args)
    print("hello world!!")
    asyncio.run(start_bacnet())


async def start_bacnet():
    async with BAC0.start() as bacnet:  # noqa: F841
        pass


if __name__ == "__main__":
    main()
