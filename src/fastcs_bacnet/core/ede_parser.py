import csv
import ipaddress
import math
import re
from dataclasses import dataclass
from typing import Any

import pandas
from bacpypes3.primitivedata import ObjectType
from dls_bms.bms import (
    checkPvNameLength,
    checkUniquePvNames,
    createPvName,
    getBMSConfig,
    getIniFile,
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


EDE_SHEET_NAME = "EDE"

# The first cell of the row of column headings in an EDE file. Rows above it
# are a title and project details, which vary between files.
EDE_HEADING_MARKER = "# keyname"

# Headings of the columns read from an EDE file. They are matched ignoring case,
# spaces and punctuation, so "device-obj-instance" also matches the
# "device obj.-instance" found in some files.
DEVICE_INSTANCE_HEADING = "device-obj-instance"
OBJECT_NAME_HEADING = "object-name"
OBJECT_TYPE_HEADING = "object-type"
OBJECT_INSTANCE_HEADING = "object-instance"
DESCRIPTION_HEADING = "description"
REQUIRED_HEADINGS = (
    DEVICE_INSTANCE_HEADING,
    OBJECT_NAME_HEADING,
    OBJECT_TYPE_HEADING,
    OBJECT_INSTANCE_HEADING,
)

# Only the analog and binary input, output and value types are supported
MAX_OBJECT_TYPE = 5


class IpMappingError(ValueError):
    """Raised when the Device to IP mapping file is invalid or incomplete"""


class EdeFormatError(ValueError):
    """Raised when an EDE file does not have the expected headings or values"""


@dataclass(frozen=True)
class EdeObject:
    """
    One BACnet object read from an EDE file

    row: row number in the spreadsheet, counting from 1, for error messages
    """

    row: int
    device_instance: int
    object_name: str
    object_type: int
    object_instance: int
    description: str


def _normalise_heading(heading: str) -> str:
    """Reduce a column heading to lower case letters and digits"""
    return re.sub(r"[^a-z0-9]", "", heading.lower())


def _cell_text(value: Any) -> str:
    """
    Convert a spreadsheet cell to text

    Empty cells become "", and whole numbers lose any ".0" a spreadsheet may
    have stored them with.
    """
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return ""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value).strip()


def _find_columns(
    rows: list[list[str]], file_path: str
) -> tuple[int, dict[str, int | None]]:
    """
    Find the row of column headings and the column of each heading read

    Returns the index of the heading row, and a map of each heading to its column
    index. The description column is optional, and maps to None if missing.
    """
    marker = _normalise_heading(EDE_HEADING_MARKER)
    heading_rows = [
        index
        for index, row in enumerate(rows)
        if row and _normalise_heading(row[0]) == marker
    ]
    if len(heading_rows) != 1:
        raise EdeFormatError(
            f"{file_path} must have one row of column headings starting with "
            f"{EDE_HEADING_MARKER!r}, found {len(heading_rows)}"
        )
    heading_row = heading_rows[0]

    columns: dict[str, list[int]] = {}
    for column, heading in enumerate(rows[heading_row]):
        columns.setdefault(_normalise_heading(heading), []).append(column)

    found: dict[str, int | None] = {}
    for heading in (*REQUIRED_HEADINGS, DESCRIPTION_HEADING):
        matches = columns.get(_normalise_heading(heading), [])
        if len(matches) > 1:
            raise EdeFormatError(
                f"{file_path} row {heading_row + 1}: column heading {heading!r} "
                "appears more than once"
            )
        if not matches and heading in REQUIRED_HEADINGS:
            raise EdeFormatError(
                f"{file_path} row {heading_row + 1}: missing column heading {heading!r}"
            )
        found[heading] = matches[0] if matches else None

    return heading_row, found


def read_ede(file_path: str) -> list[EdeObject]:
    """
    Read the BACnet objects from the "EDE" sheet of an EDE Excel file

    The row of column headings is found by its first cell, "# keyname", and
    columns are found by their headings. So rows may be added above the headings,
    and columns added or reordered, without changing this code. Blank rows, and
    rows starting with "#" (comments in the EDE format), are skipped.

    Raises EdeFormatError if the headings are missing or a value is invalid.
    """
    data = pandas.read_excel(
        file_path,
        sheet_name=EDE_SHEET_NAME,
        header=None,
        dtype=object,
        keep_default_na=False,
    )
    rows = [[_cell_text(value) for value in row] for row in data.itertuples(False)]

    heading_row, columns = _find_columns(rows, file_path)

    def cell(row: list[str], heading: str) -> str:
        column = columns[heading]
        return row[column] if column is not None and column < len(row) else ""

    objects: list[EdeObject] = []
    for index in range(heading_row + 1, len(rows)):
        row = rows[index]
        if not any(row) or row[0].startswith("#"):
            continue

        location = f"{file_path} row {index + 1}"
        values: dict[str, int] = {}
        for heading in (
            DEVICE_INSTANCE_HEADING,
            OBJECT_TYPE_HEADING,
            OBJECT_INSTANCE_HEADING,
        ):
            try:
                values[heading] = int(cell(row, heading))
            except ValueError as e:
                raise EdeFormatError(
                    f"{location}: invalid {heading} {cell(row, heading)!r}"
                ) from e

        object_type = values[OBJECT_TYPE_HEADING]
        if not 0 <= object_type <= MAX_OBJECT_TYPE:
            raise EdeFormatError(f"{location}: unsupported object-type {object_type}")

        object_name = cell(row, OBJECT_NAME_HEADING)
        if not object_name:
            raise EdeFormatError(f"{location}: missing object-name")

        objects.append(
            EdeObject(
                row=index + 1,
                device_instance=values[DEVICE_INSTANCE_HEADING],
                object_name=object_name,
                object_type=object_type,
                object_instance=values[OBJECT_INSTANCE_HEADING],
                description=cell(row, DESCRIPTION_HEADING),
            )
        )

    return objects


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
) -> list[PvMappingEntry]:
    """
    Creates a PvMappingEntry for each object in an EDE file, naming its PV
    according to the config file

    file_path: Path to the EDE file as a string, see read_ede for its format
    config_dir: Path to the directory containing the bms config file as a string
        The file will be named bms.ini
    ip_mapping: Dictionary mapping a Device ID to its IPv4 address. Every device
        in the EDE file must be present.

    Raises EdeFormatError if the EDE file is invalid, and IpMappingError if any
    device in the EDE file is not in ip_mapping
    """

    entries: list[PvMappingEntry] = []
    unmapped_devices: set[int] = set()

    config_file = getBMSConfig(getIniFile(config_dir))

    for ede_object in read_ede(file_path):
        device_id = ede_object.device_instance
        if device_id not in ip_mapping:
            unmapped_devices.add(device_id)
            continue

        subscription_id = SubscriptionID(
            ip_mapping[device_id],
            ObjectIdentifier(
                object_type_as_string(ede_object.object_type),
                ede_object.object_instance,
            ),
        )

        # dls_bms looks devices up in bms.ini by their instance as a string
        pv_name = createPvName(
            str(ede_object.object_instance),
            ede_object.object_name,
            config_file,
            str(device_id),
        )

        checkPvNameLength(pv_name)

        entries.append(
            PvMappingEntry(
                subscription_id=subscription_id,
                object_type=ede_object.object_type,
                object_name=ede_object.object_name,
                object_description=ede_object.description,
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
