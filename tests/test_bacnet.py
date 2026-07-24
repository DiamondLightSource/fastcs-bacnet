# Tests for the Bacnet side of the application
import asyncio

from BAC0 import start

from fastcs_bacnet.core.BAC0.bacnet_client import BacnetClient
from fastcs_bacnet.core.BAC0.subscription_id import (
    IPv4SocketAddress,
    ObjectIdentifier,
    SubscriptionID,
)


async def test_subscribing_to_non_existent_points(
    loguru_caplog,
    unused_tcp_port_factory,
):
    """Test the behaviour when attempting to subscribe to a point that doesn't exist in
    the Bacnet server"""

    object_type = "analog-output"
    object_instance = 2

    fake_subscription = SubscriptionID(
        IPv4SocketAddress("localhost", unused_tcp_port_factory(), 555),
        ObjectIdentifier(object_type, object_instance),
    )

    async with start() as bac0:
        bacnet_client = BacnetClient(
            bac0, initial_subscriptions=[fake_subscription], subscription_lifetime=5
        )
        await bacnet_client.start_subscriptions()
        # Unfortunate, but there doesn't seem like there's an easy way to bypass the
        # 10 seconds of bacpypes3 trying to reconnect to the fake device.
        # Added on 5 seconds as cutting it too close seems to make logs not appear in
        # the loguru_caplog fixture.
        await asyncio.sleep(15)

    assert (
        "Exception in starting subscription for object analog-output,2"
        in loguru_caplog.text
    )

    assert "bacpypes3.apdu.AbortPDU: no-response" in loguru_caplog.text
