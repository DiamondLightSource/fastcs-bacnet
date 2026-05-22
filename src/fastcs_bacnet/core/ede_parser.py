import csv

from bacpypes3.primitivedata import ObjectType

from dls_bms.dls_bms.bms import (
    IFM_FILE_TYPE,
    checkPvNameLength,
    checkUniquePvNames,
    createPvName,
    extractData,
    getBMSConfig,
    getIniFile,
    openCsvFile,
    openExcelFile,
    skipHeader,
)
from fastcs_bacnet.core.BAC0.subscription_id import (
    IPv4SocketAddress,
    ObjectIdentifier,
    SubscriptionID,
)


def parse_ede(
    file_path: str, config_dir: str, header_rows: int = 0
) -> dict[SubscriptionID, str]:
    """
    Creates a mapping of subscriptions to PV names from an EDE and config file

    file_path: Path to the EDE file as a string
    config_dir: Path to the directory containing the bms config file as a string
        The file will be named bms.ini
    header_rows: Number of row before data starts on the EDE file
    """

    pv_names_dict = {}

    config_file = getBMSConfig(getIniFile(config_dir))

    if ".xls" in file_path or ".xlsx" in file_path:
        ede_file = openExcelFile(file_path)
    else:
        ede_file = openCsvFile(file_path)

    reader = csv.reader(ede_file, delimiter=",")
    reader = skipHeader(reader, IFM_FILE_TYPE, headerRows=header_rows)

    for row in reader:
        device_instance, object_instance_str, object_name, _, optional_fields = (
            extractData(row, IFM_FILE_TYPE)
        )

        object_type_int = optional_fields[0]

        ip = ip_from_row(row)

        subscription_id = SubscriptionID(
            IPv4SocketAddress(ip, 47808, int(device_instance)),
            ObjectIdentifier(
                object_type_as_string(object_type_int), int(object_instance_str)
            ),
        )

        pv_name = createPvName(
            object_instance_str, object_name, config_file, device_instance
        )

        checkPvNameLength(pv_name)

        pv_names_dict[subscription_id] = pv_name

    checkUniquePvNames(list(pv_names_dict.keys()))

    return pv_names_dict


def ip_from_row(row: list[str]) -> str:
    """
    Get IP address from a row of an EDE file
    """
    return row[17]


def object_type_as_string(object_type: int) -> str:
    """
    Maps integer object type to its string representation
    """

    object_type_enum = ObjectType(object_type)

    return object_type_enum.asn1
