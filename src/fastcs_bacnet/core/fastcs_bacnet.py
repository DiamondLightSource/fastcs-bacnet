from BAC0 import start
from fastcs.launch import FastCS
from fastcs.transports.epics.ca import EpicsCATransport

from fastcs_bacnet.core.BAC0.bacnet_client import BacnetClient
from fastcs_bacnet.core.BAC0.subscription_id import SubscriptionID
from fastcs_bacnet.core.FastCS.bacnet_controller import BacnetController


async def fastcs_bacnet(pv_names_dict: dict[SubscriptionID, str]):
    """
    Runs the fastcs-bacnet application on the passed in subscriptions

    This will start a FastCS EPICS IOC using the Channel Access protocol.

    subscriptions: The bacnet objects to subscribe to
    """

    subscriptions = list(pv_names_dict.keys())

    # Use a context provider so if application errors out or is closed
    # BAC0 client is shut down correctly
    async with start() as bac0:
        bacnet_client = BacnetClient(bac0, initial_subscriptions=subscriptions)

        epics_ca = EpicsCATransport()
        bacnet_controller = BacnetController(bacnet_client, pv_names_dict)
        bacnet_controller.set_path(["FASTCS_BACNET"])

        fastcs = FastCS(bacnet_controller, [epics_ca])

        await fastcs.serve(interactive=False)
