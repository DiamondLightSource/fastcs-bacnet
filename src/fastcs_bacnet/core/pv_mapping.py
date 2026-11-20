import os
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

import pandas

from fastcs_bacnet.core.BAC0.subscription_id import SubscriptionID

# Column headings of the BMS to EPICS mapping file supplied to IFM
MAPPING_COLUMNS = [
    "Device",
    "Device description",
    "Type",
    "Instance",
    "Object BACnet name",
    "Object description",
    "EPICS name",
]
MAPPING_SHEET_NAME = "epics-bars-output"
MAPPING_FILE_SUFFIXES = (".csv", ".xlsx")


@dataclass(frozen=True)
class PvMappingEntry:
    """
    Everything known about one BACnet object and the EPICS PV it is served as

    subscription_id: identifies the device and object
    object_type: BACnet object type code, as given in the EDE file (e.g. 0 for
        analog-input)
    object_name: BACnet object name from the EDE file
    object_description: description from the EDE file, empty if there is none
    pv_name: full name of the EPICS PV
    """

    subscription_id: SubscriptionID
    object_type: int
    object_name: str
    object_description: str
    pv_name: str


def pv_names_dict(entries: Iterable[PvMappingEntry]) -> dict[SubscriptionID, str]:
    """Map each subscription to the name of its EPICS PV"""
    return {entry.subscription_id: entry.pv_name for entry in entries}


def check_mapping_file_path(file_path: str | Path) -> Path:
    """
    Check that a mapping file can be written in the format implied by its suffix

    Raises ValueError if the suffix is not one of MAPPING_FILE_SUFFIXES
    """
    path = Path(file_path)
    if path.suffix.lower() not in MAPPING_FILE_SUFFIXES:
        raise ValueError(
            f"PV mapping file {path} must have one of the suffixes "
            f"{list(MAPPING_FILE_SUFFIXES)}"
        )
    return path


def write_pv_mapping(entries: Iterable[PvMappingEntry], file_path: str | Path) -> None:
    """
    Write the BMS to EPICS mapping file, as CSV or Excel depending on its suffix

    Rows are sorted by device, object type and object instance. Any missing parent
    directories are created. The file is written under a temporary name and then
    renamed, so a reader never sees a partially written file.

    entries: the objects to write, one row each
    file_path: destination, ending in .csv or .xlsx
    """
    path = check_mapping_file_path(file_path)

    rows = sorted(
        (
            entry.subscription_id.socket_address.device_instance,
            # No source of device descriptions yet, so the column is left empty
            "",
            entry.object_type,
            entry.subscription_id.object_id.object_instance,
            entry.object_name,
            entry.object_description,
            entry.pv_name,
        )
        for entry in entries
    )
    data = pandas.DataFrame(rows, columns=MAPPING_COLUMNS)

    path.parent.mkdir(parents=True, exist_ok=True)
    # Keep the real suffix so pandas still recognises the format
    temp_path = path.with_name(f".{path.stem}.tmp{path.suffix}")
    try:
        if path.suffix.lower() == ".csv":
            data.to_csv(temp_path, index=False)
        else:
            data.to_excel(
                temp_path, sheet_name=MAPPING_SHEET_NAME, index=False, engine="openpyxl"
            )
        os.replace(temp_path, path)
    finally:
        temp_path.unlink(missing_ok=True)
