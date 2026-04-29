import asyncio
import socket

from fastcs_bacnet.dummy.BAC0.device import Device


def main():
    asyncio.run(start_dummy_device())


async def start_dummy_device():

    ip = socket.gethostbyname(socket.gethostname())
    ip = "127.0.0.1"
    Device(ip, 47809, 456, number_of_random_fields=10)

    await asyncio.Event().wait()


if __name__ == "__main__":
    main()
