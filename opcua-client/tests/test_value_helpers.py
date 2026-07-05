from pathlib import Path

import pytest
from asyncua import ua

from src.opcua_scenario_client import (
    convert_value,
    json_safe,
    values_match,
)


@pytest.mark.parametrize(
    ("raw_value", "expected"),
    [
        ("true", True),
        ("TRUE", True),
        ("1", True),
        ("yes", True),
        ("on", True),
        ("false", False),
        ("FALSE", False),
        ("0", False),
        ("no", False),
        ("off", False),
        ("  true  ", True),
    ],
)
def test_convert_boolean_values(
    raw_value: str,
    expected: bool,
) -> None:
    assert convert_value(raw_value, ua.VariantType.Boolean) is expected


def test_convert_invalid_boolean_raises_value_error() -> None:
    with pytest.raises(
        ValueError,
        match="Invalid Boolean value",
    ):
        convert_value("maybe", ua.VariantType.Boolean)


@pytest.mark.parametrize(
    "variant_type",
    [
        ua.VariantType.SByte,
        ua.VariantType.Byte,
        ua.VariantType.Int16,
        ua.VariantType.UInt16,
        ua.VariantType.Int32,
        ua.VariantType.UInt32,
        ua.VariantType.Int64,
        ua.VariantType.UInt64,
    ],
)
def test_convert_integer_types(
    variant_type: ua.VariantType,
) -> None:
    result = convert_value("42", variant_type)

    assert result == 42
    assert isinstance(result, int)


@pytest.mark.parametrize(
    "variant_type",
    [
        ua.VariantType.Float,
        ua.VariantType.Double,
    ],
)
def test_convert_floating_point_types(
    variant_type: ua.VariantType,
) -> None:
    result = convert_value("12.5", variant_type)

    assert result == 12.5
    assert isinstance(result, float)


def test_convert_string_preserves_original_value() -> None:
    raw_value = "  Pump Station 1  "

    assert (
        convert_value(raw_value, ua.VariantType.String)
        == raw_value
    )


def test_convert_unsupported_type_raises_value_error() -> None:
    with pytest.raises(
        ValueError,
        match="Unsupported OPC UA type",
    ):
        convert_value(
            "2026-07-05T12:00:00Z",
            ua.VariantType.DateTime,
        )


@pytest.mark.parametrize(
    "value",
    [
        None,
        "water",
        10,
        10.5,
        True,
        False,
    ],
)
def test_json_safe_preserves_json_primitives(value: object) -> None:
    assert json_safe(value) == value


def test_json_safe_converts_non_json_value_to_string() -> None:
    value = Path("/tmp/example")

    assert json_safe(value) == "/tmp/example"


@pytest.mark.parametrize(
    ("expected", "actual"),
    [
        ("running", "running"),
        (True, True),
        (15, 15),
        (12.5, 12.5),
        (12.5, 12.5000004),
        (1.0, 1),
    ],
)
def test_values_match_returns_true(
    expected: object,
    actual: object,
) -> None:
    assert values_match(expected, actual) is True


@pytest.mark.parametrize(
    ("expected", "actual"),
    [
        ("running", "stopped"),
        (True, False),
        (15, 16),
        (12.5, 12.51),
    ],
)
def test_values_match_returns_false(
    expected: object,
    actual: object,
) -> None:
    assert values_match(expected, actual) is False
