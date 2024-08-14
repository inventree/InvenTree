"""Helper functions for custom status labels."""

from common.models import InvenTreeCustomUserStateModel
from InvenTree.helpers import inheritors

from .states import StatusCode


def get_custom_status_labels(include_custom: bool = True):
    """Return a dict of custom status labels."""
    return {cls.tag(): cls for cls in get_custom_classes(include_custom)}


def get_custom_classes(include_custom: bool = True):
    """Return a dict of status classes (custom and class defined)."""
    if not include_custom:
        return inheritors(StatusCode)

    # Gather DB settings
    custom_db_states = {}
    custom_db_mdls = {}
    for item in list(InvenTreeCustomUserStateModel.objects.all()):
        if not custom_db_states.get(item.reference_status):
            custom_db_states[item.reference_status] = []
        custom_db_states[item.reference_status].append(item)
        custom_db_mdls[item.model.app_label] = item.reference_status
    custom_db_mdls_keys = custom_db_mdls.keys()

    states = {}
    for cls in inheritors(StatusCode):
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
            states[tag] = StatusCode(f'{tag.capitalize()}Status', data)
    return states.values()
