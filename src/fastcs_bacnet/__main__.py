"""Interface for ``python -m fastcs_bacnet``."""

import asyncio
from argparse import ArgumentParser
from collections.abc import Sequence

from fastcs.logging import configure_logging, logger

from fastcs_bacnet.core.ede_parser import parse_ede, parse_ip_mapping_file
from fastcs_bacnet.core.fastcs_bacnet import fastcs_bacnet
from fastcs_bacnet.core.pv_mapping import (
    check_mapping_file_path,
    pv_names_dict,
    write_pv_mapping,
)

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
        "--pv-mapping-out",
        type=str,
        default=None,
        metavar="PATH",
        help="Write the mapping of BACnet objects to EPICS PV names to this file "
        + "before starting the IOC. The format (.csv or .xlsx) is taken from the "
        + "suffix",
    )

    parser.add_argument(
        "--export-only",
        action="store_true",
        help="Write the file given by --pv-mapping-out and exit without starting "
        + "the IOC",
    )

    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=__version__,
    )

    args_namespace = parser.parse_args(args)

    mapping_out = args_namespace.pv_mapping_out
    if args_namespace.export_only and mapping_out is None:
        parser.error("--export-only requires --pv-mapping-out")
    if mapping_out is not None:
        # Fail before the slow EDE parsing if the file could not be written
        try:
            check_mapping_file_path(mapping_out)
        except ValueError as e:
            parser.error(str(e))

    ip_mapping = parse_ip_mapping_file(args_namespace.ip_mapping)

    entries = parse_ede(
        args_namespace.ede_file_path,
        args_namespace.config_dir,
        ip_mapping,
    )

    if mapping_out is not None:
        write_pv_mapping(entries, mapping_out)
        logger.info(f"Wrote mapping of {len(entries)} PVs to {mapping_out}")
        if args_namespace.export_only:
            return

    asyncio.run(fastcs_bacnet(pv_names_dict(entries)))


if __name__ == "__main__":
    main()
