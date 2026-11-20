"""
Convert the BMS XML export (e.g. dls-last-saved.xml) into the files fastcs-bacnet
reads: the EDE file and the Device to IP mapping file.

The XML holds one DEVICE element per BACnet device, with its address in
SRC_ADDRESS and the objects to subscribe to in OBJECT_LIST.
"""

import csv
import datetime
import ipaddress
import xml.etree.ElementTree as ET
from argparse import ArgumentParser
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

import openpyxl

from fastcs_bacnet.core.ede_parser import (
    BACNET_PORT,
    EDE_HEADING_MARKER,
    EDE_SHEET_NAME,
    MAX_OBJECT_TYPE,
)

# Column headings of the EDE file. The repeated and oddly placed headings are
# deliberate: dls_bms reads inactive-text, active-text and unit-code from
# columns O, P and Q of this layout, and checks the headings of O and P.
EDE_COLUMNS = [
    EDE_HEADING_MARKER,
    "device-obj-instance",
    "object-name",
    "object-type",
    "object-instance",
    "description",
    "present-value-default",
    "min-present-value",
    "max-present-value",
    "commandValue",
    "hi-limit",
    "low-limit",
    "unit-code",
    "Inactive-Text",
    "Inactive-Text",
    "Active-Text",
    "unit-code",
]
# Row of the column headings, counting from 1. fastcs-bacnet finds the headings
# wherever they are, but dls_bms still expects them on row 8.
EDE_HEADING_ROW = 8


class BmsXmlError(ValueError):
    """Raised when the BMS XML file cannot be converted"""


@dataclass(frozen=True)
class BmsObject:
    """One BACnet object from the BMS XML file"""

    object_type: int
    instance: int
    name: str
    description: str
    units: int | None
    inactive_text: str
    active_text: str


@dataclass(frozen=True)
class BmsDevice:
    """One BACnet device from the BMS XML file and the objects subscribed to"""

    instance: int
    name: str
    description: str
    ip_address: str
    objects: list[BmsObject]


def ip_from_mac(mac: str, device: int) -> str:
    """
    Decode the IP address from a BACnet/IP MAC address

    A BACnet/IP MAC address is 6 bytes: the 4 byte IPv4 address followed by the
    2 byte UDP port, e.g. "c0:a8:04:80:ba:c0" is 192.168.4.128 port 0xBAC0.
    fastcs-bacnet assumes every device uses the standard port, so any other port
    is rejected.
    """
    try:
        octets = [int(part, 16) for part in mac.split(":")]
        if len(octets) != 6 or not all(0 <= octet <= 255 for octet in octets):
            raise ValueError
    except ValueError as e:
        raise BmsXmlError(
            f"Device {device}: MAC {mac!r} is not a 6 byte BACnet/IP address"
        ) from e

    port = octets[4] << 8 | octets[5]
    if port != BACNET_PORT:
        raise BmsXmlError(
            f"Device {device}: MAC {mac!r} uses port {port}, only the standard "
            f"BACnet port {BACNET_PORT} is supported"
        )

    return str(ipaddress.IPv4Address(bytes(octets[:4])))


def _properties(element: ET.Element) -> dict[str, str]:
    """Map each PROPERTY of an OBJECT by its NAME attribute to its text"""
    return {
        prop.get("NAME", ""): (prop.text or "").strip()
        for prop in element.findall("PROPERTY")
    }


def _parse_units(units: str | None, device: int, instance: int) -> int | None:
    """Extract the BACnet unit code from e.g. "62  - degrees-celsius" """
    if not units:
        return None
    code = units.split("-", 1)[0].strip()
    try:
        return int(code)
    except ValueError as e:
        raise BmsXmlError(
            f"Device {device} object {instance}: unrecognised units {units!r}"
        ) from e


def _parse_object(element: ET.Element, device: int) -> BmsObject:
    object_type = int(element.get("TYPE", ""))
    instance = int(element.get("INSTANCE", ""))
    if not 0 <= object_type <= MAX_OBJECT_TYPE:
        raise BmsXmlError(
            f"Device {device} object {instance}: unsupported object type {object_type}"
        )

    properties = _properties(element)
    name = properties.get("object-name") or (element.findtext("NAME") or "").strip()
    if not name:
        raise BmsXmlError(f"Device {device} object {instance}: has no name")

    return BmsObject(
        object_type=object_type,
        instance=instance,
        name=name,
        description=properties.get("description", ""),
        units=_parse_units(properties.get("units"), device, instance),
        inactive_text=properties.get("inactive-text", ""),
        active_text=properties.get("active-text", ""),
    )


def _parse_device(element: ET.Element) -> BmsDevice:
    try:
        instance = int(element.get("ADDR", ""))
    except ValueError as e:
        raise BmsXmlError(
            f"DEVICE has invalid ADDR {element.get('ADDR')!r}, expected the "
            "device instance number"
        ) from e

    address = element.find("SRC_ADDRESS")
    if address is None:
        raise BmsXmlError(f"Device {instance}: has no SRC_ADDRESS")
    if address.get("NET", "0") != "0":
        # The MAC of a device on a remote network is not its IP address
        raise BmsXmlError(
            f"Device {instance}: is on remote BACnet network {address.get('NET')}, "
            "only devices reachable directly over BACnet/IP are supported"
        )

    objects = []
    for object_element in element.findall("OBJECT_LIST/OBJECT"):
        try:
            if (object_element.findtext("SUBSCRIBE") or "").strip() != "1":
                continue
            objects.append(_parse_object(object_element, instance))
        except ValueError as e:
            if isinstance(e, BmsXmlError):
                raise
            raise BmsXmlError(
                f"Device {instance}: OBJECT has invalid TYPE "
                f"{object_element.get('TYPE')!r} or INSTANCE "
                f"{object_element.get('INSTANCE')!r}"
            ) from e

    return BmsDevice(
        instance=instance,
        name=(element.findtext("NAME") or "").strip(),
        description=(element.findtext("DESCRIPTION") or "").strip(),
        ip_address=ip_from_mac(address.get("MAC", ""), instance),
        objects=objects,
    )


