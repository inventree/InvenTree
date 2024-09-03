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

    # Gather DB settings
    from common.models import InvenTreeCustomUserStateModel

    custom_db_states = {}
    custom_db_mdls = {}
    for item in list(InvenTreeCustomUserStateModel.objects.all()):
        if not custom_db_states.get(item.reference_status):
            custom_db_states[item.reference_status] = []
        custom_db_states[item.reference_status].append(item)
        custom_db_mdls[item.model.app_label] = item.reference_status
    custom_db_mdls_keys = custom_db_mdls.keys()

    states = {}
    for cls in discovered_classes:
        tag = cls.tag()
        states[tag] = cls
        if custom_db_mdls and tag in custom_db_mdls_keys:
            data = [(str(m.name), (m.value, m.label, m.color)) for m in states[tag]]
            data_keys = [i[0] for i in data]

            # Extent with non present tags
            for entry in custom_db_states[custom_db_mdls[tag]]:
                ref_name = str(entry.name.upper().replace(' ', ''))
                if ref_name not in data_keys:
                    data += [
                        (
                            str(entry.name.upper().replace(' ', '')),
                            (entry.key, entry.label, entry.color),
                        )
                    ]

            # Re-assemble the enum
            states[tag] = base_class(f'{tag.capitalize()}Status', data)
    return states.values()
