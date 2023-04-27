"""Utility class to enable simpler imports."""

from common.notifications import (BulkNotificationMethod,
                                  SingleNotificationMethod)

from ..base.action.mixins import ActionMixin
from ..base.barcodes.mixins import BarcodeMixin
from ..base.event.mixins import EventMixin
from ..base.integration.AppMixin import AppMixin
from ..base.integration.mixins import (APICallMixin, NavigationMixin,
                                       PanelMixin, SettingsContentMixin,
                                       ValidationMixin)
from ..base.integration.ReportMixin import ReportMixin
from ..base.integration.ScheduleMixin import ScheduleMixin
from ..base.integration.SettingsMixin import SettingsMixin
from ..base.integration.UrlsMixin import UrlsMixin
from ..base.label.mixins import LabelPrintingMixin
from ..base.locate.mixins import LocateMixin

__all__ = [
    'APICallMixin',
    'AppMixin',
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
    'LocateMixin',
    'ValidationMixin',
    'SingleNotificationMethod',
    'BulkNotificationMethod',
]
