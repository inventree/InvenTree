"""Custom management command to export all tags.

This is used to generate a YAML file which contains all of the tags available in InvenTree.
"""

from django.contrib.admindocs import utils
from django.core.exceptions import ImproperlyConfigured
from django.core.management.base import BaseCommand
from django.template.engine import Engine

import yaml


class Command(BaseCommand):
    """Extract tag information, and export to a YAML file."""

    def add_arguments(self, parser):
        """Add custom arguments for this command."""
        parser.add_argument(
            'filename', type=str, help='Output filename for tag definitions'
        )

    def handle(self, *args, **kwargs):
        """Export tag information to a YAML file."""
        tags = discover_tags()

        # Write
        filename = kwargs.get('filename', 'inventree_tags.yml')
        with open(filename, 'w', encoding='utf-8') as f:
            yaml.dump(tags, f, indent=4)
        print(f"Exported InvenTree tag definitions to '{filename}'")


def discover_tags():
    """Discover all available tags.

    This function is a copy of a function from the Django 'admindocs' module in django.contrib.admindocs.views.TemplateTagIndexView
    """
    tags = []
    try:
        engine = Engine.get_default()
    except ImproperlyConfigured:
        # Non-trivial TEMPLATES settings aren't supported (#24125).
        pass
    else:
        app_libs = sorted(engine.template_libraries.items())
        builtin_libs = [('', lib) for lib in engine.template_builtins]
        for module_name, library in builtin_libs + app_libs:
            for tag_name, tag_func in library.tags.items():
                title, body, metadata = utils.parse_docstring(tag_func.__doc__)
                tag_library = module_name.split('.')[-1]
                tags.append({
                    'name': tag_name,
                    'title': title,
                    'body': body,
                    'meta': metadata,
                    'library': tag_library,
                })
    return tags
