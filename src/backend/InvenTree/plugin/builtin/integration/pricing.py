"""Builtin plugin for providing pricing functionality."""

from django.utils.translation import gettext_lazy as _

import structlog

from plugin import InvenTreePlugin
from plugin.mixins import PricingMixin, SettingsMixin

logger = structlog.get_logger('inventree')


class InvenTreePricingPlugin(PricingMixin, SettingsMixin, InvenTreePlugin):
    """Default InvenTree plugin for pricing functionality."""

    NAME = 'InvenTreePricingPlugin'
    SLUG = 'inventree-pricing'
    AUTHOR = _('InvenTree contributors')
    TITLE = _('InvenTree Pricing Plugin')
    DESCRIPTION = _('Provides default pricing integration functionality for InvenTree')
    VERSION = '1.0.0'
