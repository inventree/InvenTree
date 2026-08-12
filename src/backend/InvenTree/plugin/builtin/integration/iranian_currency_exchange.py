"""Builtin plugin for Iranian rial currency exchange rates."""

import decimal

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

import requests
import structlog

from common.settings import get_global_setting
from plugin import InvenTreePlugin
from plugin.mixins import CurrencyExchangeMixin, ScheduleMixin, SettingsMixin

logger = structlog.get_logger('inventree')


def validate_positive_finite_rate(value):
    """Validate a rate which can safely be used for currency conversion."""
    try:
        rate = decimal.Decimal(str(value))
    except (decimal.InvalidOperation, TypeError, ValueError):
        rate = decimal.Decimal(0)

    if not rate.is_finite() or rate <= 0:
        raise ValidationError(
            _('Enter a positive, finite USD to IRR rate'), code='invalid'
        )


class IranianCurrencyExchange(
    ScheduleMixin, CurrencyExchangeMixin, SettingsMixin, InvenTreePlugin
):
    """Provide a USD to IRR rate from manual configuration or Navasan."""

    NAME = 'IranianCurrencyExchange'
    SLUG = 'iranian-currency-exchange'
    AUTHOR = _('InvenTree contributors')
    TITLE = _('Iranian Currency Exchange')
    DESCRIPTION = _('Manual or API-provided USD to IRR exchange rates')
    VERSION = '1.0.0'

    API_URL = 'https://api.navasan.tech/latest/'
    API_ITEM = 'usd_sell'
    API_TIMEOUT = 10

    SCHEDULED_TASKS = {
        'refresh_usd_irr': {'func': 'refresh_usd_irr', 'schedule': 'I', 'minutes': 480}
    }

    SETTINGS = {
        'API_ENABLED': {
            'name': _('Enable USD exchange rate API'),
            'description': _(
                'Consume the Navasan API for USD to IRR updates instead of using the manual rate'
            ),
            'validator': bool,
            'default': False,
        },
        'USD_IRR_RATE': {
            'name': _('Manual USD to IRR rate'),
            'description': _('Iranian rials per one US dollar'),
            'units': _('IRR per USD'),
            'validator': [float, validate_positive_finite_rate],
        },
        'API_KEY': {
            'name': _('Navasan API key'),
            'description': _('Required when exchange rate API is enabled'),
            'protected': True,
            'default': '',
        },
        'API_VALUE_UNIT': {
            'name': _('Navasan value unit'),
            'description': _(
                'Select the unit returned for your Navasan account to prevent a tenfold conversion error'
            ),
            'choices': [
                ('', _('Select value unit')),
                ('IRR', _('Iranian rial (IRR)')),
                ('IRT', _('Iranian toman (IRT)')),
            ],
            'default': '',
        },
    }

    _DIGIT_TRANSLATION = str.maketrans('۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩', '01234567890123456789')

    @classmethod
    def _parse_rate(cls, value) -> decimal.Decimal:
        """Parse and validate a positive exchange rate."""
        text = str(value).translate(cls._DIGIT_TRANSLATION)
        text = text.replace(',', '').replace('٬', '').replace('،', '').strip()
        rate = decimal.Decimal(text)

        if not rate.is_finite() or rate <= 0:
            raise ValueError('USD to IRR rate must be a positive finite number')

        return rate

    def _manual_rate(self) -> decimal.Decimal | None:
        """Return the configured manual rate, if valid."""
        try:
            return self._parse_rate(self.get_setting('USD_IRR_RATE'))
        except (decimal.InvalidOperation, TypeError, ValueError):
            logger.warning('Manual USD to IRR exchange rate is not valid')
            return None

    def _api_rate(self) -> decimal.Decimal | None:
        """Fetch the latest Tehran USD sell rate from Navasan."""
        api_key = self.get_setting('API_KEY')
        unit = str(self.get_setting('API_VALUE_UNIT')).upper()

        if not api_key:
            logger.warning('Navasan API key is not configured')
            return None

        if unit not in {'IRR', 'IRT'}:
            logger.warning('Navasan API value unit is not configured')
            return None

        try:
            # Navasan latest-rates API contract:
            # https://www.navasan.tech/webserviceguide/#latest-rates
            # Requests recommends an explicit timeout for production calls:
            # https://requests.readthedocs.io/en/latest/user/quickstart/#timeouts
            response = requests.get(
                self.API_URL,
                params={'item': self.API_ITEM, 'api_key': api_key},
                headers={'Accept': 'application/json'},
                timeout=self.API_TIMEOUT,
            )
            response.raise_for_status()
            value = response.json()[self.API_ITEM]['value']
            rate = self._parse_rate(value)
        except requests.RequestException:
            logger.warning('Navasan USD to IRR exchange rate request failed')
            return None
        except (decimal.InvalidOperation, KeyError, TypeError, ValueError):
            logger.warning('Navasan returned an invalid USD to IRR exchange rate')
            return None

        # One toman is exactly ten rials.
        return rate * 10 if unit == 'IRT' else rate

    def refresh_usd_irr(self):
        """Refresh the selected API exchange rate on the plugin schedule."""
        if not self.get_setting('API_ENABLED'):
            return

        selected_plugin = get_global_setting(
            'CURRENCY_UPDATE_PLUGIN', create=False, cache=False
        )

        if selected_plugin != self.slug:
            return

        from InvenTree.tasks import update_exchange_rates

        update_exchange_rates(force=True)

    def update_exchange_rates(self, base_currency: str, symbols: list[str]) -> dict:
        """Return USD-based rates for the phase-one USD and IRR scope."""
        base_currency = str(base_currency).upper()
        requested = {str(symbol).upper() for symbol in symbols}
        supported = {'USD', 'IRR'}

        # django-money stores only six decimal places for exchange rates. Using IRR
        # as the base would round the reciprocal USD rate too aggressively.
        if base_currency != 'USD':
            logger.warning(
                'Iranian currency exchange plugin requires USD base currency'
            )
            return {}

        if not requested.issubset(supported):
            logger.warning('Iranian currency exchange plugin supports only USD and IRR')
            return {}

        rates = {'USD': decimal.Decimal(1)}

        if 'IRR' not in requested:
            return rates

        rate = (
            self._api_rate() if self.get_setting('API_ENABLED') else self._manual_rate()
        )

        if rate is None:
            # An empty result tells the exchange backend to preserve last-known rates.
            return {}

        rates['IRR'] = rate
        return rates
