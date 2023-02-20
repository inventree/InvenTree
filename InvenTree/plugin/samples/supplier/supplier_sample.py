"""Sample implementations for supplier plugin."""
from django.utils.translation import gettext_lazy as _

from common.models import WebConnectionData
from plugin import InvenTreePlugin
from plugin.mixins import SupplierMixin


class SampleSupplierPlugin(SupplierMixin, InvenTreePlugin):
    """Sample supplier plugin."""

    NAME = "SampleSupplierPlugin"
    SLUG = "samplesupplier"

    CONNECTIONS = {
        'sample_account': WebConnectionData(
            name='A Sample Account',
            description=_('An Account for a sample supplier'),
            settings={
                'SETTING_A': {
                    'name': _('Setting A'),
                    'description': _('Setting A Description'),
                },
            }
        ),
    }
