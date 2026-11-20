import datetime
from pathlib import Path

import openpyxl
import pytest

from fastcs_bacnet.bms_xml_converter import (
    EDE_HEADING_ROW,
    EDE_SHEET_NAME,
    BmsDevice,
    BmsObject,
    BmsXmlError,
    ip_from_mac,
    main,
    parse_bms_xml,
    write_ede,
    write_ip_mapping,
)
from fastcs_bacnet.core.BAC0.subscription_id import IPv4SocketAddress
from fastcs_bacnet.core.ede_parser import (
    BACNET_PORT,
    parse_ede,
    parse_ip_mapping_file,
)
from tests.test_ede_parser import BMS_CONFIG_DIR

# Structure copied from dls-last-saved.xml. Device 193 is in the test bms.ini.
DEVICE_193 = """
<DEVICE ADDR="193">
    <NAME>POL908_FFBD58</NAME>
    <DESCRIPTION>Chiller #1</DESCRIPTION>
    <MAX_APDU>1476</MAX_APDU>
    <SEG_SUPPORT>0</SEG_SUPPORT>
    <SRC_ADDRESS MAC="c0:a8:04:80:ba:c0" LOCAL="1" LEN="6" NET="0" HWADDR="">
    </SRC_ADDRESS>
    <TRUE_NUM_OBJECTS>1</TRUE_NUM_OBJECTS>
    <RPM_SUPPORT>0</RPM_SUPPORT>
    <OBJECT_LIST>
        <OBJECT TYPE="0" INSTANCE="2538" CLIENTINDEX="1">
            <NAME>IO_DspTCdsOut</NAME>
            <SUBSCRIBE>1</SUBSCRIBE>
            <PROPERTY ID="22" NAME="cov-increment">0.100000 FLOAT</PROPERTY>
            <PROPERTY ID="28" NAME="description">Dsp.TCdsOut</PROPERTY>
            <PROPERTY ID="77" NAME="object-name">IO_DspTCdsOut</PROPERTY>
            <PROPERTY ID="85" NAME="present-value">23.756977 FLOAT</PROPERTY>
            <PROPERTY ID="117" NAME="units">62  - degrees-celsius</PROPERTY>
        </OBJECT>
        <OBJECT TYPE="3" INSTANCE="12" CLIENTINDEX="2">
            <NAME>IO_PumpRun</NAME>
            <SUBSCRIBE>1</SUBSCRIBE>
            <PROPERTY ID="4" NAME="active-text">Running</PROPERTY>
            <PROPERTY ID="28" NAME="description">Pump.Run</PROPERTY>
            <PROPERTY ID="46" NAME="inactive-text">Stopped</PROPERTY>
            <PROPERTY ID="77" NAME="object-name">IO_PumpRun</PROPERTY>
        </OBJECT>
        <OBJECT TYPE="0" INSTANCE="99" CLIENTINDEX="3">
            <NAME>IO_NotWanted</NAME>
            <SUBSCRIBE>0</SUBSCRIBE>
            <PROPERTY ID="77" NAME="object-name">IO_NotWanted</PROPERTY>
        </OBJECT>
    </OBJECT_LIST>
</DEVICE>
"""

DEVICE_194 = """
<DEVICE ADDR="194">
    <NAME>POL908_FFBD59</NAME>
    <DESCRIPTION>Chiller #2</DESCRIPTION>
    <SRC_ADDRESS MAC="c0:a8:04:81:ba:c0" LOCAL="1" LEN="6" NET="0" HWADDR="">
    </SRC_ADDRESS>
    <OBJECT_LIST>
        <OBJECT TYPE="2" INSTANCE="5" CLIENTINDEX="1">
            <NAME>IO_Setpoint</NAME>
            <SUBSCRIBE>1</SUBSCRIBE>
            <PROPERTY ID="77" NAME="object-name">IO_Setpoint</PROPERTY>
        </OBJECT>
    </OBJECT_LIST>
</DEVICE>
"""


def write_xml(tmp_path: Path, *devices: str) -> Path:
    path = tmp_path / "bms.xml"
    path.write_text(f'<?xml version="1.0"?>\n<BACNET>{"".join(devices)}</BACNET>\n')
    return path


@pytest.mark.parametrize(
    "mac, ip",
    [
        ("c0:a8:04:80:ba:c0", "192.168.4.128"),
        ("AC:17:F0:65:BA:C0", "172.23.240.101"),
        ("0:0:0:1:ba:c0", "0.0.0.1"),
    ],
)
def test_ip_from_mac(mac: str, ip: str):
    assert ip_from_mac(mac, 1) == ip


@pytest.mark.parametrize(
    "mac, error",
    [
        ("c0:a8:04:80:ba:c1", "port 47809"),
        ("c0:a8:04:80", "not a 6 byte"),
        ("c0:a8:04:80:ba:c0:00", "not a 6 byte"),
        ("c0:a8:04:zz:ba:c0", "not a 6 byte"),
        ("c0:a8:04:100:ba:c0", "not a 6 byte"),
        ("", "not a 6 byte"),
    ],
)
def test_ip_from_mac_errors(mac: str, error: str):
    with pytest.raises(BmsXmlError, match=error):
        ip_from_mac(mac, 1)


