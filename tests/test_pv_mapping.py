from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas
import pytest

from fastcs_bacnet.__main__ import main
from fastcs_bacnet.core.BAC0.subscription_id import (
    IPv4SocketAddress,
    ObjectIdentifier,
    SubscriptionID,
)
from fastcs_bacnet.core.pv_mapping import (
    MAPPING_COLUMNS,
    MAPPING_SHEET_NAME,
    PvMappingEntry,
    pv_names_dict,
    write_pv_mapping,
)
from tests.test_ede_parser import BMS_CONFIG_DIR, EDE_FILE, EDE_HEADER_ROWS

IP_MAPPING_FILE = EDE_FILE.parent / "device_ip_mapping.csv"

# The rows the example EDE file should produce, in sorted order
EXAMPLE_ROWS = [
    [2098177, "", 0, 6, "DH'GF'Giz'AI6", "", "SV-BM-EHAHU-10:GF:GIZ:AI6"],
    [2098177, "", 1, 4, "DH'GF'Giz'AO4", "", "SV-BM-EHAHU-10:GF:GIZ:AO4"],
    [2098177, "", 4, 3, "DH'GF'Giz'BO3", "", "SV-BM-EHAHU-10:GF:GIZ:BO3"],
]


def make_entry(
    device: int, object_type: int, instance: int, description: str = ""
) -> PvMappingEntry:
    type_names = {0: "analog-input", 3: "binary-input"}
    return PvMappingEntry(
        subscription_id=SubscriptionID(
            IPv4SocketAddress("10.0.0.1", 47808, device),
            ObjectIdentifier(type_names[object_type], instance),
        ),
        object_type=object_type,
        object_name=f"OBJ{device}_{object_type}_{instance}",
        object_description=description,
        pv_name=f"PV:{device}:{object_type}:{instance}",
    )


def read_mapping(path: Path) -> pandas.DataFrame:
    """Read a mapping file back, keeping empty cells as empty strings"""
    if path.suffix == ".csv":
        return pandas.read_csv(path, keep_default_na=False)
    return pandas.read_excel(path, sheet_name=MAPPING_SHEET_NAME, keep_default_na=False)


def run_main(*extra_args: str) -> None:
    main(
        [
            "-r",
            str(EDE_HEADER_ROWS),
            str(EDE_FILE),
            BMS_CONFIG_DIR,
            str(IP_MAPPING_FILE),
            *extra_args,
        ]
    )


@pytest.mark.parametrize("suffix", [".csv", ".xlsx"])
def test_write_pv_mapping_sorts_rows(tmp_path: Path, suffix: str):
    path = tmp_path / "nested" / f"mapping{suffix}"
    entries = [
        make_entry(20, 0, 1),
        make_entry(3, 3, 7, "Pump, running"),
        make_entry(3, 0, 9),
        make_entry(3, 0, 10),
    ]

    write_pv_mapping(entries, path)

    data = read_mapping(path)
    assert list(data.columns) == MAPPING_COLUMNS
    assert data.values.tolist() == [
        [3, "", 0, 9, "OBJ3_0_9", "", "PV:3:0:9"],
        [3, "", 0, 10, "OBJ3_0_10", "", "PV:3:0:10"],
        [3, "", 3, 7, "OBJ3_3_7", "Pump, running", "PV:3:3:7"],
        [20, "", 0, 1, "OBJ20_0_1", "", "PV:20:0:1"],
    ]
    # Only the final file is left behind
    assert list(path.parent.iterdir()) == [path]


def test_write_pv_mapping_replaces_existing_file(tmp_path: Path):
    path = tmp_path / "mapping.csv"
    write_pv_mapping([make_entry(1, 0, 1), make_entry(1, 0, 2)], path)

    write_pv_mapping([make_entry(2, 0, 1)], path)

    assert read_mapping(path)["EPICS name"].tolist() == ["PV:2:0:1"]


def test_write_pv_mapping_rejects_unknown_suffix(tmp_path: Path):
    with pytest.raises(ValueError, match="must have one of the suffixes"):
        write_pv_mapping([make_entry(1, 0, 1)], tmp_path / "mapping.txt")


def test_pv_names_dict():
    entry = make_entry(1, 0, 1)

    assert pv_names_dict([entry]) == {entry.subscription_id: entry.pv_name}


@pytest.mark.parametrize("suffix", [".csv", ".xlsx"])
def test_cli_export_only(tmp_path: Path, suffix: str):
    path = tmp_path / f"mapping{suffix}"

    with patch("fastcs_bacnet.__main__.fastcs_bacnet", new_callable=MagicMock) as ioc:
        run_main("--pv-mapping-out", str(path), "--export-only")

    ioc.assert_not_called()
    assert read_mapping(path).values.tolist() == EXAMPLE_ROWS


def test_cli_writes_mapping_then_starts_ioc(tmp_path: Path):
    path = tmp_path / "mapping.csv"

    # A plain MagicMock, as an AsyncMock would create a coroutine nothing awaits
    with (
        patch("fastcs_bacnet.__main__.fastcs_bacnet", new_callable=MagicMock) as ioc,
        patch("fastcs_bacnet.__main__.asyncio.run"),
    ):
        run_main("--pv-mapping-out", str(path))

    assert read_mapping(path).values.tolist() == EXAMPLE_ROWS
    (pv_names,), _ = ioc.call_args
    assert sorted(pv_names.values()) == [row[-1] for row in EXAMPLE_ROWS]


@pytest.mark.parametrize(
    "extra_args, error",
    [
        (["--export-only"], "--export-only requires --pv-mapping-out"),
        (["--pv-mapping-out", "mapping.txt"], "must have one of the suffixes"),
    ],
)
def test_cli_mapping_argument_errors(capsys, extra_args: list[str], error: str):
    with (
        patch("fastcs_bacnet.__main__.parse_ede") as parse_ede,
        pytest.raises(SystemExit),
    ):
        run_main(*extra_args)

    parse_ede.assert_not_called()
    assert error in capsys.readouterr().err
