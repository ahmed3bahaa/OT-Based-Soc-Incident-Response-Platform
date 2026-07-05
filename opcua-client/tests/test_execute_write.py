from copy import deepcopy
from typing import Any

import pytest
from asyncua import ua
from asyncua.crypto.security_policies import (
    SecurityPolicyBasic256Sha256,
)

from src import opcua_scenario_client as scenario_client


class FakeNode:
    def __init__(
        self,
        *,
        old_value: Any,
        variant_type: ua.VariantType,
        verified_value: Any,
        write_error: Exception | None = None,
    ) -> None:
        self.old_value = old_value
        self.variant_type = variant_type
        self.verified_value = verified_value
        self.write_error = write_error

        self.written_attribute = None
        self.written_data_value = None

    async def read_data_value(self) -> ua.DataValue:
        return ua.DataValue(
            ua.Variant(
                self.old_value,
                self.variant_type,
            )
        )

    async def write_attribute(
        self,
        attribute,
        data_value,
    ) -> None:
        self.written_attribute = attribute
        self.written_data_value = data_value

        if self.write_error is not None:
            raise self.write_error

    async def read_value(self) -> Any:
        return self.verified_value


class FakeClient:
    def __init__(self, node: FakeNode) -> None:
        self.node = node
        self.application_uri = None
        self.requested_node_id = None
        self.security_configuration = None
        self.entered = False
        self.exited = False

    async def set_security(
        self,
        policy,
        *,
        certificate,
        private_key,
        mode,
    ) -> None:
        self.security_configuration = {
            "policy": policy,
            "certificate": certificate,
            "private_key": private_key,
            "mode": mode,
        }

    async def __aenter__(self):
        self.entered = True
        return self

    async def __aexit__(
        self,
        exception_type,
        exception,
        traceback,
    ) -> bool:
        self.exited = True
        return False

    def get_node(self, node_id: str) -> FakeNode:
        self.requested_node_id = node_id
        return self.node


def install_fake_client(
    monkeypatch,
    fake_client: FakeClient,
    captured_events: list[dict[str, Any]],
) -> dict[str, Any]:
    constructor_arguments: dict[str, Any] = {}

    def client_factory(*, url: str, timeout: int) -> FakeClient:
        constructor_arguments["url"] = url
        constructor_arguments["timeout"] = timeout
        return fake_client

    def capture_event(event: dict[str, Any]) -> None:
        captured_events.append(deepcopy(event))

    monkeypatch.setattr(
        scenario_client,
        "Client",
        client_factory,
    )
    monkeypatch.setattr(
        scenario_client,
        "append_json_event",
        capture_event,
    )

    return constructor_arguments


@pytest.mark.asyncio
async def test_execute_write_success(
    monkeypatch,
) -> None:
    node_id = (
        "ns=2;s=watersim.TankPLC.MAIN."
        "ARTIRMA_VERI.SU_SEVIYESI"
    )

    node = FakeNode(
        old_value=14.0,
        variant_type=ua.VariantType.Float,
        verified_value=15.0,
    )
    client = FakeClient(node)
    events: list[dict[str, Any]] = []

    constructor_arguments = install_fake_client(
        monkeypatch,
        client,
        events,
    )

    result = await scenario_client.execute_write(
        node_id=node_id,
        requested_value="15.0",
        scenario_id="unit-success-001",
    )

    assert result == 0
    assert constructor_arguments == {
        "url": scenario_client.ENDPOINT,
        "timeout": 10,
    }

    assert client.application_uri == scenario_client.APPLICATION_URI
    assert client.entered is True
    assert client.exited is True
    assert client.requested_node_id == node_id

    security = client.security_configuration

    assert security is not None
    assert security["policy"] is SecurityPolicyBasic256Sha256
    assert security["certificate"] == str(
        scenario_client.CERTIFICATE
    )
    assert security["private_key"] == str(
        scenario_client.PRIVATE_KEY
    )
    assert security["mode"] == (
        ua.MessageSecurityMode.SignAndEncrypt
    )

    assert node.written_attribute == ua.AttributeIds.Value
    assert node.written_data_value is not None
    assert node.written_data_value.Value.Value == 15.0
    assert (
        node.written_data_value.Value.VariantType
        == ua.VariantType.Float
    )

    assert len(events) == 1

    event = events[0]

    assert event["event"]["action"] == "opcua_write"
    assert event["event"]["outcome"] == "success"
    assert event["ot"]["tag"] == "SU_SEVIYESI"
    assert event["ot"]["scenario_id"] == "unit-success-001"
    assert event["ot"]["data_type"] == "Float"
    assert event["ot"]["old_value"] == 14.0
    assert event["ot"]["new_value"] == 15.0
    assert event["ot"]["verified_value"] == 15.0
    assert event["ot"]["verified"] is True
    assert "error" not in event


