from pathlib import Path

import pytest

from fastcs_bacnet.core.BAC0.subscription_id import IPv4SocketAddress
from fastcs_bacnet.core.ede_parser import (
    BACNET_PORT,
    IpMappingError,
    parse_ede,
    parse_ip_mapping_file,
)

REPO_ROOT = Path(__file__).parent.parent
EXAMPLES_DIR = REPO_ROOT / "src" / "fastcs_bacnet" / "data" / "examples"
EDE_FILE = EXAMPLES_DIR / "gizmo_EDE.xlsx"
EDE_HEADER_ROWS = 8
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
        header_rows=EDE_HEADER_ROWS,
    )

    assert entries
    assert all(entry.subscription_id.socket_address == address for entry in entries)


def test_parse_ede_unmapped_device():
    with pytest.raises(IpMappingError, match=rf"\[{EXAMPLE_DEVICE}\]"):
        parse_ede(
            str(EDE_FILE),
            BMS_CONFIG_DIR,
            {1: IPv4SocketAddress("10.0.0.1", BACNET_PORT, 1)},
            header_rows=EDE_HEADER_ROWS,
        )
