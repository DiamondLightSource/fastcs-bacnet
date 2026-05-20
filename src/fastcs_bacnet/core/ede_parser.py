import csv

from bacpypes3.primitivedata import ObjectType

from dls_bms.bms import (
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
from fastcs_bacnet.practical.BAC0.subscription_id import (
    IPv4SocketAddress,
    ObjectIdentifier,
    SubscriptionID,
)


def parse_ede(
    file_path: str, header_rows: int, config_dir: str
) -> dict[SubscriptionID, str]:

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
            IPv4SocketAddress(ip, 47808),
            ObjectIdentifier(
                object_type_as_string(object_type_int), int(object_instance_str)
            ),
        )

        pv_name = createPvName(
            object_instance_str, object_name, config_file, device_instance
        )

        # do some final checks, raise exceptions, log warnings / errors
        checkPvNameLength(pv_name)

        pv_names_dict[subscription_id] = pv_name

    checkUniquePvNames(list(pv_names_dict.keys()))

    return pv_names_dict


def ip_from_row(row: list[str]) -> str:
    return row[17]


def object_type_as_string(object_type: int) -> str:

    object_type_enum = ObjectType(object_type)

    return object_type_enum.asn1
