import asyncio
from collections import Counter
from dataclasses import dataclass

import numpy
from fastcs.attributes import AttributeIO, AttributeIORef, AttrR
from fastcs.controllers import Controller
from fastcs.datatypes import Int, Waveform
from fastcs.logging import logger
from fastcs.methods import scan

from fastcs_bacnet.core.BAC0.bacnet_client import BacnetClient
from fastcs_bacnet.core.BAC0.object_subscription import (
    SubscriptionStatus,
)


@dataclass
class RunningTasksIORef(AttributeIORef):
    update_period: float | None = 1


class RunningTasksIO(AttributeIO[int, RunningTasksIORef]):
    async def update(self, attr: AttrR[int, RunningTasksIORef]):
        running_tasks = len(asyncio.all_tasks())
        await attr.update(running_tasks)


class StatisticsController(Controller):
    """
    A FastCS controller for statistics about the running system
    """

    _bacnet_client: BacnetClient

    running_tasks = AttrR(Int(min=0))

    total_subscriptions = AttrR(Int(min=0))
    # Count of subscriptions in the Active state
    active_subscriptions = AttrR(Int(min=0))
    # Count of subscriptions in the Inactive state
    inactive_subscriptions = AttrR(Int(min=0))

    total_devices = AttrR(Int(min=0))
    # An Active device has one or more active subscriptions
    count_active_devices = AttrR(Int(min=0))
    active_devices: AttrR[numpy.ndarray]
    # An Inactive device has zero active subscriptions
    count_inactive_devices = AttrR(Int(min=0))
    inactive_devices: AttrR[numpy.ndarray]

    # TODO:
    # - Last contact time from each device
    # - more?

    def __init__(self, bacnet_client: BacnetClient):

        self._bacnet_client = bacnet_client

        # TODO: Understand this and how to add the other ones
        super().__init__(ios=[RunningTasksIO()])

    async def initialise(self):
        device_count = len(self._bacnet_client.get_devices())
        self.add_attribute(
            "active_devices", AttrR(Waveform(numpy.int32, shape=(device_count,)))
        )
        self.add_attribute(
            "inactive_devices", AttrR(Waveform(numpy.int32, shape=(device_count,)))
        )

    @scan(period=5.0)
    async def update_attributes(self):
        try:
            await self._update_attributes()
        except Exception:
            # FastCS would normally halt all scan tasks on a Controller if an exception
            # is seen. However we are only introspecting other Controllers, so don't
            # need FastCS to stop us doing that.
            logger.exception("Exception in statistics controller scan")

    async def _update_attributes(self):
        """Update all attributes on this controller"""
        devices = self._bacnet_client.get_devices()
        device_count = len(devices)

        total_subscriptions = 0
        active_subscriptions = 0
        inactive_subscriptions = 0

        count_active_devices = 0
        active_devices = []
        count_inactive_devices = 0
        inactive_devices = []

        for device in devices:
            subs_counter = Counter(
                subs.get_status() for subs in device.get_subscriptions()
            )

            total_subscriptions += subs_counter.total()
            active_subscriptions += subs_counter[SubscriptionStatus.ACTIVE]
            inactive_subscriptions += subs_counter[SubscriptionStatus.INACTIVE]

            device_id = (
                device.get_subscriptions()[0]
                .get_subscription_id()
                .socket_address.device_instance
            )
            if subs_counter[SubscriptionStatus.ACTIVE] > 0:
                count_active_devices += 1
                active_devices.append(device_id)
            else:
                count_inactive_devices += 1
                inactive_devices.append(device_id)

        running_tasks = len(asyncio.all_tasks())

        # This is probably overkill, could just await each in turn
        async with asyncio.TaskGroup() as tg:
            tg.create_task(self.running_tasks.update(running_tasks))
            tg.create_task(self.total_subscriptions.update(total_subscriptions))
            tg.create_task(self.active_subscriptions.update(active_subscriptions))
            tg.create_task(self.inactive_subscriptions.update(inactive_subscriptions))
            tg.create_task(self.total_devices.update(device_count))
            tg.create_task(self.count_active_devices.update(count_active_devices))
            tg.create_task(self.active_devices.update(active_devices))
            tg.create_task(self.count_inactive_devices.update(count_inactive_devices))
            tg.create_task(self.inactive_devices.update(inactive_devices))
