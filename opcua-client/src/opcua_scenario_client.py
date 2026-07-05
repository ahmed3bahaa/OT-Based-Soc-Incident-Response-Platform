import argparse
import asyncio
import json
import math
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from asyncua import Client, ua
from asyncua.crypto.security_policies import SecurityPolicyBasic256Sha256
from dotenv import load_dotenv

PROJECT_DIR = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_DIR / ".env")


def resolve_project_path(value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return PROJECT_DIR / path


ENDPOINT = os.getenv("OPCUA_ENDPOINT", "opc.tcp://Ahmed:49320")
APPLICATION_URI = os.getenv(
    "OPCUA_APPLICATION_URI",
    "urn:Ubuntu:ICSIncidentResponse:OPCUAScenarioClient",
)

CERTIFICATE = resolve_project_path(
    os.getenv("OPCUA_CERT", "certs/ot-scenario-client-cert.der")
)
PRIVATE_KEY = resolve_project_path(
    os.getenv("OPCUA_PRIVATE_KEY", "certs/ot-scenario-client-key.pem")
)
LOG_FILE = resolve_project_path(
    os.getenv("OPCUA_LOG_FILE", "logs/opcua_operations.jsonl")
)

SOURCE_IP = os.getenv("OPCUA_SOURCE_IP", "192.168.56.10")
SERVER_IP = os.getenv("OPCUA_SERVER_IP", "192.168.56.1")
SERVER_PORT = int(os.getenv("OPCUA_SERVER_PORT", "49320"))


INTEGER_TYPES = {
    ua.VariantType.SByte,
    ua.VariantType.Byte,
    ua.VariantType.Int16,
    ua.VariantType.UInt16,
    ua.VariantType.Int32,
    ua.VariantType.UInt32,
    ua.VariantType.Int64,
    ua.VariantType.UInt64,
}

FLOAT_TYPES = {
    ua.VariantType.Float,
    ua.VariantType.Double,
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


def convert_value(raw_value: str, variant_type: ua.VariantType) -> Any:
    if variant_type == ua.VariantType.Boolean:
        normalized = raw_value.strip().lower()

        if normalized in {"true", "1", "yes", "on"}:
            return True

        if normalized in {"false", "0", "no", "off"}:
            return False

        raise ValueError(f"Invalid Boolean value: {raw_value}")

    if variant_type in INTEGER_TYPES:
        return int(raw_value)

    if variant_type in FLOAT_TYPES:
        return float(raw_value)

    if variant_type == ua.VariantType.String:
        return raw_value

    raise ValueError(
        f"Unsupported OPC UA type for this MVP: {variant_type.name}"
    )


def values_match(expected: Any, actual: Any) -> bool:
    if isinstance(expected, float) and isinstance(actual, (float, int)):
        return math.isclose(expected, float(actual), rel_tol=1e-6, abs_tol=1e-6)

    return expected == actual


def append_json_event(event: dict[str, Any]) -> None:
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

    with LOG_FILE.open("a", encoding="utf-8") as file:
        file.write(
            json.dumps(
                event,
                ensure_ascii=False,
                separators=(",", ":"),
            )
            + "\n"
        )


async def execute_write(
    node_id: str,
    requested_value: str,
    scenario_id: str,
) -> int:
    event: dict[str, Any] = {
        "@timestamp": utc_now(),
        "event": {
            "kind": "event",
            "category": ["process"],
            "type": ["change"],
            "action": "opcua_write",
            "outcome": "unknown",
        },
        "source": {
            "ip": SOURCE_IP,
        },
        "destination": {
            "ip": SERVER_IP,
            "port": SERVER_PORT,
        },
        "network": {
            "transport": "tcp",
            "protocol": "opcua",
        },
        "client": {
            "name": "ot-scenario-client",
            "application_uri": APPLICATION_URI,
        },
        "ot": {
            "protocol": "opcua",
            "operation": "write",
            "node_id": node_id,
            "tag": node_id.split(".")[-1],
            "scenario_id": scenario_id,
        },
    }

    client = Client(url=ENDPOINT, timeout=10)
    client.application_uri = APPLICATION_URI

    try:
        await client.set_security(
            SecurityPolicyBasic256Sha256,
            certificate=str(CERTIFICATE),
            private_key=str(PRIVATE_KEY),
            mode=ua.MessageSecurityMode.SignAndEncrypt,
        )

        async with client:
            node = client.get_node(node_id)

            # Read before writing: this becomes old_value.
            old_data_value = await node.read_data_value()

            if old_data_value.Value is None:
                raise RuntimeError("The OPC UA node returned no value.")

            old_value = old_data_value.Value.Value
            variant_type = old_data_value.Value.VariantType

            new_value = convert_value(requested_value, variant_type)

            # Send only the Value field.
            # KEPServer rejects writes containing client-provided timestamps/status.
            write_data_value = ua.DataValue(
                ua.Variant(new_value, variant_type)
            )

            await node.write_attribute(
                ua.AttributeIds.Value,
                write_data_value,
            )

            # Read after writing to verify the operation.
            verified_value = await node.read_value()
            verified = values_match(new_value, verified_value)

            event["@timestamp"] = utc_now()
            event["event"]["outcome"] = "success" if verified else "failure"

            event["ot"].update(
                {
                    "data_type": variant_type.name,
                    "old_value": json_safe(old_value),
                    "new_value": json_safe(new_value),
                    "verified_value": json_safe(verified_value),
                    "verified": verified,
                }
            )

    except Exception as error:
        event["@timestamp"] = utc_now()
        event["event"]["outcome"] = "failure"
        event["error"] = {
            "type": type(error).__name__,
            "message": str(error),
        }

        append_json_event(event)
        print(json.dumps(event, indent=2, ensure_ascii=False))
        return 1

    append_json_event(event)
    print(json.dumps(event, indent=2, ensure_ascii=False))
    return 0 if event["event"]["outcome"] == "success" else 1


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Perform and log one secure OPC UA write."
    )

    parser.add_argument(
        "--node-id",
        required=True,
        help="Full OPC UA NodeId.",
    )
    parser.add_argument(
        "--value",
        required=True,
        help="New value to write.",
    )
    parser.add_argument(
        "--scenario-id",
        default="manual-test",
        help="Scenario identifier.",
    )

    return parser.parse_args()


async def main() -> int:
    args = parse_arguments()

    return await execute_write(
        node_id=args.node_id,
        requested_value=args.value,
        scenario_id=args.scenario_id,
    )


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
