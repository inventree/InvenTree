"""Custom exchange backend which hooks into the InvenTree plugin system to fetch exchange rates from an external API."""

import logging

from django.db.transaction import atomic

from djmoney.contrib.exchange.backends.base import SimpleExchangeBackend
from djmoney.contrib.exchange.models import ExchangeBackend, Rate

from common.settings import currency_code_default, currency_codes

logger = logging.getLogger('inventree')


class InvenTreeExchange(SimpleExchangeBackend):
    """Backend for automatically updating currency exchange rates.

    Uses the plugin system to actually fetch the rates from an external API.
    """

    name = "InvenTreeExchange"

    def get_rates(self, **kwargs) -> None:
        """Set the requested currency codes and get rates."""
        from common.models import InvenTreeSetting
        from plugin import registry

        base_currency = kwargs.get('base_currency', currency_code_default())
        symbols = kwargs.get('symbols', currency_codes())

        # Find the selected exchange rate plugin
        slug = InvenTreeSetting.get_setting('CURRENCY_UPDATE_PLUGIN', '', create=False)

        if slug:
            plugin = registry.get_plugin(slug)
        else:
            plugin = None

        if not plugin:
            # Find the first active currency exchange plugin
            plugins = registry.with_mixin('currencyexchange', active=True)

            if len(plugins) > 0:
                plugin = plugins[0]

        if not plugin:
            logger.warning(
                'No active currency exchange plugins found - skipping update'
            )
            return {}

        logger.info("Running exchange rate update using plugin '%s'", plugin.name)

        # Plugin found - run the update task
        try:
            rates = plugin.update_exchange_rates(base_currency, symbols)
        except Exception as exc:
            logger.exception("Exchange rate update failed: %s", exc)
            return {}

        if not rates:
            logger.warning(
                "Exchange rate update failed - no data returned from plugin %s", slug
            )
            return {}

        # Update exchange rates based on returned data
        if type(rates) is not dict:
            logger.warning(
                "Invalid exchange rate data returned from plugin %s (type %s)",
                slug,
                type(rates),
            )
            return {}

        # Ensure base currency is provided
        rates[base_currency] = 1.00

        return rates

    @atomic
    def update_rates(self, base_currency=None, **kwargs):
        """Call to update all exchange rates"""
        backend, _ = ExchangeBackend.objects.update_or_create(
            name=self.name, defaults={"base_currency": base_currency}
        )

        if base_currency is None:
            base_currency = currency_code_default()

        symbols = currency_codes()

        logger.info(
            "Updating exchange rates for %s (%s currencies)",
            base_currency,
            len(symbols),
        )

        # Fetch new rates from the backend
        # If the backend fails, the existing rates will not be updated
        rates = self.get_rates(base_currency=base_currency, symbols=symbols)

        if rates:
            # Clear out existing rates
            backend.clear_rates()

            Rate.objects.bulk_create([
                Rate(currency=currency, value=amount, backend=backend)
                for currency, amount in rates.items()
            ])
        else:
            logger.info(
                "No exchange rates returned from backend - currencies not updated"
            )

        logger.info("Updated exchange rates for %s", base_currency)
