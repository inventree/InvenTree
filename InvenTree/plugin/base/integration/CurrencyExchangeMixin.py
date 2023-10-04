"""Plugin mixin class for supporting currency exchange data"""


class CurrencyExchangeMixin:
    """Mixin class which provides support for currency exchange rates

    Nominally this plugin mixin would be used to interface with an external API,
    to periodically retrieve currency exchange rate information.

    The plugin class *must* implement the update_exchange_rates method,
    which is called periodically by the background worker thread.
    """

    class MixinMeta:
        """Meta options for this mixin class"""

        MIXIN_NAME = "CurrentExchange"

    def __init__(self):
        """Register the mixin"""
        super().__init__()
        self.add_mixin('currency', True, __class__)

    def update_exchange_rates(self):
        """Update currency exchange rates.

        This method must be implemented by the plugin class.
        """
        raise NotImplementedError("Plugin must implement update_exchange_rates method")
