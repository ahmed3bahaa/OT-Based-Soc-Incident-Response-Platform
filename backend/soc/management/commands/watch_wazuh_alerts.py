from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from django.core.management.base import BaseCommand, CommandError

from soc.live_ingest import ingest_live_alerts


def parse_json_lines(lines: list[bytes]) -> list[dict[str, Any]]:
    alerts: list[dict[str, Any]] = []

    for raw in lines:
        raw = raw.replace(b"\x00", b"").strip()
        if not raw:
            continue
        try:
            item = json.loads(raw.decode("utf-8", errors="replace"))
        except json.JSONDecodeError:
            continue
        if isinstance(item, dict):
            alerts.append(item)

    return alerts


class Command(BaseCommand):
    help = "Tail Wazuh alerts.json and ingest/correlate matching OT alerts in near real time."

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--file",
            type=Path,
            default=Path("/var/ossec/logs/alerts/alerts.json"),
            help="Path to Wazuh alerts.json.",
        )
        parser.add_argument(
            "--poll-interval",
            type=float,
            default=2.0,
            help="Seconds between file checks.",
        )
        parser.add_argument(
            "--window-seconds",
            type=int,
            default=900,
            help="Correlation window for pairing process and network evidence.",
        )
        parser.add_argument(
            "--from-start",
            action="store_true",
            help="Read existing file content before tailing new alerts.",
        )
        parser.add_argument(
            "--wait",
            action="store_true",
            help="Wait for the file to appear instead of failing immediately.",
        )
        parser.add_argument(
            "--once",
            action="store_true",
            help="Read available content once and exit. Useful for tests and backfills.",
        )

    def handle(self, *args, **options) -> None:
        path = Path(options["file"])
        poll_interval = float(options["poll_interval"])
        window_seconds = int(options["window_seconds"])
        read_from_start = bool(options["from_start"])
        wait_for_file = bool(options["wait"])
        once = bool(options["once"])

        if window_seconds < 1:
            raise CommandError("--window-seconds must be greater than zero")

        while not path.exists():
            if not wait_for_file:
                raise CommandError(f"Wazuh alerts file not found: {path}")
            self.stdout.write(f"Waiting for Wazuh alerts file: {path}")
            time.sleep(poll_interval)

        offset = 0 if read_from_start else path.stat().st_size
        self.stdout.write(
            self.style.SUCCESS(
                f"Watching {path} from byte offset {offset} with window={window_seconds}s"
            )
        )

        while True:
            if not path.exists():
                if once:
                    return
                if wait_for_file:
                    time.sleep(poll_interval)
                    continue
                raise CommandError(f"Wazuh alerts file disappeared: {path}")

            size = path.stat().st_size
            if size < offset:
                offset = 0

            with path.open("rb") as file:
                file.seek(offset)
                lines = file.readlines()
                offset = file.tell()

            alerts = parse_json_lines(lines)
            if alerts:
                result = ingest_live_alerts(
                    alerts,
                    source="wazuh_file",
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
