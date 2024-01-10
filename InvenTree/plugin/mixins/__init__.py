"""Utility class to enable simpler imports."""

from common.notifications import BulkNotificationMethod, SingleNotificationMethod

from plugin.base.action.mixins import ActionMixin
from plugin.base.barcodes.mixins import BarcodeMixin, SupplierBarcodeMixin
from plugin.base.event.mixins import EventMixin
from plugin.base.integration.APICallMixin import APICallMixin
from plugin.base.integration.AppMixin import AppMixin
from plugin.base.integration.CurrencyExchangeMixin import CurrencyExchangeMixin
from plugin.base.integration.mixins import (
    NavigationMixin,
    PanelMixin,
    SettingsContentMixin,
)
from plugin.base.integration.ReportMixin import ReportMixin
from plugin.base.integration.ScheduleMixin import ScheduleMixin
from plugin.base.integration.SettingsMixin import SettingsMixin
from plugin.base.integration.UrlsMixin import UrlsMixin
from plugin.base.integration.ValidationMixin import ValidationMixin
from plugin.base.label.mixins import LabelPrintingMixin
from plugin.base.locate.mixins import LocateMixin

__all__ = [
    'APICallMixin',
    'AppMixin',
    'CurrencyExchangeMixin',
    'EventMixin',
    'LabelPrintingMixin',
    'NavigationMixin',
    'ReportMixin',
    'ScheduleMixin',
    'SettingsContentMixin',
    'SettingsMixin',
    'UrlsMixin',
    'PanelMixin',
    'ActionMixin',
    'BarcodeMixin',
    'SupplierBarcodeMixin',
    'LocateMixin',
    'ValidationMixin',
    'SingleNotificationMethod',
    'BulkNotificationMethod',
]
