"""Custom management command to export all filters.

This is used to generate a YAML file which contains all of the filters available in InvenTree.
"""

from django.contrib.admindocs import utils
from django.core.exceptions import ImproperlyConfigured
from django.core.management.base import BaseCommand
from django.template.engine import Engine

import yaml


class Command(BaseCommand):
    """Extract filter information, and export to a YAML file."""

    def add_arguments(self, parser):
        """Add custom arguments for this command."""
        parser.add_argument(
            'filename', type=str, help='Output filename for filter definitions'
        )

    def handle(self, *args, **kwargs):
        """Export filter information to a YAML file."""
        filters = discover_filters()
        # Write
        filename = kwargs.get('filename', 'inventree_filters.yml')
        with open(filename, 'w', encoding='utf-8') as f:
            yaml.dump(filters, f, indent=4)
        print(f"Exported InvenTree filter definitions to '{filename}'")


def discover_filters():
    """Discover all available filters.

    This function is a copy of a function from the Django 'admindocs' module in django.contrib.admindocs.views.TemplateFilterIndexView
    """
    filters = []
    try:
        engine = Engine.get_default()
    except ImproperlyConfigured:
        # Non-trivial TEMPLATES settings aren't supported (#24125).
        pass
    else:
        app_libs = sorted(engine.template_libraries.items())
        builtin_libs = [('', lib) for lib in engine.template_builtins]
        for module_name, library in builtin_libs + app_libs:
            for filter_name, filter_func in library.filters.items():
                title, body, metadata = utils.parse_docstring(filter_func.__doc__)
                tag_library = module_name.split('.')[-1]
                filters.append({
                    'name': filter_name,
                    'title': title,
                    'body': body,
                    'meta': metadata,
                    'library': tag_library,
                })
    return filters
