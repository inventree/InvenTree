"""Custom management command to export the available report context.

This is used to generate a JSON file which contains all available report
context, so that they can be introspected by the InvenTree documentation system.

This in turn allows report context to be documented in the InvenTree documentation,
without having to manually duplicate the information in multiple places.
"""

import json
from typing import get_args, get_origin, get_type_hints

import django.db.models
from django.core.management.base import BaseCommand, CommandError

from report.mixins import QuerySet


def get_type_str(type_obj):
    """Get the type str of a type object, including any generic parameters."""
    if type_obj is django.db.models.QuerySet:
        raise CommandError(
            'INVE-E3 - Do not use django.db.models.QuerySet directly for typing, use report.mixins.QuerySet instead.'
        )

    if origin := get_origin(type_obj):
        # use abbreviated name for QuerySet to save space
        origin_str = 'QuerySet' if origin is QuerySet else get_type_str(origin)

        return f'{origin_str}[{", ".join(get_type_str(arg) for arg in get_args(type_obj))}]'

    if type_obj is type(None):
        return 'None'

    if type_obj.__module__ == 'builtins':
        return type_obj.__name__

    return f'{type_obj.__module__}.{type_obj.__name__}'


def parse_docstring(docstring: str):
    """Parse the docstring of a type object and return a dictionary of sections."""
    sections = {}
    current_section = None

    for line in docstring.splitlines():
        stripped = line.strip()

        if not stripped:
            continue

        if stripped.endswith(':'):
            current_section = stripped.rstrip(':')
            sections[current_section] = {}
        elif ':' in stripped and current_section:
            name, doc = stripped.split(':', 1)
            sections[current_section][name.strip()] = doc.strip()

    return sections


class Command(BaseCommand):
    """Extract report context information, and export to a JSON file."""

    def add_arguments(self, parser):
        """Add custom arguments for this command."""
        parser.add_argument(
            'filename',
            type=str,
            help='Output filename for the report context definitions',
        )

    def handle(self, *args, **kwargs):
        """Export report context information to a JSON file."""
        from report.helpers import report_model_types
        from report.models import (
            BaseContextExtension,
            LabelContextExtension,
            ReportContextExtension,
        )

        context = {'models': {}, 'base': {}}
        is_error = False

        # Base context models
        for key, model in [
            ('global', BaseContextExtension),
            ('report', ReportContextExtension),
            ('label', LabelContextExtension),
        ]:
            context['base'][key] = {'key': key, 'context': {}}

            attributes = parse_docstring(model.__doc__).get('Attributes', {})
            for k, v in get_type_hints(model).items():
                context['base'][key]['context'][k] = {
                    'description': attributes.get(k, ''),
                    'type': get_type_str(v),
                }

        # Report context models
        for model in report_model_types():
            model_key = model.__name__.lower()
            model_name = str(model._meta.verbose_name)

            if (
                ctx_type := get_type_hints(model.report_context).get('return', None)
            ) is None:
                print(
                    f'Error: Model {model}.report_context does not have a return type annotation'
                )
                is_error = True
                continue

            context['models'][model_key] = {
                'key': model_key,
                'name': model_name,
                'context': {},
            }

            attributes = parse_docstring(ctx_type.__doc__).get('Attributes', {})
            for k, v in get_type_hints(ctx_type).items():
                context['models'][model_key]['context'][k] = {
                    'description': attributes.get(k, ''),
                    'type': get_type_str(v),
                }

        if is_error:
            raise CommandError(
                'INVE-E4 - Some models associated with the `InvenTreeReportMixin` do not have a valid `report_context` return type annotation.'
            )

        filename = kwargs.get('filename', 'inventree_report_context.json')

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(context, f, indent=4)

        print(f"Exported InvenTree report context definitions to '{filename}'")
