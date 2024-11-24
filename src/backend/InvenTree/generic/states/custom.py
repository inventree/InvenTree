"""Helper functions for custom status labels."""

from InvenTree.helpers import inheritors

from .states import ColorEnum, StatusCode


def get_custom_status_labels(include_custom: bool = True):
    """Return a dict of custom status labels."""
    return {cls.tag(): cls for cls in inheritors(StatusCode)}


def state_color_mappings():
    """Return a list of custom user state colors."""
    return [(a.name, a.value) for a in ColorEnum]


def state_reference_mappings():
    """Return a list of custom user state references."""
    classes = inheritors(StatusCode)
    return [(a.__name__, a.__name__) for a in sorted(classes, key=lambda x: x.__name__)]


def get_logical_value(value, model: str):
    """Return the state model for the selected value."""
    from common.models import InvenTreeCustomUserStateModel

    return InvenTreeCustomUserStateModel.objects.get(key=value, model__model=model)
