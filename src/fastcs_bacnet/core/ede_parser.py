import csv
import ipaddress

from bacpypes3.primitivedata import ObjectType
from dls_bms.bms import (
    IFM_FILE_TYPE,
    checkPvNameLength,
    checkUniquePvNames,
    createPvName,
    extractData,
    getBMSConfig,
    getIniFile,
    openExcelFile,
    skipHeader,
)

from fastcs_bacnet.core.BAC0.subscription_id import (
    IPv4SocketAddress,
    ObjectIdentifier,
    SubscriptionID,
)
from fastcs_bacnet.core.pv_mapping import PvMappingEntry, pv_names_dict

# The default port all BACnet devices use by convention
# 47808 is BAC0 in hex
BACNET_PORT = 47808


class IpMappingError(ValueError):
    """Raised when the Device to IP mapping file is invalid or incomplete"""


def parse_ip_mapping_file(file_path: str) -> dict[int, IPv4SocketAddress]:
    """Create a mapping of Device IDs to IP addresses

    file_path: Path to a CSV file with "device" and "ip" columns

    Raises IpMappingError if the file is missing a column, has an invalid
    Device ID or IP address, or lists the same Device ID more than once.
    """

    result: dict[int, IPv4SocketAddress] = {}
    # utf-8-sig removes the byte-order mark that Excel adds to UTF-8 CSV exports
    with open(file_path, encoding="utf-8-sig", newline="") as csvfile:
        reader = csv.DictReader(csvfile, skipinitialspace=True)
        fieldnames = [name.strip() for name in reader.fieldnames or []]
        missing_columns = {"device", "ip"} - set(fieldnames)
        if missing_columns:
            raise IpMappingError(
                f"{file_path} is missing column(s) {sorted(missing_columns)}, "
                f"found {fieldnames}"
            )
        reader.fieldnames = fieldnames

        for row in reader:
            location = f"{file_path} line {reader.line_num}"
            device_str = (row["device"] or "").strip()
            ip_str = (row["ip"] or "").strip()

            # Skip rows that are blank apart from separators, e.g. ","
            if not device_str and not ip_str:
                continue

            try:
                device = int(device_str)
            except ValueError as e:
                raise IpMappingError(
                    f"{location}: invalid Device ID {device_str!r}"
                ) from e

            try:
                ip = str(ipaddress.IPv4Address(ip_str))
            except ValueError as e:
                raise IpMappingError(
                    f"{location}: invalid IPv4 address {ip_str!r} for device {device}"
                ) from e

            if device in result:
                raise IpMappingError(
                    f"{location}: duplicate Device ID {device} (IP {ip}), already "
                    f"mapped to IP {result[device].ip_address}"
                )

            result[device] = IPv4SocketAddress(ip, BACNET_PORT, device)

    return result


def parse_ede(
    file_path: str,
    config_dir: str,
    ip_mapping: dict[int, IPv4SocketAddress],
    header_rows: int = 0,
) -> list[PvMappingEntry]:
    """
    Creates a PvMappingEntry for each object in an EDE file, naming its PV
    according to the config file

    file_path: Path to the EDE file as a string
    config_dir: Path to the directory containing the bms config file as a string
        The file will be named bms.ini
    ip_mapping: Dictionary mapping a Device ID to its IPv4 address. Every device
        in the EDE file must be present.
    header_rows: Number of row before data starts on the EDE file

    Raises IpMappingError if any device in the EDE file is not in ip_mapping
    """

    entries: list[PvMappingEntry] = []
    unmapped_devices: set[int] = set()

    config_file = getBMSConfig(getIniFile(config_dir))

    ede_file = openExcelFile(file_path)

    reader = csv.reader(ede_file, delimiter=",")
    reader = skipHeader(reader, IFM_FILE_TYPE, headerRows=header_rows)

    for row in reader:
        device_instance, object_instance_str, object_name, _, optional_fields = (
            extractData(row, IFM_FILE_TYPE)
        )

        object_type_int = int(optional_fields[0])
        object_description = optional_fields[1]

        device_id = int(device_instance)
        if device_id not in ip_mapping:
            unmapped_devices.add(device_id)
            continue

        subscription_id = SubscriptionID(
            ip_mapping[device_id],
            ObjectIdentifier(
                object_type_as_string(object_type_int), int(object_instance_str)
            ),
        )

        pv_name = createPvName(
            object_instance_str, object_name, config_file, device_instance
        )

        checkPvNameLength(pv_name)

        entries.append(
            PvMappingEntry(
                subscription_id=subscription_id,
                object_type=object_type_int,
                object_name=object_name,
                object_description=object_description,
                pv_name=pv_name,
            )
        )

    if unmapped_devices:
        raise IpMappingError(
            f"Device(s) {sorted(unmapped_devices)} in EDE file {file_path} have no "
            "entry in the Device to IP mapping file"
        )

    checkUniquePvNames(list(pv_names_dict(entries).keys()))

    return entries


def object_type_as_string(object_type: int) -> str:
    """
    Maps integer object type to its string representation
    """

    object_type_enum = ObjectType(object_type)

    return object_type_enum.asn1
