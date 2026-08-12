"""Builtin plugin for Iranian rial currency exchange rates."""

import decimal

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

import requests
import structlog
from lxml import etree, html

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
    """Provide a USD to IRR rate from manual configuration or TGJU."""

    NAME = 'IranianCurrencyExchange'
    SLUG = 'iranian-currency-exchange'
    AUTHOR = _('Nooshin Shadiani')
    TITLE = _('Iranian Currency Exchange')
    DESCRIPTION = _('Manual or TGJU-provided USD to IRR exchange rates')
    VERSION = '1.0.0'

    TGJU_CURRENCY_URL = 'https://www.tgju.org/currency'
    TGJU_PROFILE_URL = 'https://www.tgju.org/profile/price_dollar_rl'
    REQUEST_TIMEOUT = 10
    REQUEST_HEADERS = {
        'Accept': 'text/html',
        'User-Agent': 'InvenTree Iranian Currency Exchange/1.0',
    }
    TGJU_SOURCES = (
        (
            TGJU_CURRENCY_URL,
            (
                "string((//tr[@data-market-row='price_dollar_rl']/@data-price)[1])",
                "string((//*[@id='l-price_dollar_rl']//*[contains(concat(' ', normalize-space(@class), ' '), ' info-price ')])[1])",
            ),
        ),
        (
            TGJU_PROFILE_URL,
            (
                "string((//*[@data-target='profile-tour-current_rate']//*[@data-col='info.last_trade.PDrCotVal'])[1])",
            ),
        ),
    )

    SCHEDULED_TASKS = {
        'refresh_usd_irr': {'func': 'refresh_usd_irr', 'schedule': 'I', 'minutes': 180}
    }

    SETTINGS = {
        'API_ENABLED': {
            'name': _('Enable TGJU USD rate consumer'),
            'description': _(
                'Fetch the free-market USD to IRR rate from TGJU using XPath instead of using the manual rate'
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

    @classmethod
    def _extract_tgju_rate(cls, content, xpaths) -> decimal.Decimal | None:
        """Extract the first valid IRR rate from TGJU HTML using XPath."""
        try:
            document = html.fromstring(content)
        except (etree.ParserError, TypeError, ValueError):
            return None

        for xpath in xpaths:
            try:
                return cls._parse_rate(document.xpath(xpath))
            except (decimal.InvalidOperation, TypeError, ValueError):
                continue

        return None

    def _tgju_rate(self) -> decimal.Decimal | None:
        """Fetch the TGJU free-market USD rate, expressed in Iranian rials."""
        for url, xpaths in self.TGJU_SOURCES:
            try:
                response = requests.get(
                    url, headers=self.REQUEST_HEADERS, timeout=self.REQUEST_TIMEOUT
                )
                response.raise_for_status()
            except requests.RequestException:
                continue

            if rate := self._extract_tgju_rate(response.content, xpaths):
                return rate

        logger.warning('TGJU returned no valid USD to IRR exchange rate')
        return None

    def refresh_usd_irr(self):
        """Refresh the selected TGJU exchange rate on the plugin schedule."""
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

        if requested != supported:
            logger.warning('Iranian currency exchange plugin requires USD and IRR')
            return {}

        rate = (
            self._tgju_rate()
            if self.get_setting('API_ENABLED')
            else self._manual_rate()
        )

        if rate is None:
            # An empty result tells the exchange backend to preserve last-known rates.
            return {}

        return {'USD': decimal.Decimal(1), 'IRR': rate}
