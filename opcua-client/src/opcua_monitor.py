import argparse
import asyncio
import json
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
NODE_PREFIX = os.getenv(
    "OPCUA_NODE_PREFIX",
    "ns=2;s=watersim.TankPLC.MAIN.ARTIRMA_VERI",
)
DEFAULT_SIMULATOR_TAGS = (
    "DEBI",
    "MOTOR1",
    "MOTOR2",
    "SAMANDIRA",
    "SU_SEVIYESI",
    "ScenarioID",
    "VALF",
)

# IMPORTANT:
# For this MVP monitor, we reuse the already trusted scenario-client certificate.
# Later, we can issue a separate monitor certificate/application URI.
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

USERNAME = os.getenv("OPCUA_USERNAME")
PASSWORD = os.getenv("OPCUA_PASSWORD", "")

MONITOR_LOG_FILE = resolve_project_path(
    os.getenv("OPCUA_MONITOR_LOG_FILE", "logs/opcua_monitor.jsonl")
)

OBSERVER_IP = os.getenv("OPCUA_SOURCE_IP", "192.168.56.10")
SERVER_IP = os.getenv("OPCUA_SERVER_IP", "192.168.56.1")
SERVER_PORT = int(os.getenv("OPCUA_SERVER_PORT", "49320"))


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value

    if isinstance(value, Path):
        return value.as_posix()

    if isinstance(value, bytes):
        return value.hex()

    if isinstance(value, datetime):
        return value.isoformat()

    return str(value)


def tag_from_node_id(node_id: str) -> str:
    if "." in node_id:
        return node_id.split(".")[-1]
    if ";" in node_id:
        return node_id.split(";")[-1]
    return node_id


def default_simulator_node_ids() -> list[str]:
    return [f"{NODE_PREFIX}.{tag}" for tag in DEFAULT_SIMULATOR_TAGS]


def env_node_ids() -> list[str]:
    raw = os.getenv("OPCUA_MONITOR_NODE_IDS", "")
    return [node_id.strip() for node_id in raw.split(",") if node_id.strip()]


def append_json_event(event: dict[str, Any]) -> None:
    MONITOR_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

    with MONITOR_LOG_FILE.open("a", encoding="utf-8") as file:
        file.write(
            json.dumps(
                event,
                ensure_ascii=False,
                separators=(",", ":"),
            )
            + "\n"
        )


class DataChangeHandler:
    def __init__(self, scenario_id: str, last_values: dict[str, Any]):
        self.scenario_id = scenario_id
        self.last_values = last_values

    def datachange_notification(self, node, value, data):
        node_id = node.nodeid.to_string()
        new_value = json_safe(value)
        old_value = self.last_values.get(node_id)

        # Suppress initial subscription callback / duplicate value notifications.
        # We only want real observed changes after the monitor starts.
        if old_value == new_value:
            return

        self.last_values[node_id] = new_value

        event = {
            "@timestamp": utc_now(),
            "event": {
                "kind": "event",
                "category": ["process"],
                "type": ["change"],
                "action": "opcua_datachange",
                "outcome": "observed",
            },
            "observer": {
                "name": "ot-opcua-monitor",
                "ip": OBSERVER_IP,
                "role": "opcua_subscription_monitor",
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
                "name": "ot-opcua-monitor",
                "application_uri": APPLICATION_URI,
            },
            "ot": {
                "protocol": "opcua",
                "operation": "datachange",
                "node_id": node_id,
                "tag": tag_from_node_id(node_id),
                "scenario_id": self.scenario_id,
                "old_value": old_value,
                "new_value": new_value,
                "observer": True,
                "change_origin": "unknown_from_subscription",
            },
        }

        append_json_event(event)
        print(json.dumps(event, indent=2, ensure_ascii=False))


async def run_monitor(
    node_ids: list[str],
    scenario_id: str,
    interval_ms: int,
) -> int:
    print(f"[+] Endpoint: {ENDPOINT}")
    print("[+] Security: Basic256Sha256 / SignAndEncrypt")
    print(f"[+] Certificate: {CERTIFICATE}")
    print(f"[+] Private key: {PRIVATE_KEY}")
    print(f"[+] User identity: {'username' if USERNAME else 'anonymous'}")
    print(f"[+] Monitor log: {MONITOR_LOG_FILE}")
    print(f"[+] Scenario ID: {scenario_id}")
    print(f"[+] Node subscriptions: {len(node_ids)}")

    if not CERTIFICATE.exists():
        raise FileNotFoundError(f"Certificate not found: {CERTIFICATE}")

    if not PRIVATE_KEY.exists():
        raise FileNotFoundError(f"Private key not found: {PRIVATE_KEY}")

    client = Client(url=ENDPOINT, timeout=10)
    client.application_uri = APPLICATION_URI
    if USERNAME:
        client.set_user(USERNAME)
        client.set_password(PASSWORD)

    await client.set_security(
        SecurityPolicyBasic256Sha256,
        certificate=str(CERTIFICATE),
        private_key=str(PRIVATE_KEY),
        mode=ua.MessageSecurityMode.SignAndEncrypt,
    )

    last_values: dict[str, Any] = {}

    async with client:
        nodes = [client.get_node(node_id) for node_id in node_ids]

        for node in nodes:
            node_id = node.nodeid.to_string()
            try:
                initial_value = json_safe(await node.read_value())
                last_values[node_id] = initial_value
                print(f"[+] Initial value: {node_id} = {initial_value!r}")
            except Exception as error:
                last_values[node_id] = None
                print(f"[!] Could not read initial value for {node_id}: {error}")

        handler = DataChangeHandler(
            scenario_id=scenario_id,
            last_values=last_values,
        )

        subscription = await client.create_subscription(interval_ms, handler)

        for node in nodes:
            await subscription.subscribe_data_change(node)
            print(f"[+] Subscribed: {node.nodeid.to_string()}")

        print("[+] Monitor is running.")
        print("[+] Now change the tag from UaExpert GUI.")
        print("[+] Press Ctrl+C to stop.")

        while True:
            await asyncio.sleep(1)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Passively monitor OPC UA tag changes and write JSONL events."
    )

    parser.add_argument(
        "--node-id",
        action="append",
        help="Full OPC UA NodeId to monitor. Can be used multiple times.",
    )
    parser.add_argument(
        "--all-simulator-tags",
        action="store_true",
        help="Monitor the known KEPServerEX simulator tags used by the MVP lab.",
    )
    parser.add_argument(
        "--scenario-id",
        default=f"gui-monitor-proof-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}",
        help="Scenario identifier added to monitor events.",
    )
    parser.add_argument(
        "--interval-ms",
        type=int,
        default=500,
        help="OPC UA subscription publishing interval in milliseconds.",
    )

    args = parser.parse_args()

    if not args.node_id and not args.all_simulator_tags and not env_node_ids():
        parser.error(
            "Provide --node-id, set OPCUA_MONITOR_NODE_IDS, "
            "or use --all-simulator-tags."
        )

    return args


async def main() -> int:
    args = parse_arguments()
    node_ids = args.node_id or env_node_ids()
    if args.all_simulator_tags:
        node_ids = [*node_ids, *default_simulator_node_ids()]

    return await run_monitor(
        node_ids=list(dict.fromkeys(node_ids)),
        scenario_id=args.scenario_id,
        interval_ms=args.interval_ms,
    )


if __name__ == "__main__":
    try:
        raise SystemExit(asyncio.run(main()))
    except KeyboardInterrupt:
        print("\n[+] Monitor stopped by user.")
        raise SystemExit(0) from None
