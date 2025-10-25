"""Pricing mixin class for supporting pricing data."""

from plugin import PluginMixinEnum


class PricingMixin:
    """Mixin class which provides support for pricing functionality.

    - This plugin class provides stubs for pricing-related features.
    - A default implementation is provided which can be overridden by the plugin.
    """

    class MixinMeta:
        """Meta options for this mixin class."""

        MIXIN_NAME = 'Pricing'

    def __init__(self):
        """Register the mixin."""
        super().__init__()
        self.add_mixin(PluginMixinEnum.PRICING, True, __class__)
