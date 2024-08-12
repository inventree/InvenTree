"""Sample plugin which demonstrates user interface integrations."""

from django.utils.translation import gettext_lazy as _

from plugin import InvenTreePlugin
from plugin.mixins import SettingsMixin, UserInterfaceMixin


class SampleUserInterfacePlugin(SettingsMixin, UserInterfaceMixin, InvenTreePlugin):
    """A sample plugin which demonstrates user interface integrations."""

    NAME = 'SampleUI'
    SLUG = 'sampleui'
    TITLE = 'Sample User Interface Plugin'
    DESCRIPTION = 'A sample plugin which demonstrates user interface integrations'
    VERSION = '1.0'

    SETTINGS = {
        'ENABLE_PART_PANELS': {
            'name': _('Enable Part Panels'),
            'description': _('Enable custom panels for Part views'),
            'default': True,
            'validator': bool,
        },
        'ENABLE_PURCHASE_ORDER_PANELS': {
            'name': _('Enable Purchase Order Panels'),
            'description': _('Enable custom panels for Purchase Order views'),
            'default': False,
            'validator': bool,
        },
    }
