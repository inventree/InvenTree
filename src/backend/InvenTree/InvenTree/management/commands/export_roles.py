"""Custom management command to export all user permission roles.

This is used to generate a JSON file which contains all of the roles (rulesets)
available in InvenTree, so that they can be introspected by the InvenTree
documentation system. This allows the roles table to be documented without
having to manually duplicate the information (which otherwise silently drifts
out of sync with the source code - e.g. a newly added ruleset going undocumented).
"""

import json

from django.core.management.base import BaseCommand

from users.ruleset import RULESET_CHOICES, RuleSetEnum, get_ruleset_models

from .export_report_context import parse_docstring


class Command(BaseCommand):
    """Extract user permission role information, and export to a JSON file."""

    def add_arguments(self, parser):
        """Add custom arguments for this command."""
        parser.add_argument(
            'filename', type=str, help='Output filename for role definitions'
        )

    def handle(self, *args, **kwargs):
        """Export role information to a JSON file."""
        roles = discover_roles()

        filename = kwargs.get('filename', 'inventree_roles.json')

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(roles, f, indent=4)

        print(f"Exported InvenTree role definitions to '{filename}'")


def get_model_names() -> dict:
    """Return a mapping of database table names to model names."""
    from django.apps import apps

    names = {}

    for model in apps.get_models():
        table = f'{model._meta.app_label}_{model._meta.model_name}'
        names[table] = str(model._meta.verbose_name).capitalize()

    return names


def discover_roles():
    """Discover all available user permission roles (rulesets).

    Returns a list of roles, in the order they are declared in `RULESET_CHOICES`.
    Each role's description is sourced from `RuleSetEnum`'s docstring `Attributes:`
    block, rather than being manually curated here - so a role's description can
    never drift out of sync with its source.

    Each role also lists the database models it grants permissions against
    (sourced from `get_ruleset_models`) - some models are covered by multiple roles.
    """
    attributes = parse_docstring(RuleSetEnum.__doc__ or '').get('Attributes', {})
    ruleset_models = get_ruleset_models()
    model_names = get_model_names()

    return [
        {
            'name': key.name,
            'key': str(key.value),
            'label': str(label),
            'description': attributes.get(key.name, ''),
            'models': [
                {'table': table, 'name': model_names.get(table, table)}
                for table in ruleset_models.get(key.value, [])
            ],
        }
        for key, label in RULESET_CHOICES
    ]
