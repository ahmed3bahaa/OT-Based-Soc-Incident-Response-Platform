from __future__ import annotations

import base64
import json
import os
import ssl
import time
import urllib.error
import urllib.request
from typing import Any
from urllib.parse import urlparse

from django.core.management.base import BaseCommand, CommandError

from soc.live_ingest import WATCH_RULES, ingest_live_alerts


def default_search_body(size: int) -> dict[str, Any]:
    return {
        "size": size,
        "sort": [{"@timestamp": {"order": "asc"}}],
        "query": {
            "bool": {
                "filter": [
                    {
                        "terms": {
                            "rule.id": sorted(WATCH_RULES),
                        }
                    }
                ]
            }
        },
    }


def decode_response(raw: bytes) -> Any:
    if not raw:
        return {}
    return json.loads(raw.decode("utf-8", errors="replace"))


class Command(BaseCommand):
    help = "Poll a Wazuh/Indexer alerts API and ingest/correlate matching OT alerts."

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--url",
            default=os.getenv("WAZUH_ALERTS_URL") or os.getenv("WAZUH_INDEXER_ALERTS_URL"),
            help=(
                "Alerts API URL. For Wazuh Indexer/OpenSearch this is usually "
                "https://HOST:9200/wazuh-alerts-*/_search."
            ),
        )
        parser.add_argument(
            "--method",
            choices=("GET", "POST"),
            default=os.getenv("WAZUH_ALERTS_METHOD", "POST"),
        )
        parser.add_argument("--username", default=os.getenv("WAZUH_API_USERNAME"))
        parser.add_argument("--password", default=os.getenv("WAZUH_API_PASSWORD"))
        parser.add_argument("--token", default=os.getenv("WAZUH_API_TOKEN"))
        parser.add_argument(
            "--insecure",
            action="store_true",
            default=os.getenv("WAZUH_API_INSECURE", "").lower() in {"1", "true", "yes"},
            help="Disable TLS certificate verification for lab-only endpoints.",
        )
        parser.add_argument(
            "--body",
            default=os.getenv("WAZUH_ALERTS_BODY"),
            help="Optional JSON request body. If omitted for POST, a rule.id query is used.",
        )
        parser.add_argument(
            "--size",
            type=int,
            default=int(os.getenv("WAZUH_ALERTS_SIZE", "100")),
            help="Default OpenSearch result size when --body is omitted.",
        )
        parser.add_argument(
            "--poll-interval",
            type=float,
            default=float(os.getenv("WAZUH_ALERTS_POLL_INTERVAL", "5")),
        )
        parser.add_argument(
            "--window-seconds",
            type=int,
            default=int(os.getenv("OT_SOC_CORRELATION_WINDOW_SECONDS", "900")),
        )
        parser.add_argument("--once", action="store_true")

    def handle(self, *args, **options) -> None:
        url = options["url"]
        if not url:
            raise CommandError(
                "Missing --url. Set WAZUH_ALERTS_URL or pass a Wazuh Indexer "
                "search URL such as https://HOST:9200/wazuh-alerts-*/_search."
            )
        if urlparse(url).scheme not in {"http", "https"}:
            raise CommandError("--url must use http:// or https://")

        method = options["method"]
        poll_interval = float(options["poll_interval"])
        window_seconds = int(options["window_seconds"])
        once = bool(options["once"])
        context = ssl._create_unverified_context() if options["insecure"] else None  # nosec B323

        self.stdout.write(
            self.style.SUCCESS(
                f"Polling {url} with method={method}, window={window_seconds}s"
            )
        )

        while True:
            try:
                payload = self.fetch_payload(url, method, options, context)
            except urllib.error.URLError as error:
                self.stderr.write(f"Wazuh poll failed: {error}")
                if once:
                    raise CommandError(str(error)) from error
                time.sleep(poll_interval)
                continue

            result = ingest_live_alerts(
                payload,
                source="wazuh_api",
                window_seconds=window_seconds,
            )
            self.stdout.write(
                "alerts created={created}, skipped={skipped}; "
                "cases created={cases_created}, skipped={cases_skipped}".format(
                    created=result.alerts_created,
                    skipped=result.alerts_skipped,
                    cases_created=result.cases_created,
                    cases_skipped=result.cases_skipped,
                )
            )

            if once:
                return

            time.sleep(poll_interval)

    def fetch_payload(
        self,
        url: str,
        method: str,
        options: dict[str, Any],
        context: ssl.SSLContext | None,
    ) -> Any:
        headers = {
            "Accept": "application/json",
        }
        body: bytes | None = None

        if method == "POST":
            headers["Content-Type"] = "application/json"
            if options["body"]:
                body = str(options["body"]).encode("utf-8")
            else:
                body = json.dumps(default_search_body(int(options["size"]))).encode("utf-8")

        if options["token"]:
            headers["Authorization"] = f"Bearer {options['token']}"
        elif options["username"] and options["password"]:
            token = base64.b64encode(
                f"{options['username']}:{options['password']}".encode("utf-8")
            ).decode("ascii")
            headers["Authorization"] = f"Basic {token}"

        request = urllib.request.Request(
            url,
            data=body,
            headers=headers,
            method=method,
        )

        with urllib.request.urlopen(request, timeout=30, context=context) as response:  # nosec B310
            return decode_response(response.read())
