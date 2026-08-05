# Tests for the Bacnet side of the application
import asyncio
from pathlib import Path

import pytest
from BAC0 import start
from pytest import LogCaptureFixture, approx

from fastcs_bacnet.core.BAC0.bacnet_client import BacnetClient
from fastcs_bacnet.core.BAC0.subscription_id import (
    IPv4SocketAddress,
    ObjectIdentifier,
    SubscriptionID,
)
from tests.conftest import (
    BACNET_SERVER_IP,
    DeviceData,
    ObjectData,
    create_bacnet_server,
)


async def test_subscribing_to_non_existent_device(
    loguru_caplog: LogCaptureFixture,
    unused_tcp_port_factory,
    bac0_config_reduce_apdu_retries: Path,
):
    """Test the behaviour when attempting to subscribe to a device that doesn't exist"""

    object_type = "analog-output"
    object_instance = 2

    fake_subscription = SubscriptionID(
        IPv4SocketAddress("localhost", unused_tcp_port_factory(), 555),
        ObjectIdentifier(object_type, object_instance),
    )

    async with start(json_file=bac0_config_reduce_apdu_retries) as bac0:
        bacnet_client = BacnetClient(
            bac0,
            initial_subscriptions=[fake_subscription],
        )
        await bacnet_client.start_subscriptions()
        # While the timeout does happen a quicker than this, loguru seems to need a
        # few seconds to collect the log messages
        await asyncio.sleep(5)

    assert (
        "Exception in starting subscription for object analog-output,2"
        in loguru_caplog.text
    )

    assert "bacpypes3.apdu.AbortPDU: no-response" in loguru_caplog.text


@pytest.mark.xfail(reason="Waiting for fix for BAC0 #584", raises=AssertionError)
async def test_responding_to_device_starting(
    loguru_caplog: LogCaptureFixture,
    unused_tcp_port_factory,
    bac0_config_reduce_apdu_retries: Path,
):
    """Test that we can subscribe to a device that starts up after our client -
    i.e. that we can respond to am IAm notification and open subscriptions"""

    object_type = "analog-output"
    object_instance = 2
    object_value = 5.9

    port = unused_tcp_port_factory()
    device_id = 555

    server_address = IPv4SocketAddress("localhost", port, device_id)
    obj_id = ObjectIdentifier(object_type, object_instance)
    subscription = SubscriptionID(
        server_address,
        obj_id,
    )

    # Set up data for our new device
    data = DeviceData(
        "NewDevice",
        BACNET_SERVER_IP,
        port,
        device_id,
        [ObjectData(object_type, object_instance, object_value, "ABC-123")],
    )

    async with start(json_file=bac0_config_reduce_apdu_retries) as bac0:
        bacnet_client = BacnetClient(
            bac0, initial_subscriptions=[subscription], subscription_lifetime=5
        )
        await bacnet_client.start_subscriptions()
        await asyncio.sleep(5)  # Ensure initial attempt to subscribe fails

        # TODO: The creation of this server should emit an IAm message, but as of issue
        # #584 in BAC0 it does not. Re-visit this test when we have a fix for that.
        device = create_bacnet_server(data)
        # Give time for the subscription to retry after IAm received
        await asyncio.sleep(2)

        subs = bacnet_client._devices[server_address]

    # Confirm IAm was received
    server_ipaddr = IPv4SocketAddress(BACNET_SERVER_IP, port, device_id)
    assert f"Received Iam from device {server_ipaddr}" in loguru_caplog.text
    # And that we have the right value
    assert subs._object_subscriptions[obj_id]._present_value == approx(object_value)

    await device.disconnect()
