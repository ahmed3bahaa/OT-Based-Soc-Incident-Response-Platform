import asyncio
import os
import sys
from pathlib import Path

from asyncua import Client, ua
from asyncua.crypto.security_policies import SecurityPolicyBasic256Sha256
from dotenv import load_dotenv


PROJECT_DIR = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_DIR / ".env")


def project_path(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else PROJECT_DIR / path


ENDPOINT = os.getenv("OPCUA_ENDPOINT", "opc.tcp://Ahmed:49320")
APPLICATION_URI = os.getenv(
    "OPCUA_APPLICATION_URI",
    "urn:Ubuntu:ICSIncidentResponse:OPCUAScenarioClient",
)
CERTIFICATE = project_path(
    os.getenv("OPCUA_CERT", "certs/ot-scenario-client-cert.der")
)
PRIVATE_KEY = project_path(
    os.getenv("OPCUA_PRIVATE_KEY", "certs/ot-scenario-client-key.pem")
)


async def search_node(
    node,
    target: str,
    path: list[str],
    visited: set[str],
    depth: int = 0,
    max_depth: int = 10,
) -> None:
    if depth > max_depth:
        return

    node_id = node.nodeid.to_string()

    if node_id in visited:
        return

    visited.add(node_id)

    try:
        children = await node.get_children()
    except Exception:
        return

    for child in children:
        try:
            browse_name = await child.read_browse_name()
            display_name = await child.read_display_name()

            name = browse_name.Name or display_name.Text or "unknown"
            child_path = path + [name]
            child_node_id = child.nodeid.to_string()

            if target.casefold() in name.casefold():
                print("\nMATCH FOUND")
                print("Path:   " + " / ".join(child_path))
                print("NodeId: " + child_node_id)
                print("Browse namespace index:", browse_name.NamespaceIndex)

            await search_node(
                child,
                target,
                child_path,
                visited,
                depth + 1,
                max_depth,
            )

        except Exception:
            continue


async def main() -> None:
    target = sys.argv[1] if len(sys.argv) > 1 else "SU_SEVIYESI"

    client = Client(url=ENDPOINT, timeout=10)
    client.application_uri = APPLICATION_URI

    await client.set_security(
        SecurityPolicyBasic256Sha256,
        certificate=str(CERTIFICATE),
        private_key=str(PRIVATE_KEY),
        mode=ua.MessageSecurityMode.SignAndEncrypt,
    )

    async with client:
        print("Connected to:", ENDPOINT)

        namespaces = await client.get_namespace_array()

        print("\nServer namespace array:")
        for index, namespace_uri in enumerate(namespaces):
            print(f"  [{index}] {namespace_uri}")

        print(f"\nSearching for: {target}")

        await search_node(
            client.nodes.objects,
            target,
            ["Objects"],
            set(),
        )


if __name__ == "__main__":
    asyncio.run(main())