@pytest.mark.asyncio
async def test_execute_write_verification_mismatch(
    monkeypatch,
) -> None:
    node = FakeNode(
        old_value=14.0,
        variant_type=ua.VariantType.Float,
        verified_value=14.0,
    )
    client = FakeClient(node)
    events: list[dict[str, Any]] = []

    install_fake_client(
        monkeypatch,
        client,
        events,
    )

    result = await scenario_client.execute_write(
        node_id=(
            "ns=2;s=watersim.TankPLC.MAIN."
            "ARTIRMA_VERI.SU_SEVIYESI"
        ),
        requested_value="15.0",
        scenario_id="unit-mismatch-001",
    )

    assert result == 1
    assert len(events) == 1

    event = events[0]

    assert event["event"]["outcome"] == "failure"
    assert event["ot"]["old_value"] == 14.0
    assert event["ot"]["new_value"] == 15.0
    assert event["ot"]["verified_value"] == 14.0
    assert event["ot"]["verified"] is False
    assert "error" not in event


@pytest.mark.asyncio
async def test_execute_write_logs_write_exception(
    monkeypatch,
) -> None:
    node = FakeNode(
        old_value=14.0,
        variant_type=ua.VariantType.Float,
        verified_value=14.0,
        write_error=RuntimeError("KEPServer rejected the write"),
    )
    client = FakeClient(node)
    events: list[dict[str, Any]] = []

    install_fake_client(
        monkeypatch,
        client,
        events,
    )

    result = await scenario_client.execute_write(
        node_id=(
            "ns=2;s=watersim.TankPLC.MAIN."
            "ARTIRMA_VERI.VALF"
        ),
        requested_value="1.0",
        scenario_id="unit-write-failure-001",
    )

    assert result == 1
    assert len(events) == 1

    event = events[0]

    assert event["event"]["outcome"] == "failure"
    assert event["ot"]["tag"] == "VALF"
    assert event["error"] == {
        "type": "RuntimeError",
        "message": "KEPServer rejected the write",
    }


@pytest.mark.asyncio
async def test_execute_write_logs_conversion_failure(
    monkeypatch,
) -> None:
    node = FakeNode(
        old_value=14.0,
        variant_type=ua.VariantType.Float,
        verified_value=14.0,
    )
    client = FakeClient(node)
    events: list[dict[str, Any]] = []

    install_fake_client(
        monkeypatch,
        client,
        events,
    )

    result = await scenario_client.execute_write(
        node_id=(
            "ns=2;s=watersim.TankPLC.MAIN."
            "ARTIRMA_VERI.DEBI"
        ),
        requested_value="not-a-number",
        scenario_id="unit-conversion-failure-001",
    )

    assert result == 1
    assert len(events) == 1

    event = events[0]

    assert event["event"]["outcome"] == "failure"
    assert event["ot"]["tag"] == "DEBI"
    assert event["error"]["type"] == "ValueError"
    assert "could not convert string to float" in (
        event["error"]["message"]
    )
    assert node.written_data_value is None
