"""Custom management command to export the models which are recorded in the audit log.

This is used to generate a JSON file which contains all of the audited models
(those which implement the InvenTreeAuditMixin), so that they can be introspected
by the InvenTree documentation system. This allows the audited models table to be
documented without having to manually duplicate the information (which otherwise
silently drifts out of sync with the source code).
"""

import inspect
import json

from django.apps import apps
from django.core.management.base import BaseCommand
from django.utils.text import capfirst


class Command(BaseCommand):
    """Extract audited model information, and export to a JSON file."""

    def add_arguments(self, parser):
        """Add custom arguments for this command."""
        parser.add_argument(
            'filename', type=str, help='Output filename for audited model definitions'
        )

    def handle(self, *args, **kwargs):
        """Export audited model information to a JSON file."""
        models = discover_audited_models()

        filename = kwargs.get('filename', 'inventree_audited_models.json')

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(models, f, indent=4)

        print(f"Exported InvenTree audited model definitions to '{filename}'")


def audit_parent(model) -> tuple[str, str]:
    """Return a (parent, note) description of the "parent" object for audit entries against a model.

    - If the parent is a foreign key field, the name of the related model is returned
    - If the parent reference is resolved by a custom method, the method docstring summary is returned as a note
    """
    from InvenTree.models import InvenTreeAuditMixin

    if model.AUDIT_PARENT_FIELD:
        field = model._meta.get_field(model.AUDIT_PARENT_FIELD)

        if field.related_model:
            return capfirst(str(field.related_model._meta.verbose_name)), ''

    method = model.get_audit_parent_reference

    if method is not InvenTreeAuditMixin.get_audit_parent_reference:
        doc = inspect.getdoc(method) or ''
        return '', doc.split('\n\n')[0].replace('\n', ' ').strip()

    return '', ''


def discover_audited_models():
    """Discover all models which are recorded in the audit log.

    Returns a list of models, sorted by app and then by model name.
    """
    from audit.registry import audited_models

    models = []

    for model in audited_models():
        parent, parent_note = audit_parent(model)

        models.append({
            'model_type': model._meta.label_lower,
            'app': str(apps.get_app_config(model._meta.app_label).verbose_name),
            'name': capfirst(str(model._meta.verbose_name)),
            'parent': parent,
            'parent_note': parent_note,
            'include_fields': sorted(getattr(model, 'AUDIT_INCLUDE_FIELDS', ())),
        })

    return sorted(models, key=lambda m: (m['app'], m['name']))
