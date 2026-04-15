from collections import defaultdict

import pandas as pd


def compare_files(bacnet_server_filepath: str, wireshark_filepath: str):
    bacnet_server_file = open(bacnet_server_filepath)
    wireshark_dataframe = pd.read_csv(wireshark_filepath)

    # not sure what to do with dataframe yet
    print(wireshark_dataframe.info())

    start_time = None  # noqa: F841
    end_time = None  # noqa: F841

    line = ""
    while "END" not in line:
        line = bacnet_server_file.readline()
        if "." in line:
            # data line
            pass
        elif "," in line:
            # metadata line
            pass

    bacnet_server_frequencies: dict[tuple[str, int, int], int] = defaultdict(int)  # noqa: F841
    wireshark_package_frequencies: dict[tuple[str, int, int], int] = {}  # noqa: F841
