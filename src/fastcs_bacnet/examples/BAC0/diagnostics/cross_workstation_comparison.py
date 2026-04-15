from collections import defaultdict

import pandas as pd


def compare_files(bacnet_server_filepath: str, wireshark_filepath: str):
    bacnet_server_file = open(bacnet_server_filepath)
    wireshark_dataframe = pd.read_csv(wireshark_filepath)

    # not sure what to do with dataframe yet
    print(wireshark_dataframe.info())

    start_time = None
    end_time = None

    bacnet_server_frequencies: dict[tuple[str, int, int], int] = defaultdict(int)

    line = ""
    while "END" not in line:
        line = bacnet_server_file.readline()
        if "." in line:
            socket_address = line.split(",")[0]
            address = socket_address.split(":")[0]
            port = int(socket_address.split(":")[1])
            object_id = int(line.split(",")[1].split(".")[0])

            bacnet_server_frequencies[(address, port, object_id)] += 1

        elif "," in line:
            start_time = line.split(",")[0]  # noqa: F841
            end_time = line.split(",")[1]  # noqa: F841

    wireshark_package_frequencies: dict[tuple[str, int, int], int] = {}  # noqa: F841
