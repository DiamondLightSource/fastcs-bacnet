from dataclasses import dataclass

from fastcs.attributes import AttributeIO, AttributeIORef, AttrR, AttrRW
from fastcs.controllers import Controller
from fastcs.datatypes import Float

from fastcs_bacnet.dummy_device import DummyDevice, FieldType


@dataclass
class DummyAttributeIORef(AttributeIORef):
    field_type: FieldType
    index: int


class IndexAttributeIO(AttributeIO[float, DummyAttributeIORef]):
    def __init__(self, device: DummyDevice):
        super().__init__()

        self.device = device

    async def update(self, attr: AttrR[float, DummyAttributeIORef]):

        await attr.update(
            self.device.get_value(attr.io_ref.field_type, attr.io_ref.index)
        )


class DummyDeviceController(Controller):
    def __init__(self, dummy_device: DummyDevice):
        super().__init__(ios=[IndexAttributeIO(dummy_device)])
        update_period = 1.5

        # this could be looped maybe?
        for i in range(len(dummy_device.constant_fields)):
            self.add_attribute(
                "constant_field_" + str(i),
                AttrR(
                    Float(),
                    io_ref=DummyAttributeIORef(
                        FieldType.CONSTANT, i, update_period=update_period
                    ),
                ),
            )

        for i in range(len(dummy_device.oscillating_fields)):
            self.add_attribute(
                "oscillating_field_" + str(i),
                AttrR(
                    Float(),
                    io_ref=DummyAttributeIORef(
                        FieldType.OSCILLATING, i, update_period=update_period
                    ),
                ),
            )

        for i in range(len(dummy_device.random_fields)):
            self.add_attribute(
                "random_field_" + str(i),
                AttrR(
                    Float(),
                    io_ref=DummyAttributeIORef(
                        FieldType.RANDOM, i, update_period=update_period
                    ),
                ),
            )

        for i in range(len(dummy_device.rw_fields)):
            self.add_attribute(
                "rw_field_" + str(i),
                AttrRW(
                    Float(),
                    io_ref=DummyAttributeIORef(
                        FieldType.WRITABLE, i, update_period=update_period
                    ),
                ),
            )
