# End-to-End (e2e) tests of fastcs-bacnet
import asyncio
from collections.abc import AsyncGenerator

import aioca
import numpy
import pytest

from fastcs_bacnet.core.BAC0.subscription_id import (
    IPv4SocketAddress,
    ObjectIdentifier,
    SubscriptionID,
)
from fastcs_bacnet.core.fastcs_bacnet import fastcs_bacnet

from .conftest import DeviceData


@pytest.fixture
async def fastcs_application(
    bacnet_servers: None,
    device_data: list[DeviceData],
) -> AsyncGenerator[None]:
    """The main application under test.

    Runs in a background task"""

    subscriptions: dict[SubscriptionID, str] = {}

    for device in device_data:
        addr = IPv4SocketAddress(device.device_ip, device.device_port, device.device_id)
        for object in device.object_data:
            obj_id = ObjectIdentifier(object.object_type, object.object_instance)
            subscriptions.update({SubscriptionID(addr, obj_id): object.pv})

    task = asyncio.create_task(fastcs_bacnet(subscriptions))
    yield
    task.cancel()
    await task


async def wait_for_pv_value(
    pv: str, expected_value: int | list[int], timeout: float = 15.0
) -> None:
    """Wait until a PV reports the expected value, failing after timeout.

    The StatisticsController only recalculates its PVs periodically, so a single
    caget may return a stale value. camonitor delivers the current value on
    connection and every update after that, so we wait for a matching one."""
    matched = asyncio.Event()
    last_value = None

    def on_update(value):
        nonlocal last_value
        last_value = value
        if isinstance(value, numpy.ndarray):
            is_match = numpy.array_equal(value, expected_value)
        else:
            is_match = value == expected_value
        if is_match:
            matched.set()

    # FORMAT_TIME is required: libca silently drops monitor updates with a zero
    # byte payload, which is what an empty waveform of a plain DBR type produces.
    # Requesting timestamp metadata makes the payload non-empty.
    subscription = aioca.camonitor(pv, on_update, format=aioca.FORMAT_TIME)
    try:
        await asyncio.wait_for(matched.wait(), timeout)
    except TimeoutError:
        pytest.fail(
            f"Statistics PV {pv} was not {expected_value} after {timeout}s, "
            f"last value was {last_value}"
        )
    finally:
        subscription.close()


async def test_all_object_creation_subscription(
    device_data: list[DeviceData],
    fastcs_application: None,
):
    """Check that the FastCS application can retrieve all expected PVs from all
    configured Devices"""

    for device in device_data:
        for object in device.object_data:
            val = await aioca.caget(object.pv)
            assert val == object.expected_value, (
                f"Did not find expected value for device {device.device_name} "
                f"object {object}"
            )

    # Test the StatisticsController PVs
    data = [
        ("STATS:CountActiveDevices", 3),
        ("STATS:CountInactiveDevices", 0),
        ("STATS:InactiveSubscriptions", 0),
        ("STATS:TotalDevices", 3),
        ("STATS:TotalSubscriptions", 54),
        ("STATS:ActiveDevices", [5555, 5678, 8765]),
        ("STATS:InactiveDevices", []),
        ("STATS:ActiveSubscriptions", 54),
        # Don't check RunningTasks as it is a rather unstable number
        # ("STATS:RunningTasks", 223),
    ]

    for pv, expected_value in data:
        await wait_for_pv_value(pv, expected_value)