def parse_bms_xml(file_path: str | Path) -> list[BmsDevice]:
    """
    Read every device, and the objects subscribed to on it, from the BMS XML file

    Only objects with SUBSCRIBE set to 1 are included.

    Raises BmsXmlError if the file is invalid, or a device or object appears more
    than once.
    """
    try:
        root = ET.parse(file_path).getroot()
    except ET.ParseError as e:
        raise BmsXmlError(f"{file_path} is not valid XML: {e}") from e

    devices = [_parse_device(element) for element in root.iter("DEVICE")]

    seen_devices: set[int] = set()
    for device in devices:
        if device.instance in seen_devices:
            raise BmsXmlError(f"Device {device.instance} appears more than once")
        seen_devices.add(device.instance)

        seen_objects: set[tuple[int, int]] = set()
        for obj in device.objects:
            key = (obj.object_type, obj.instance)
            if key in seen_objects:
                raise BmsXmlError(
                    f"Device {device.instance}: object type {obj.object_type} "
                    f"instance {obj.instance} appears more than once"
                )
            seen_objects.add(key)

    return devices


def write_ip_mapping(devices: Sequence[BmsDevice], file_path: str | Path) -> None:
    """Write the Device to IP mapping CSV file read by fastcs-bacnet"""
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["device", "ip"])
        for device in devices:
            writer.writerow([device.instance, device.ip_address])


def write_ede(
    devices: Sequence[BmsDevice],
    file_path: str | Path,
    title: str,
    timestamp: datetime.date | None = None,
) -> None:
    """
    Write the EDE Excel file read by fastcs-bacnet

    The layout follows the EDE files supplied by IFM: a title, project details,
    then the column headings on row 8, then one row per object.

    title: text for the first row, e.g. the name of the source file
    timestamp: date recorded as the time of last change, default today
    """
    timestamp = timestamp or datetime.date.today()

    workbook = openpyxl.Workbook()
    sheet = workbook.active
    assert sheet is not None
    sheet.title = EDE_SHEET_NAME

    header_rows: list[list[str]] = [
        [title],
        [],
        ["# PROJECT_NAME", "IFM Diamond Light Source"],
        ["# VERSION_OF_REFERENCEFILE", "1"],
        ["# TIMESTAMP_OF_LAST_CHANGE", timestamp.strftime("%d.%m.%Y")],
        ["# VERSION_OF_LAYOUT", "2.2"],
        ["# mandatory"] + ["mandatory"] * 4 + ["optional"] * 12,
        EDE_COLUMNS,
    ]
    assert len(header_rows) == EDE_HEADING_ROW
    for header_row in header_rows:
        sheet.append(header_row)

    for device in devices:
        for obj in device.objects:
            row: list[str | int | None] = [None] * len(EDE_COLUMNS)
            row[0] = obj.name
            row[1] = device.instance
            row[2] = obj.name
            row[3] = obj.object_type
            row[4] = obj.instance
            row[5] = obj.description or None
            row[12] = obj.units
            row[14] = obj.inactive_text or None
            row[15] = obj.active_text or None
            row[16] = obj.units
            sheet.append(row)

    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    workbook.save(path)


def main(args: Sequence[str] | None = None) -> None:
    parser = ArgumentParser(
        description="Create the EDE file and Device to IP mapping file used by "
        + "fastcs-bacnet from the BMS XML export"
    )
    parser.add_argument("xml_file", type=str, help="Filepath to the BMS XML file")
    parser.add_argument(
        "--ede",
        type=str,
        metavar="PATH",
        help="Write the EDE file (.xlsx) here",
    )
    parser.add_argument(
        "--ip-mapping",
        type=str,
        metavar="PATH",
        help="Write the Device to IP mapping file (.csv) here",
    )

    args_namespace = parser.parse_args(args)
    if args_namespace.ede is None and args_namespace.ip_mapping is None:
        parser.error("at least one of --ede and --ip-mapping is required")
    if args_namespace.ede is not None and Path(args_namespace.ede).suffix != ".xlsx":
        parser.error("--ede must be a .xlsx file")

    try:
        devices = parse_bms_xml(args_namespace.xml_file)
    except (BmsXmlError, OSError) as e:
        parser.exit(1, f"error: {e}\n")

    if args_namespace.ip_mapping is not None:
        write_ip_mapping(devices, args_namespace.ip_mapping)
        print(f"Wrote {len(devices)} devices to {args_namespace.ip_mapping}")

    if args_namespace.ede is not None:
        title = f"EDE file generated from {Path(args_namespace.xml_file).name}"
        write_ede(devices, args_namespace.ede, title)
        n_objects = sum(len(device.objects) for device in devices)
        print(f"Wrote {n_objects} objects to {args_namespace.ede}")


if __name__ == "__main__":
    main()
