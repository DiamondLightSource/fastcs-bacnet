import asyncio

from fastcs_bacnet.dummy.BAC0.device import Device


async def run_devices(
    dummy_device_ports: list[int],
    dummy_device_ids: list[int],
    number_of_fields: int,
    min_change_time: float = 1.0,
    max_change_time=5.0,
):
    dummy_devices = []

    for i in range(len(dummy_device_ports)):
        port = dummy_device_ports[i]
        id = dummy_device_ids[i]

        dummy_device = Device(
            None,
            port,
            id,
            number_of_random_fields=number_of_fields,
            min_change_time=min_change_time,
            max_change_time=max_change_time,
        )
        dummy_devices.append(dummy_device)

    await asyncio.Event().wait()

    for dummy_device in dummy_devices:
        await dummy_device.disconnect()


# constants chosen to simulate roughly 2000 updates per minute
DUMMY_DEVICE_PORTS = list(range(47808, 47820))
DUMMY_DEVICE_IDS = list(range(123, 135))
NUMBER_OF_FIELDS = 30

asyncio.run(
    run_devices(
        DUMMY_DEVICE_PORTS,
        DUMMY_DEVICE_IDS,
        NUMBER_OF_FIELDS,
        min_change_time=2.0,
        max_change_time=10.0,
    )
)
