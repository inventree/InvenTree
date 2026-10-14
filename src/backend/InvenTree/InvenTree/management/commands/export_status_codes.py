"""Custom management command to export all status codes.

This is used to generate a JSON file which contains all of the 'StatusCode'
classes available in InvenTree, so that they can be introspected by the
InvenTree documentation system. This allows status code tables to be
documented without having to manually duplicate the information (which
otherwise silently drifts out of sync with the source code).
"""

import json

from django.core.management.base import BaseCommand

from generic.states import StatusCode
from InvenTree.helpers import inheritors

from .export_report_context import parse_docstring


class Command(BaseCommand):
    """Extract status code information, and export to a JSON file."""

    def add_arguments(self, parser):
        """Add custom arguments for this command."""
        parser.add_argument(
            'filename', type=str, help='Output filename for status code definitions'
        )

    def handle(self, *args, **kwargs):
        """Export status code information to a JSON file."""
        status_codes = discover_status_codes()

        filename = kwargs.get('filename', 'inventree_status_codes.json')

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(status_codes, f, indent=4)

        print(f"Exported InvenTree status code definitions to '{filename}'")


def discover_status_codes():
    """Discover all available status code classes.

    Returns a dict, keyed by class name, of every concrete `StatusCode`
    subclass (i.e. one which defines at least one status value - this
    excludes abstract base classes such as `MachineStatus`, which is
    subclassed per machine driver/plugin rather than used directly).

    Each entry contains the class' module path and 'tag', plus a list of its
    status values. The description of each value is sourced from the
    class docstring's Google-style `Attributes:` block (see e.g.
    `build.status_codes.BuildStatus`), rather than being manually curated
    here - so a status code's description can never drift out of sync with
    its source.
    """
    data = {}

    for cls in inheritors(StatusCode):
        # custom=False: this is a definition of the *built-in* status codes as
        # they exist in source - user/plugin-defined custom states are runtime data
        values = cls.dict(custom=False)

        if not values:
            # Abstract base class with no concrete status values (e.g. MachineStatus)
            continue

        attributes = parse_docstring(cls.__doc__ or '').get('Attributes', {})

        data[cls.__name__] = {
            'module': cls.__module__,
            'tag': cls.tag(),
            'values': [
                {
                    'name': item['name'],
                    'key': item['key'],
                    'label': str(item['label']),
                    'color': item['color'],
                    'description': attributes.get(item['name'], ''),
                }
                for item in values.values()
            ],
        }

    return dict(sorted(data.items()))
