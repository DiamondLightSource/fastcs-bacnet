from collections import defaultdict
from datetime import datetime, time

import pandas as pd
import pandasql as ps


def make_client_dict(
    bacnet_client_ouput_filepath: str,
) -> tuple[datetime, datetime, dict[tuple[str, int, int], int]]:

    bacnet_server_file = open(bacnet_client_ouput_filepath)

    bacnet_server_frequencies: dict[tuple[str, int, int], int] = defaultdict(int)
    start_time: datetime | None = None
    end_time: datetime | None = None

    line = ""
    while "END" not in line:
        line = bacnet_server_file.readline()
        if "DATA: " in line:
            socket_address = line.split(",")[0].split(" ")[1]
            address = socket_address.split(":")[0]
            port = int(socket_address.split(":")[1])
            object_id = int(line.split(",")[1].split(".")[0])

            bacnet_server_frequencies[(address, port, object_id)] += 1

        elif "TIMES//" in line:
            times = line.split("//")[1]
            start_time_str = times.split("/")[1]
            end_time_str = times.split("/")[3]
            start_time = datetime.fromisoformat(start_time_str)
            end_time = datetime.fromisoformat(end_time_str)

    bacnet_server_file.close()

    if start_time is None or end_time is None:
        raise Exception

    return (start_time, end_time, bacnet_server_frequencies)


def make_wireshark_dict(
    wireshark_output_filepath: str, start_time: datetime, end_time: datetime
) -> dict[tuple[str, int, int], int]:

    wireshark_package_frequencies: dict[tuple[str, int, int], int] = {}

    wireshark_dataframe = pd.read_csv(wireshark_output_filepath)

    current_datetime = datetime.now()

    # easier to do the filtering logic in python (SQL is bad for working with strings)
    # 0 to keep it, 1 if it gets filtered
    filter: list[int] = []
    for time_str in wireshark_dataframe.Time:
        time_object = time.fromisoformat(time_str)
        datetime_object = datetime(
            current_datetime.year,
            current_datetime.month,
            current_datetime.day,
            time_object.hour,
            time_object.minute,
            time_object.second,
            time_object.microsecond,
        )

        if datetime_object > start_time and datetime_object < end_time:
            filter.append(0)
        else:
            filter.append(1)

    wireshark_dataframe.insert(0, "filter", filter)

    query = (
        "select Source, Port, Info, count(*) as frequency from wireshark_dataframe "
        + "where filter == 0 group by Source, Port, Info"
    )

    query_result = ps.sqldf(query)

    if query_result is not None:
        for _, row in query_result.iterrows():
            # so we know its a subscription update
            if "unconfirmedCOVNotification" in row.Info:
                ip = row.Source
                port = int(row.Port)
                object_instance = int(row.Info.split(" ")[3].split(",")[1])

                wireshark_package_frequencies[(ip, port, object_instance)] = (
                    row.frequency
                )

    return wireshark_package_frequencies


def compare_dicts(
    client_dict: dict[tuple[str, int, int], int],
    wireshark_dict: dict[tuple[str, int, int], int],
):
    missed_updates_from_connected_object = 0
    total_missed_updates = 0
    missed_objects = 0
    total_updates = 0
    total_updates_from_connected_objects = 0
    mystery_updates = 0

    seen_ips = set()
    seen_ports = set()
    seen_object_numbers = set()

    for key, wireshark_frequency in wireshark_dict.items():
        seen_ips.add(key[0])
        seen_ports.add(key[1])
        seen_object_numbers.add(key[2])

        if key not in client_dict:
            missed_objects += 1
            total_missed_updates += wireshark_frequency
            total_updates += wireshark_frequency
        else:
            client_frequency = client_dict[key]

            if client_frequency > wireshark_frequency:
                mystery_updates += client_frequency - wireshark_frequency
            else:
                missed_updates_from_connected_object += (
                    wireshark_frequency - client_frequency
                )
                total_missed_updates += wireshark_frequency - client_frequency
                total_updates += wireshark_frequency
                total_updates_from_connected_objects += wireshark_frequency

    for key, client_frequency in client_dict.items():
        seen_ips.add(key[0])
        seen_ports.add(key[1])
        seen_object_numbers.add(key[2])

        if key not in wireshark_dict:
            mystery_updates += client_frequency

    print("total updates ", total_updates)
    print("missed objects: ", missed_objects)
    print("missed updates: ", missed_updates_from_connected_object)
    print("mystery updates: ", mystery_updates)
    print(
        "reliability score: ",
        (total_updates_from_connected_objects - missed_updates_from_connected_object)
        / total_updates_from_connected_objects,
    )

    print("total unique ips seen: ", len(seen_ips))
    print("total unique ports seen: ", len(seen_ports))
    print("total unique object instance numbers seen: ", len(seen_object_numbers))


def compare_files(bacnet_server_filepath: str, wireshark_filepath: str):
    start_time, end_time, client_dict = make_client_dict(bacnet_server_filepath)

    wireshark_dict = make_wireshark_dict(wireshark_filepath, start_time, end_time)

    compare_dicts(client_dict, wireshark_dict)


compare_files(
    "./recieved_BAC0_updates.txt",
    "./cross_workstation_test_1",
)
