from django.core.management.base import BaseCommand, CommandError

from market.services.bantay_presyo import sync_bantay_presyo_market_prices


class Command(BaseCommand):
    help = "Import Region V market prices from Bantay Presyo using Legazpi City Public Market and Naga People's Mall."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Fetch and display the resolved prices without writing MarketPrice records.",
        )

    def handle(self, *args, **options):
        if options["dry_run"]:
            raise CommandError("Dry-run mode is no longer supported in the automated sync command.")

        result = sync_bantay_presyo_market_prices(force=True)
        if result.get("status") != "success":
            raise CommandError(result.get("error") or result.get("reason") or "Unknown Bantay Presyo sync failure.")

        for message in result.get("skipped", []):
            self.stdout.write(self.style.WARNING(f"Skipped {message}"))
        self.stdout.write(
            self.style.SUCCESS(
                f"Import completed. Created: {result.get('created', 0)}, "
                f"Updated: {result.get('updated', 0)}, "
                f"Skipped: {len(result.get('skipped', []))}"
            )
        )
