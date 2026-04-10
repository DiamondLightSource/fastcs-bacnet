import asyncio
from datetime import datetime as dt

from fastcs_bacnet.dummy.BAC0.device import Device

DUMMY_DEVICE_PORTS = [47900, 47901, 47902, 47904]
DUMMY_DEVICE_IDS = [125, 126, 127, 128]
DEVICE_FIELDS = [5, 10, 20, 20]


async def async_function():

    dummy_device_0 = Device(
        None,
        DUMMY_DEVICE_PORTS[0],
        DUMMY_DEVICE_IDS[0],
        number_of_constant_fields=DEVICE_FIELDS[0],
    )

    dummy_device_1 = Device(
        None,
        DUMMY_DEVICE_PORTS[1],
        DUMMY_DEVICE_IDS[1],
        number_of_oscillating_fields=DEVICE_FIELDS[1],
    )

    dd1_history_file = open("dummy_device_1_history.txt", "w")

    def dd1_callback_factory(object_name: str):
        def dd1_callback(old_value: float | None, new_value: float):
            dd1_history_file.write("send time: " + str(dt.now()) + "\n")
            if old_value is None or abs(old_value - new_value) > 0.1:
                dd1_history_file.write(
                    "package from port: " + str(DUMMY_DEVICE_PORTS[1]) + "\n"
                )
                dd1_history_file.write(
                    object_name + " changed to " + object_name + "\n"
                )
            else:
                dd1_history_file.write("change in dead zone, no package sent\n")

        return dd1_callback

    for i in range(DEVICE_FIELDS[1]):
        object_name = "oscillating_object_" + str(i)
        object = dummy_device_1.get_object_from_name(object_name)
        object.device_variable.set_diagnostic_callback(
            dd1_callback_factory(object_name)
        )

    dummy_device_2 = Device(
        None,
        DUMMY_DEVICE_PORTS[2],
        DUMMY_DEVICE_IDS[2],
        number_of_random_fields=DEVICE_FIELDS[2],
    )

    dd2_history_file = open("dummy_device_2_history.txt", "w")

    def dd2_callback_factory(object_name: str):
        def dd2_callback(old_value: float | None, new_value: float):
            dd2_history_file.write("send time: " + str(dt.now()) + "\n")
            if old_value is None or abs(old_value - new_value) > 0.1:
                dd2_history_file.write(
                    "package from port: " + str(DUMMY_DEVICE_PORTS[2]) + "\n"
                )
                dd2_history_file.write(
                    object_name + " changed to " + object_name + "\n"
                )
            else:
                dd2_history_file.write("change in dead zone, no package sent \n")

        return dd2_callback

    for i in range(DEVICE_FIELDS[2]):
        object_name = "random_object_" + str(i)
        object = dummy_device_2.get_object_from_name(object_name)
        object.device_variable.set_diagnostic_callback(
            dd2_callback_factory(object_name)
        )

    dummy_device_3 = Device(
        None,
        DUMMY_DEVICE_PORTS[3],
        DUMMY_DEVICE_IDS[3],
        number_of_oscillating_fields=DEVICE_FIELDS[3] // 2,
        number_of_random_fields=DEVICE_FIELDS[3] // 2,
    )

    dd3_history_file = open("dummy_device_3_history.txt", "w")

    def dd3_callback_factory(object_name: str):
        def dd3_callback(old_value: float | None, new_value: float):
            dd3_history_file.write("send time: " + str(dt.now()) + "\n")
            if old_value is None or abs(old_value - new_value) > 0.1:
                dd3_history_file.write(
                    "package from port: " + str(DUMMY_DEVICE_PORTS[3]) + "\n"
                )
                dd3_history_file.write(
                    object_name + " changed to " + object_name + "\n"
                )
            else:
                dd3_history_file.write("change in dead zone, no package sent \n")

        return dd3_callback

    for i in range(DEVICE_FIELDS[3] // 2):
        object_name = "oscillating_object_" + str(i)
        object = dummy_device_3.get_object_from_name(object_name)
        object.device_variable.set_diagnostic_callback(
            dd3_callback_factory(object_name)
        )
    for i in range(DEVICE_FIELDS[3] // 2):
        object_name = "random_object_" + str(i)
        object = dummy_device_3.get_object_from_name(object_name)
        object.device_variable.set_diagnostic_callback(
            dd3_callback_factory(object_name)
        )

    input()

    await dummy_device_0.disconnect()
    await dummy_device_1.disconnect()
    await dummy_device_2.disconnect()
    await dummy_device_3.disconnect()
    dd1_history_file.close()
    dd2_history_file.close()
    dd3_history_file.close()


asyncio.run(async_function())
