"""Helper functions for custom status labels."""

from InvenTree.helpers import inheritors

from .states import ColorEnum, StatusCode


def get_custom_status_labels(include_custom: bool = True):
    """Return a dict of custom status labels."""
    return {cls.tag(): cls for cls in get_custom_classes(include_custom)}


def get_status_api_response(base_class=StatusCode, prefix=None):
    """Return a dict of status classes (custom and class defined).

    Args:
        base_class: The base class to search for subclasses.
        prefix: A list of strings to prefix the class names with.
    """
    return {
        '__'.join([*(prefix or []), k.__name__]): {
            'class': k.__name__,
            'values': k.dict(),
        }
        for k in get_custom_classes(base_class=base_class, subclass=False)
    }


def state_color_mappings():
    """Return a list of custom user state colors."""
    return [(a.name, a.value) for a in ColorEnum]


def state_reference_mappings():
    """Return a list of custom user state references."""
    classes = get_custom_classes(include_custom=False)
    return [(a.__name__, a.__name__) for a in sorted(classes, key=lambda x: x.__name__)]


def get_logical_value(value, model: str):
    """Return the state model for the selected value."""
    from common.models import InvenTreeCustomUserStateModel

    return InvenTreeCustomUserStateModel.objects.get(key=value, model__model=model)


def get_custom_classes(
    include_custom: bool = True, base_class=StatusCode, subclass=False
):
    """Return a dict of status classes (custom and class defined)."""
    discovered_classes = inheritors(base_class, subclass)

    if not include_custom:
        return discovered_classes

    states = {}

    for cls in discovered_classes:
        name = cls.__name__
        states[name] = cls

        data = [(str(m.name), (m.value, m.label, m.color)) for m in cls]

        labels = [str(item[0]) for item in data]

        for item in cls.custom_values():
            label = str(item.name)
            if label not in labels and label not in cls.labels():
                data += [(str(item.name), (item.key, item.label, item.color))]

        # Re-assemble the enum
        states[name] = base_class(name, data)

    return states.values()
