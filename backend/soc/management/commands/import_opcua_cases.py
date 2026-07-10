from __future__ import annotations

import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from soc.catalog import seed_catalogs
from soc.importers import import_cases_payload


class Command(BaseCommand):
    help = "Import correlated OPC UA case JSON into the backend database."

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--file",
            required=True,
            type=Path,
            help="Path to a JSON file containing one case object or a list of cases.",
        )

    def handle(self, *args, **options) -> None:
        path = Path(options["file"])

        if not path.exists():
            raise CommandError(f"Case JSON file not found: {path}")

        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            raise CommandError(f"Invalid JSON in {path}: {error}") from error

        seed_counts = seed_catalogs()
        result = import_cases_payload(payload)

        self.stdout.write(
            self.style.SUCCESS(
                "Catalog seed complete: "
                f"rules created={seed_counts['rules_created']}, "
                f"rules updated={seed_counts['rules_updated']}, "
                f"tags created={seed_counts['tags_created']}, "
                f"tags updated={seed_counts['tags_updated']}, "
                f"assets created={seed_counts['assets_created']}, "
                f"assets updated={seed_counts['assets_updated']}"
            )
        )
        self.stdout.write(
            self.style.SUCCESS(
                "OPC UA case import complete: "
                f"cases created={result.cases_created}, "
                f"cases skipped={result.cases_skipped}, "
                f"evidence created={result.evidence_created}, "
                f"evidence skipped={result.evidence_skipped}"
            )
        )
