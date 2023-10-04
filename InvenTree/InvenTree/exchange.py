"""Custom exchange backend which hooks into the InvenTree plugin system to fetch exchange rates from an external API."""

import logging

from djmoney.contrib.exchange.backends.base import SimpleExchangeBackend

from common.settings import currency_code_default, currency_codes

logger = logging.getLogger('inventree')


class InvenTreeExchange(SimpleExchangeBackend):
    """Backend for automatically updating currency exchange rates.

    Uses the plugin system to actually fetch the rates from an external API.
    """

    name = "InvenTreeExchange"

    def update_rates(self, base_currency=None) -> None:
        """Set the requested currency codes and get rates."""

        from common.models import InvenTreeSetting
        from plugin import registry

        # Set default - see B008
        if base_currency is None:
            base_currency = currency_code_default()

        plugins = registry.with_mixin('currencyexchange')

        # Find the selected exchange rate plugin
        slug = InvenTreeSetting.get_setting('CURRENCY_UPDATE_PLUGIN', '', create=False)

        if slug:
            plugin = plugins.get_plugin(slug)
        else:
            plugin = None

        if not plugin:
            # Find the first active currency exchange plugin
            plugins = registry.with_mixin('currencyexchange', active=True)

            if len(plugins) > 0:
                plugin = plugins[0]

        if not plugin:
            logger.warning('No active currency exchange plugins found - skipping update')
            return

        # Plugin found - run the update task
        try:
            rates = plugin.update_exchange_rates(base_currency, currency_codes())
        except Exception as exc:
            logger.exception("Exchange rate update failed: %s", exc)
            return

        if rates:
            # Update exchange rates based on returned data
            ...
