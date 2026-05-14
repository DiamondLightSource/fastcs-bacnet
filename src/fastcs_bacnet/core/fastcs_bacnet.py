from BAC0 import start
from fastcs.launch import FastCS
from fastcs.transports.epics import EpicsIOCOptions
from fastcs.transports.epics.ca import EpicsCATransport

from fastcs_bacnet.practical.BAC0.bacnet_client import BacnetClient
from fastcs_bacnet.practical.BAC0.subscription_id import SubscriptionID
from fastcs_bacnet.practical.FastCS.bacnet_controller import BacnetController


async def fastcs_bacnet(subscriptions: list[SubscriptionID]):
    """
    Runs the fastcs-bacnet application on the passed in subscriptions

    This will start a FastCS EPICS IOC that can be used to query the
    subscribed to objects

    subscriptions: The bacnet objects to subscribe to
    """

    # Use a context provider so if application errors out or is closed
    # BAC0 client is shut down correctly
    async with start() as bac0:
        bacnet_client = BacnetClient(bac0)
        await bacnet_client.add_subscriptions(subscriptions)

        epics_ca = EpicsCATransport(epicsca=EpicsIOCOptions(pv_prefix="FASTCSBACNET"))
        bacnet_controller = BacnetController(bacnet_client)

        fastcs = FastCS(bacnet_controller, [epics_ca])

        await fastcs.serve(interactive=False)
