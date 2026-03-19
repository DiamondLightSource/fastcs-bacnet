"""Interface for ``python -m fastcs_bacnet``."""

from argparse import ArgumentParser
from collections.abc import Sequence

from fastcs_bacnet.examples.FastCS.CA_for_dummy_device import (
    single_controller_multi_random,
)

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
    single_controller_multi_random()


if __name__ == "__main__":
    main()
