"""Interface for ``python -m fastcs_bacnet``."""

from argparse import ArgumentParser
from collections.abc import Sequence
from dataclasses import dataclass

from fastcs.attributes import AttributeIO, AttributeIORef, AttrR
from fastcs.controllers import Controller
from fastcs.datatypes import Float
from fastcs.launch import FastCS
from fastcs.transports.epics import EpicsIOCOptions
from fastcs.transports.epics.ca import EpicsCATransport

from . import __version__

__all__ = ["main"]


class DeviceObject:
    def __init__(self, number_of_fields: int):
        self.number_of_fields = number_of_fields
        self.store: dict[int, float] = {}

        for i in range(number_of_fields):
            self.store[i] = (i * 439 % 238) / 57

    def get(self, index: int):
        return self.store[index]


@dataclass
class IndexAttributeIORef(AttributeIORef):
    index: int


class IndexAttributeIO(AttributeIO[float, IndexAttributeIORef]):
    def __init__(self, device: DeviceObject):
        super().__init__()

        self.device = device

    async def update(self, attr: AttrR[float, IndexAttributeIORef]):

        await attr.update(self.device.get(attr.io_ref.index))


class SimpleController(Controller):
    def __init__(self, device: DeviceObject):
        super().__init__(ios=[IndexAttributeIO(device)])

        for i in range(device.number_of_fields):
            self.add_attribute(
                "attribute_" + str(i),
                AttrR(Float(), io_ref=IndexAttributeIORef(i, update_period=1)),
            )


device_object = DeviceObject(1500)

epics_ca = EpicsCATransport(epicsca=EpicsIOCOptions(pv_prefix="DEMO"))
local_controller = SimpleController(device_object)
fastcs = FastCS(local_controller, [epics_ca])


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

    # TO TEST:
    # 1: run this file (fastcs-bacnet)
    # 2: start terminal (outside of container)
    # 3: run command "caget DEMO:Attribute943"


if __name__ == "__main__":
    main()
