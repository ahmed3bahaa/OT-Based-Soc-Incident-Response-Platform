import asyncio
import socket
from pathlib import Path

from asyncua.crypto.cert_gen import setup_self_signed_certificate
from cryptography.x509.oid import ExtendedKeyUsageOID

PROJECT_DIR = Path(__file__).resolve().parents[1]
CERT_DIR = PROJECT_DIR / "certs"

PRIVATE_KEY = CERT_DIR / "ot-scenario-client-key.pem"
CERTIFICATE = CERT_DIR / "ot-scenario-client-cert.der"

APPLICATION_URI = "urn:Ubuntu:ICSIncidentResponse:OPCUAScenarioClient"


async def main() -> None:
    CERT_DIR.mkdir(parents=True, exist_ok=True)

    await setup_self_signed_certificate(
        PRIVATE_KEY,
        CERTIFICATE,
        APPLICATION_URI,
        socket.gethostname(),
        [ExtendedKeyUsageOID.CLIENT_AUTH],
        {
            "countryName": "TR",
            "organizationName": "OT Lab",
            "localityName": "Sakarya",
        },
    )

    print(f"Certificate: {CERTIFICATE}")
    print(f"Private key: {PRIVATE_KEY}")
    print(f"Application URI: {APPLICATION_URI}")


if __name__ == "__main__":
    asyncio.run(main())
