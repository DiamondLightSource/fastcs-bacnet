"""Interface for ``python -m fastcs_bacnet``."""

from argparse import ArgumentParser
from collections.abc import Sequence
from pathlib import Path

from fastcs import FastCS
from fastcs.attributes import AttrR
from fastcs.connections import IPConnection, IPConnectionSettings
from fastcs.controllers import Controller
from fastcs.datatypes import String
from fastcs.transports.epics import EpicsGUIOptions, EpicsIOCOptions
from fastcs.transports.epics.ca.transport import EpicsCATransport

from . import __version__

__all__ = ["main"]


class MyController(Controller):
    device_id = AttrR(String())

    def __init__(self, settings: IPConnectionSettings):
        super().__init__()

        self._ip_settings = settings
        self._connection = IPConnection()

    async def connect(self):
        await self._connection.connect(self._ip_settings)


gui_options = EpicsGUIOptions(
    output_path=Path(".") / "demo.bob", title="Demo Temperature Controller"
)
epics_ca = EpicsCATransport(gui=gui_options, epicsca=EpicsIOCOptions(pv_prefix="DEMO"))
connection_settings = IPConnectionSettings("localhost", 25565)
fastcs = FastCS(MyController(connection_settings), [epics_ca])


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
    fastcs.run()


if __name__ == "__main__":
    main()