def test_parse_bms_xml(tmp_path: Path):
    devices = parse_bms_xml(write_xml(tmp_path, DEVICE_193, DEVICE_194))

    assert devices == [
        BmsDevice(
            instance=193,
            name="POL908_FFBD58",
            description="Chiller #1",
            ip_address="192.168.4.128",
            objects=[
                BmsObject(0, 2538, "IO_DspTCdsOut", "Dsp.TCdsOut", 62, "", ""),
                BmsObject(3, 12, "IO_PumpRun", "Pump.Run", None, "Stopped", "Running"),
            ],
        ),
        BmsDevice(
            instance=194,
            name="POL908_FFBD59",
            description="Chiller #2",
            ip_address="192.168.4.129",
            objects=[BmsObject(2, 5, "IO_Setpoint", "", None, "", "")],
        ),
    ]


@pytest.mark.parametrize(
    "old, new, error",
    [
        ('NET="0"', 'NET="5"', "remote BACnet network 5"),
        ('ADDR="193"', 'ADDR="abc"', "invalid ADDR 'abc'"),
        ('TYPE="3"', 'TYPE="8"', "object 12: unsupported object type 8"),
        ('INSTANCE="12"', 'INSTANCE=""', "invalid TYPE '3' or INSTANCE ''"),
        ("62  - degrees", "x - degrees", "object 2538: unrecognised units"),
    ],
)
def test_parse_bms_xml_errors(tmp_path: Path, old: str, new: str, error: str):
    device = DEVICE_193.replace(old, new)

    with pytest.raises(BmsXmlError, match=error):
        parse_bms_xml(write_xml(tmp_path, device))


def test_parse_bms_xml_duplicate_object(tmp_path: Path):
    # Make the second object a copy of the first
    device = DEVICE_193.replace('TYPE="3" INSTANCE="12"', 'TYPE="0" INSTANCE="2538"')

    with pytest.raises(
        BmsXmlError, match="type 0 instance 2538 appears more than once"
    ):
        parse_bms_xml(write_xml(tmp_path, device))


def test_parse_bms_xml_duplicate_device(tmp_path: Path):
    with pytest.raises(BmsXmlError, match="Device 193 appears more than once"):
        parse_bms_xml(write_xml(tmp_path, DEVICE_193, DEVICE_193))


def test_parse_bms_xml_invalid_xml(tmp_path: Path):
    path = tmp_path / "bms.xml"
    path.write_text("<BACNET><DEVICE>")

    with pytest.raises(BmsXmlError, match="is not valid XML"):
        parse_bms_xml(path)


def test_write_ip_mapping_is_read_by_fastcs_bacnet(tmp_path: Path):
    devices = parse_bms_xml(write_xml(tmp_path, DEVICE_193, DEVICE_194))
    path = tmp_path / "out" / "device_ip_mapping.csv"

    write_ip_mapping(devices, path)

    assert parse_ip_mapping_file(str(path)) == {
        193: IPv4SocketAddress("192.168.4.128", BACNET_PORT, 193),
        194: IPv4SocketAddress("192.168.4.129", BACNET_PORT, 194),
    }


def test_write_ede_layout(tmp_path: Path):
    devices = parse_bms_xml(write_xml(tmp_path, DEVICE_193))
    path = tmp_path / "EDE.xlsx"

    write_ede(devices, path, "Title", datetime.date(2026, 11, 20))

    sheet = openpyxl.load_workbook(path)[EDE_SHEET_NAME]
    rows = list(sheet.iter_rows(values_only=True))
    assert rows[0][0] == "Title"
    assert rows[4][:2] == ("# TIMESTAMP_OF_LAST_CHANGE", "20.11.2026")
    assert rows[EDE_HEADING_ROW - 1][:2] == ("# keyname", "device-obj-instance")
    assert "IP" not in rows[EDE_HEADING_ROW - 1]
    assert rows[EDE_HEADING_ROW:] == [
        # fmt: off
        (
            "IO_DspTCdsOut",
            193,
            "IO_DspTCdsOut",
            0,
            2538,
            "Dsp.TCdsOut",
            None,
            None,
            None,
            None,
            None,
            None,
            62,
            None,
            None,
            None,
            62,
        ),
        (
            "IO_PumpRun",
            193,
            "IO_PumpRun",
            3,
            12,
            "Pump.Run",
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            "Stopped",
            "Running",
            None,
        ),
        # fmt: on
    ]


def test_generated_files_are_read_by_fastcs_bacnet(tmp_path: Path):
    """The generated EDE and IP mapping files load with the test bms.ini"""
    xml = write_xml(tmp_path, DEVICE_193)
    ede = tmp_path / "EDE.xlsx"
    ip_mapping = tmp_path / "device_ip_mapping.csv"

    main([str(xml), "--ede", str(ede), "--ip-mapping", str(ip_mapping)])

    entries = parse_ede(
        str(ede),
        BMS_CONFIG_DIR,
        parse_ip_mapping_file(str(ip_mapping)),
    )
    assert [
        (e.subscription_id.object_id.to_tuple(), e.object_description, e.pv_name)
        for e in entries
    ] == [
        (("analog-input", 2538), "Dsp.TCdsOut", "SV-BM-CH1-01:IODSPTCDSOUT"),
        (("binary-input", 12), "Pump.Run", "SV-BM-CH1-01:IOPUMPRUN"),
    ]
    assert all(
        e.subscription_id.socket_address.ip_address == "192.168.4.128" for e in entries
    )


@pytest.mark.parametrize(
    "args, error",
    [
        ([], "at least one of --ede and --ip-mapping is required"),
        (["--ede", "EDE.xls"], "--ede must be a .xlsx file"),
        (["--ip-mapping", "ip.csv"], "No such file or directory"),
    ],
)
def test_main_errors(tmp_path: Path, capsys, args: list[str], error: str):
    with pytest.raises(SystemExit):
        main([str(tmp_path / "missing.xml"), *args])

    assert error in capsys.readouterr().err
