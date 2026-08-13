from BAC0 import start
from fastcs.controllers import Controller
from fastcs.launch import FastCS
from fastcs.transports.epics.ca import EpicsCATransport

from fastcs_bacnet.core.BAC0.bacnet_client import BacnetClient
from fastcs_bacnet.core.BAC0.subscription_id import SubscriptionID, sort_dict
from fastcs_bacnet.core.FastCS.bacnet_subcontroller import BacnetSubController
from fastcs_bacnet.core.FastCS.statistics_controller import StatisticsController


async def fastcs_bacnet(pv_names_dict: dict[SubscriptionID, str]):
    """
    Runs the fastcs-bacnet application on the passed in subscriptions

    This will start a FastCS EPICS IOC using the Channel Access protocol.

    pv_names_dict: A mapping from SubscriptionID s (representing objects on devices)
        to the name of the name its repsective EPICS PV should be given
    """

    subscriptions = list(pv_names_dict.keys())

    async with start() as bac0:
        bacnet_client = BacnetClient(bac0, initial_subscriptions=subscriptions)

        epics_ca = EpicsCATransport()

        controllers: list[Controller] = []

        sorted_dict = sort_dict(pv_names_dict)

        # Create each top level Controller
        for key, val in sorted_dict.items():
            controller = BacnetSubController(bacnet_client, val)
            controller.set_path([key])
            controllers.append(controller)

        statistics_controller = StatisticsController(bacnet_client)
        # TODO: "STATS" should also be prefixed with the IOC's name
        statistics_controller.set_path(["STATS"])
        controllers.append(statistics_controller)

        # Note that this would more properly be some kind of one-time initalisation in
        # FastCS, but no such hook exists. Fortunately it's safe to start updating
        # attributes before FastCS has started, so this is not a problem.
        await bacnet_client.start_subscriptions()

        fastcs = FastCS(controllers, [epics_ca])

        await fastcs.serve(interactive=True)
