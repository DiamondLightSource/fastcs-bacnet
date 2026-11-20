"""Interface for ``python -m fastcs_bacnet``."""

import asyncio
from argparse import ArgumentParser
from collections.abc import Sequence

from fastcs.logging import configure_logging

from fastcs_bacnet.core.ede_parser import parse_ede, parse_ip_mapping_file
from fastcs_bacnet.core.fastcs_bacnet import fastcs_bacnet

from . import __version__

__all__ = ["main"]


def main(args: Sequence[str] | None = None) -> None:
    configure_logging()

    description = (
        "Start a FastCS IOC with PVs and Bacnet object subscriptions defined "
        + "from an EDE file and a BMS config file"
    )

    parser = ArgumentParser(description=description)
    parser.add_argument(
        "ede_file_path",
        type=str,
        help="Filepath to the EDE file",
    )

    parser.add_argument(
        "config_dir", type=str, help="Filepath to the directory with the bms.ini file"
    )

    parser.add_argument(
        "ip_mapping", type=str, help="Filepath to the Device to IP mapping file"
    )

    parser.add_argument(
        "-r",
        "--header_rows",
        type=int,
        default=0,
        help="Number of rows before data in the EDE file",
    )

    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=__version__,
    )

    args_namespace = parser.parse_args(args)

    ip_mapping = parse_ip_mapping_file(args_namespace.ip_mapping)

    pv_names_dict = parse_ede(
        args_namespace.ede_file_path,
        args_namespace.config_dir,
        ip_mapping,
        header_rows=args_namespace.header_rows,
    )

    asyncio.run(fastcs_bacnet(pv_names_dict))


if __name__ == "__main__":
    main()
