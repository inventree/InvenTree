"""Custom management command to export the fsm states of models."""

import json

from django.apps import apps
from django.core.management.base import BaseCommand
from django.utils.text import capfirst

from generic.states import DEFERRABLE, RETURN_VALUE
from generic.states.introspection import state_fields, transition_methods


class Command(BaseCommand):
    """Extract fsm model information, and export to a JSON file."""

    def add_arguments(self, parser):
        """Add custom arguments for this command."""
        parser.add_argument(
            'filename', type=str, help='Output filename for audited model definitions'
        )

    def handle(self, *args, **kwargs):
        """Export fsm model information to a JSON file."""
        models = discover_fsm_models()

        filename = kwargs.get('filename', 'inventree_audited_models.json')

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(models, f, indent=4)

        print(f"Exported InvenTree fsm model definitions to '{filename}'")


def extract_value(src):
    """Return the plain value (or list of values) of a transition source/target."""
    if isinstance(src, DEFERRABLE):
        src = src.target

    value = getattr(src, 'value', src)

    if isinstance(value, RETURN_VALUE):
        return [state.value for state in value.allowed_states]
    return value


def describe_operations(methods):
    """Describe each transition method with its sources, targets and conditions."""
    return {
        name: {
            key: {
                'source': extract_value(transition.source),
                'extra_permission': transition.permission,
                'target': extract_value(transition.target),
                'conditions': list(transition.conditions),
            }
            for key, transition in meta.transitions.items()
        }
        for name, meta in methods.items()
    }


def reachable_states(methods):
    """Map each source state to the sorted list of states reachable from it."""
    # target -> sources; the last transition of a method defines its targets
    sources_by_target = {}
    for meta in methods.values():
        sources = []
        targets = []
        for transition in meta.transitions.values():
            targets = extract_value(transition.target)
            if not isinstance(targets, list):
                targets = [int(targets)]
            sources.append(extract_value(transition.source))
        for target in targets:
            sources_by_target[target] = sources

    reachable = {}
    for target, sources in sources_by_target.items():
        for source in sources:
            reachable.setdefault(source, []).append(target)
    return {source: sorted(targets) for source, targets in reachable.items()}


def discover_fsm_models():
    """Discover all models which have fsm states.

    Returns a list of models, sorted by app and then by model name.
    """
    from generic.states.api_helpers import supported_models

    models = []

    for model in supported_models():
        states = {}
        for field in state_fields(model):
            methods = transition_methods(model, field)
            states[field] = {
                'operations': describe_operations(methods),
                'transitions': reachable_states(methods),
                'states': {
                    value: str(label)
                    for value, label in getattr(model, field).field.choices
                },
            }

        models.append({
            'model_type': model._meta.label_lower,
            'app': str(apps.get_app_config(model._meta.app_label).verbose_name),
            'name': capfirst(str(model._meta.verbose_name)),
            'states': states,
        })

    return sorted(models, key=lambda m: (m['app'], m['name']))
