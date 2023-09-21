"""Custom management command to rebuild all MPTT models.

- This is crucial after importing any fixtures, etc
"""

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """Rebuild all database models which leverage the MPTT structure."""

    def handle(self, *args, **kwargs):
        """Rebuild all database models which leverage the MPTT structure."""
        # Part model
        try:
            print("Rebuilding Part objects")

            from part.models import Part
            Part.objects.rebuild()
        except Exception:
            print("Error rebuilding Part objects")

        # Part category
        try:
            print("Rebuilding PartCategory objects")

            from part.models import PartCategory
            PartCategory.objects.rebuild()
        except Exception:
            print("Error rebuilding PartCategory objects")

        # StockItem model
        try:
            print("Rebuilding StockItem objects")

            from stock.models import StockItem
            StockItem.objects.rebuild()
        except Exception:
            print("Error rebuilding StockItem objects")

        # StockLocation model
        try:
            print("Rebuilding StockLocation objects")

            from stock.models import StockLocation
            StockLocation.objects.rebuild()
        except Exception:
            print("Error rebuilding StockLocation objects")

        # Build model
        try:
            print("Rebuilding Build objects")

            from build.models import Build
            Build.objects.rebuild()
        except Exception:
            print("Error rebuilding Build objects")
