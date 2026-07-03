# End-to-End (e2e) tests of fastcs-bacnet
import asyncio
from collections.abc import AsyncGenerator

import aioca
import BAC0
import pytest

from fastcs_bacnet.core.BAC0.subscription_id import (
    IPv4SocketAddress,
    ObjectIdentifier,
    SubscriptionID,
)
from fastcs_bacnet.core.fastcs_bacnet import fastcs_bacnet
from fastcs_bacnet.dummy.BAC0.device import Device
from fastcs_bacnet.dummy.generic.device_variables.constant_variable import (
    ConstantVariable,
)

BAC0.log_level("error", log_this=False)

BACNET_SERVER_IP = "127.0.0.1"
BACNET_SERVER_PORT = 47809
BACNET_SERVER_DEVICEID = 456


@pytest.fixture
def subscriptions() -> dict[SubscriptionID, str]:
    """A list of subscriptions for our bacnet server to set up
    and our test client to subscribe to"""
    ipv4address = IPv4SocketAddress(
        BACNET_SERVER_IP, BACNET_SERVER_PORT, BACNET_SERVER_DEVICEID
    )

    subscriptions = {}

    # AnalogOutputs
    for i in range(3):
        subscriptions.update(
            {
                SubscriptionID(
                    ipv4address, ObjectIdentifier("analog-output", i)
                ): f"analog-output-{i}"
            }
        )

    return subscriptions


@pytest.fixture
async def bacnet_server(
    subscriptions: dict[SubscriptionID, str],
) -> AsyncGenerator[Device]:
    """A BACnet server, simulating a real device"""
    device = Device(
        BACNET_SERVER_IP,
        BACNET_SERVER_PORT,
        BACNET_SERVER_DEVICEID,
    )

    for idx, (subscription, pv) in enumerate(subscriptions.items()):
        if subscription.object_id.object_type == "analog-output":
            device.create_analog_output_object(
                pv, "Placeholder Description", ConstantVariable(pv, idx)
            )

    yield device

    await device.disconnect()


@pytest.fixture
async def fastcs_application(
    subscriptions: dict[SubscriptionID, str],
) -> AsyncGenerator[None]:
    """The main application under test"""
    task = asyncio.create_task(fastcs_bacnet(subscriptions))
    yield
    task.cancel()
    await task


async def test_experiments(
    subscriptions: dict[SubscriptionID, str], bacnet_server, fastcs_application
):

    for idx, pv in enumerate(subscriptions.values()):
        val = await aioca.caget(f"FASTCS_BACNET:Subcontroller0:{pv}")
        assert val == idx
