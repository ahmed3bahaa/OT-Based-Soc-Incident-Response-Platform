from django.core.management.base import BaseCommand

from soc.catalog import seed_catalogs


class Command(BaseCommand):
    help = "Seed MVP OT rule, tag, and asset catalogs."

    def handle(self, *args, **options) -> None:
        counts = seed_catalogs()

        self.stdout.write(
            self.style.SUCCESS(
                "Catalog seed complete: "
                f"rules created={counts['rules_created']}, "
                f"rules updated={counts['rules_updated']}, "
                f"tags created={counts['tags_created']}, "
                f"tags updated={counts['tags_updated']}, "
                f"assets created={counts['assets_created']}, "
                f"assets updated={counts['assets_updated']}"
            )
        )
