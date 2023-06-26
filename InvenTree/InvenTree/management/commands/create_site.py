"""Custom management command to create a Site."""

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """Create a Site for tests."""

    def handle(self, *args, **kwargs):
        """Create a Site for tests."""
        # Part model
        try:
            print("Creating Site")

            from django.contrib.sites.models import Site

            Site.objects.create(
                name="Test Site",
                domain="127.0.0.1",
            )
        except Exception as _e:
            print("Error creating Site", _e)
