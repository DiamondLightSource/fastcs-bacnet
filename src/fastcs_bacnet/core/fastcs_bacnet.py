import asyncio

from BAC0 import start
from fastcs.launch import FastCS
from fastcs.transports.epics import EpicsIOCOptions
from fastcs.transports.epics.ca import EpicsCATransport

from fastcs_bacnet.practical.BAC0.bacnet_client import BacnetClient
from fastcs_bacnet.practical.BAC0.subscription_id import SubscriptionID
from fastcs_bacnet.practical.FastCS.bacnet_controller import BacnetController


async def fastcs_bacnet(subscriptions: list[SubscriptionID]):

    async with start() as bac0:
        bacnet_client = BacnetClient(bac0, initial_subscriptions=subscriptions)

        epics_ca = EpicsCATransport(epicsca=EpicsIOCOptions(pv_prefix="FASTCSBACNET"))
        bacnet_controller = BacnetController(bacnet_client)

        fastcs = FastCS(bacnet_controller, [epics_ca])

        asyncio.create_task(fastcs.serve(interactive=False))

        await asyncio.Event().wait()
