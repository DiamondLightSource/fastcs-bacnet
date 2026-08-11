# Tests for the FastCS side of the application
from collections import defaultdict
from collections.abc import Callable
from unittest.mock import MagicMock

import pytest
from fastcs.datatypes import Bool, Float

from fastcs_bacnet.core.BAC0.bacnet_client import BacnetClient
from fastcs_bacnet.core.BAC0.subscription_id import (
    IPv4SocketAddress,
    ObjectIdentifier,
    PVNode,
    SubscriptionID,
    sort_dict,
)
from fastcs_bacnet.core.FastCS.bacnet_attributes import (
    AnalogAttributeIORef,
    BinaryAttributeIORef,
)
from fastcs_bacnet.core.FastCS.bacnet_subcontroller import (
    BacnetSubController,
    InvalidObjectTypeError,
)


@pytest.fixture
def mock_bacnet_controller() -> BacnetSubController:
    mock_client = MagicMock(BacnetClient)
    mock_node = MagicMock(PVNode)
    mock_node.suffix = MagicMock()
    mock_node.children = MagicMock()
    return BacnetSubController(mock_client, mock_node)


@pytest.fixture
def subs_id_factory() -> Callable[[], SubscriptionID]:
    """Fixture to create a generic SubscriptionID with incrementing object instance
    number, suitable for use in the structures we manipulate"""
    ip = "127.0.0.1"
    port = 47808
    device_id = (
        1234  # TODO: Technically all the created subsids will have same number...
    )

    sub_id_counter = 0

    def _subs_id_factory(object_type="test-type"):
        nonlocal sub_id_counter
        sub_id_counter += 1
        return SubscriptionID(
            IPv4SocketAddress(ip, port, device_id),
            ObjectIdentifier(object_type, sub_id_counter),
        )

    return _subs_id_factory


def test_sort_dict_creates_expected_structure(subs_id_factory):
    """Test that the sort_dict function sorts data as expected"""

    sub_1 = subs_id_factory()
    sub_2 = subs_id_factory()
    sub_3 = subs_id_factory()
    sub_4 = subs_id_factory()
    sub_5 = subs_id_factory()
    sub_6 = subs_id_factory()
    sub_7 = subs_id_factory()

    test_data = {
        sub_1: "ABC:DEF:JKL",
        sub_2: "ABC:DEF:123",
        sub_3: "ABC:DEF:GHI",
        sub_4: "ABC:DEF:GHI:LLL",
        sub_5: "ABC:456",
        sub_6: "ABC:789",
        sub_7: "ZZZ:AAA",
    }

    dict_under_test = sort_dict(test_data)

    # Create expected test data
    expected_dict = defaultdict(PVNode)
    expected_dict["ABC"].children["DEF"].suffix["JKL"] = sub_1
    expected_dict["ABC"].children["DEF"].suffix["123"] = sub_2
    expected_dict["ABC"].children["DEF"].suffix["GHI"] = sub_3
    expected_dict["ABC"].children["DEF"].children["GHI"].suffix["LLL"] = sub_4
    expected_dict["ABC"].suffix["456"] = sub_5
    expected_dict["ABC"].suffix["789"] = sub_6
    expected_dict["ZZZ"].suffix["AAA"] = sub_7

    assert dict_under_test == expected_dict


def test_sort_dict_rejects_duplicate_pvs(subs_id_factory: Callable[[], SubscriptionID]):
    """Test we cannot create duplicate PVs"""
    sub_1 = subs_id_factory()
    sub_2 = subs_id_factory()

    test_data = {sub_1: "ABC:DEF:123", sub_2: "ABC:DEF:123"}

    with pytest.raises(ValueError):
        sort_dict(test_data)


@pytest.mark.parametrize(
    "object_type, attribute_expectation",
    [
        (
            "analog-output",
            (
                Float(),
                AnalogAttributeIORef,
            ),
        ),
        (
            "analog-input",
            (
                Float(),
                AnalogAttributeIORef,
            ),
        ),
        (
            "analog-value",
            (
                Float(),
                AnalogAttributeIORef,
            ),
        ),
        (
            "binary-output",
            (
                Bool(),
                BinaryAttributeIORef,
            ),
        ),
        (
            "binary-input",
            (
                Bool(),
                BinaryAttributeIORef,
            ),
        ),
        (
            "binary-value",
            (
                Bool(),
                BinaryAttributeIORef,
            ),
        ),
    ],
)
def test_bacnet_subcontroller_create_attributes(
    object_type: str,
    attribute_expectation,
    subs_id_factory: Callable[[str], SubscriptionID],
):
    """Test _create_attribute creates expected read-only attributes"""
    mock_client = MagicMock(BacnetClient)
    mock_node = MagicMock(PVNode)
    mock_node.suffix = MagicMock()
    mock_node.children = MagicMock()
    controller = BacnetSubController(mock_client, mock_node)

    subs_id = subs_id_factory(object_type)

    attr = controller._create_attribute(subs_id)

    assert attr.access_mode == "r"
    assert attr.datatype == attribute_expectation[0]
    assert attr.io_ref == attribute_expectation[1](subs_id)


# Test a few types we may someday support (multi-state-*), as well as a handful of other
# definitely unsupported types
@pytest.mark.parametrize(
    "object_type",
    [
        "multi-state-input",
        "multi-state-output",
        "multi-state-value",
        "device",
        "loop",
        "large-analog-value",
        "positive-integer-value",
    ],
)
def test_bacnet_subcontroller_invalid_attributes(
    object_type: str,
    mock_bacnet_controller: BacnetSubController,
    subs_id_factory: Callable[[str], SubscriptionID],
):
    """Test _create_attribute raises exceptions in expected cases"""

    subs_id = subs_id_factory(object_type)

    with pytest.raises(InvalidObjectTypeError):
        mock_bacnet_controller._create_attribute(subs_id)
