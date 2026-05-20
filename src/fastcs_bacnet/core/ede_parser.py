import csv

from dls_bms.dls_bms.bms import (
    IFM_FILE_TYPE,
    extractData,
    # getBMSConfig,
    openCsvFile,
    openExcelFile,
    skipHeader,
)
from fastcs_bacnet.practical.BAC0.subscription_id import (
    IPv4SocketAddress,
    ObjectIdentifier,
    SubscriptionID,
)


def parse_ede(
    file_path: str, header_rows: int, config_path: str
) -> list[tuple[SubscriptionID, str]]:

    subscriptions_with_names = []

    # config_file = getBMSConfig(config_path)

    if ".xls" in file_path or ".xlsx" in file_path:
        ede_file = openExcelFile(file_path)
    else:
        ede_file = openCsvFile(file_path)

    reader = csv.reader(ede_file, delimiter=",")
    reader = skipHeader(reader, IFM_FILE_TYPE, headerRows=header_rows)

    for row in reader:
        object_id, instance, name, existing_pv_name, data = extractData(
            row, IFM_FILE_TYPE
        )

        pv_name = ""  # make pv name
        subscription_id = SubscriptionID(
            IPv4SocketAddress("", 0),
            ObjectIdentifier("", 0),  # set subscription id
        )
        # do some final checks, raise exceptions, log warnings / errors

        subscriptions_with_names.append((subscription_id, pv_name))

    return subscriptions_with_names
