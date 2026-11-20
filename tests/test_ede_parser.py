from pathlib import Path
from typing import Any

import openpyxl
import pytest

from fastcs_bacnet.core.BAC0.subscription_id import IPv4SocketAddress
from fastcs_bacnet.core.ede_parser import (
    BACNET_PORT,
    EdeFormatError,
    EdeObject,
    IpMappingError,
    parse_ede,
    parse_ip_mapping_file,
    read_ede,
)

REPO_ROOT = Path(__file__).parent.parent
EXAMPLES_DIR = REPO_ROOT / "src" / "fastcs_bacnet" / "data" / "examples"
EDE_FILE = EXAMPLES_DIR / "gizmo_EDE.xlsx"
# dls_bms appends "bms.ini" by string concatenation, so a trailing slash is needed
BMS_CONFIG_DIR = f"{REPO_ROOT / 'src' / 'dls_bms' / 'tests'}/"
EXAMPLE_DEVICE = 2098177


def write_csv(tmp_path: Path, content: str, encoding: str = "utf-8") -> str:
    path = tmp_path / "mapping.csv"
    path.write_text(content, encoding=encoding)
    return str(path)


def test_parse_ip_mapping_file_example():
    mapping = parse_ip_mapping_file(str(EXAMPLES_DIR / "device_ip_mapping.csv"))

    assert mapping == {
        EXAMPLE_DEVICE: IPv4SocketAddress("172.23.240.101", BACNET_PORT, EXAMPLE_DEVICE)
    }


def test_parse_ip_mapping_file_tolerates_formatting(tmp_path: Path):
    """Excel byte-order mark, padding around values and blank-looking rows"""
    path = write_csv(
        tmp_path,
        "device, ip\r\n 1 , 10.0.0.1 \r\n,\r\n\r\n2,10.0.0.2\r\n",
        encoding="utf-8-sig",
    )

    assert parse_ip_mapping_file(path) == {
        1: IPv4SocketAddress("10.0.0.1", BACNET_PORT, 1),
        2: IPv4SocketAddress("10.0.0.2", BACNET_PORT, 2),
    }


@pytest.mark.parametrize(
    "content, error",
    [
        ("device,address\n1,10.0.0.1\n", r"missing column\(s\) \['ip'\]"),
        ("device,ip\n1,10.0.0.1\n1,10.0.0.2\n", "line 3: duplicate Device ID 1"),
        ("device,ip\nabc,10.0.0.1\n", "line 2: invalid Device ID 'abc'"),
        ("device,ip\n1,10.0.0.1011\n", "line 2: invalid IPv4 address '10.0.0.1011'"),
        ("device,ip\n1,\n", "line 2: invalid IPv4 address ''"),
    ],
)
def test_parse_ip_mapping_file_errors(tmp_path: Path, content: str, error: str):
    path = write_csv(tmp_path, content)

    with pytest.raises(IpMappingError, match=error):
        parse_ip_mapping_file(path)


def test_parse_ede_uses_ip_mapping():
    address = IPv4SocketAddress("10.0.0.1", BACNET_PORT, EXAMPLE_DEVICE)

    entries = parse_ede(
        str(EDE_FILE),
        BMS_CONFIG_DIR,
        {EXAMPLE_DEVICE: address},
    )

    assert entries
    assert all(entry.subscription_id.socket_address == address for entry in entries)


def test_parse_ede_unmapped_device():
    with pytest.raises(IpMappingError, match=rf"\[{EXAMPLE_DEVICE}\]"):
        parse_ede(
            str(EDE_FILE),
            BMS_CONFIG_DIR,
            {1: IPv4SocketAddress("10.0.0.1", BACNET_PORT, 1)},
        )


def write_ede_xlsx(tmp_path: Path, rows: list[list[Any]]) -> str:
    path = tmp_path / "EDE.xlsx"
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    assert sheet is not None
    sheet.title = "EDE"
    for row in rows:
        sheet.append(row)
    workbook.save(path)
    return str(path)


HEADINGS = [
    "# keyname",
    "device-obj-instance",
    "object-name",
    "object-type",
    "object-instance",
    "description",
]


def test_read_ede_example():
    assert read_ede(str(EDE_FILE)) == [
        EdeObject(9, EXAMPLE_DEVICE, "DH'GF'Giz'AO4", 1, 4, ""),
        EdeObject(10, EXAMPLE_DEVICE, "DH'GF'Giz'AI6", 0, 6, ""),
        EdeObject(11, EXAMPLE_DEVICE, "DH'GF'Giz'BO3", 4, 3, ""),
    ]


def test_read_ede_independent_of_layout(tmp_path: Path):
    """Headings on any row, columns in any order, spelt in different ways"""
    path = write_ede_xlsx(
        tmp_path,
        [
            ["A different title"],
            ["# PROJECT_NAME", "Somewhere"],
            [],
            ["# mandatory", "mandatory"],
            [
                "# Keyname",
                "Object Instance",
                "new-column",
                "Description",
                "OBJECT_NAME",
                "device obj.-instance",
                "object-type",
            ],
            ["AI1", 7, "x", "Temperature", "AI1", 100, 0],
            [],
            ["# a comment", "not", "an", "object"],
            # Numbers stored as text or as whole-number floats
            ["BV2", "8", None, None, "BV2", 100.0, "5"],
            [None, None, None, None, None, None, None],
        ],
    )

    assert read_ede(path) == [
        EdeObject(6, 100, "AI1", 0, 7, "Temperature"),
        EdeObject(9, 100, "BV2", 5, 8, ""),
    ]


def test_read_ede_description_is_optional(tmp_path: Path):
    path = write_ede_xlsx(tmp_path, [HEADINGS[:5], ["AI1", 100, "AI1", 0, 7]])

    assert read_ede(path) == [EdeObject(2, 100, "AI1", 0, 7, "")]


@pytest.mark.parametrize(
    "rows, error",
    [
        ([["title"], ["AI1", 100, "AI1", 0, 7]], "found 0"),
        ([HEADINGS, HEADINGS], "found 2"),
        ([HEADINGS[:4]], "row 1: missing column heading 'object-instance'"),
        (
            [HEADINGS + ["Object Name"]],
            "row 1: column heading 'object-name' appears more than once",
        ),
        (
            [["title"], HEADINGS, ["AI1", "abc", "AI1", 0, 7]],
            "row 3: invalid device-obj-instance 'abc'",
        ),
        (
            [HEADINGS, ["AI1", 100, "AI1", 0, 7.5]],
            "row 2: invalid object-instance '7.5'",
        ),
        ([HEADINGS, ["AI1", 100, "AI1", "", 7]], "row 2: invalid object-type ''"),
        ([HEADINGS, ["AI1", 100, "AI1", 8, 7]], "row 2: unsupported object-type 8"),
        ([HEADINGS, ["AI1", 100, None, 0, 7]], "row 2: missing object-name"),
    ],
)
def test_read_ede_errors(tmp_path: Path, rows: list[list[Any]], error: str):
    path = write_ede_xlsx(tmp_path, rows)

    with pytest.raises(EdeFormatError, match=error):
        read_ede(path)


def test_read_ede_ifm_example():
    """An EDE file as supplied by IFM, with text cells and its own headings"""
    objects = read_ede(str(REPO_ROOT / "data" / "examples" / "test_EDE.xlsx"))

    assert objects[0] == EdeObject(
        9, 16864, "DEB'1stFlr'B1.1.01'NatV'B1.1.17'TR", 2, 317, "Room temperature"
    )
