"""Types for settings."""

import sys
from collections.abc import Callable
from typing import Any, TypedDict

if sys.version_info >= (3, 11):
    from typing import NotRequired  # pragma: no cover
else:

    class NotRequired:  # pragma: no cover
        """NotRequired type helper is only supported with Python 3.11+."""

        def __class_getitem__(cls, item):
            """Return the item."""
            return item


class SettingsKeyType(TypedDict, total=False):
    """Type definitions for a SettingsKeyType.

    Attributes:
        name: Translatable string name of the setting (required)
        description: Translatable string description of the setting (required)
        units: Units of the particular setting (optional)
        validator: Validation function/list of functions for the setting (optional, default: None, e.g: bool, int, str, MinValueValidator, ...)
        default: Default value or function that returns default value (optional)
        choices: Function that returns or value of list[tuple[str: key, str: display value]] (optional)
        hidden: Hide this setting from settings page (optional)
        before_save: Function that gets called after save with *args, **kwargs (optional)
        after_save: Function that gets called after save with *args, **kwargs (optional)
        protected: Protected values are not returned to the client, instead "***" is returned (optional, default: False)
        required: Is this setting required to work, can be used in combination with .check_all_settings(...) (optional, default: False)
        model: Auto create a dropdown menu to select an associated model instance (e.g. 'company.company', 'auth.user' and 'auth.group' are possible too, optional)
    """

    name: str
    description: str
    units: str
    validator: Callable | list[Callable] | tuple[Callable]
    default: Callable | Any
    choices: list[tuple[str, str]] | Callable[[], list[tuple[str, str]]]
    hidden: bool
    before_save: Callable[..., None]
    after_save: Callable[..., None]
    protected: bool
    required: bool
    model: str


class InvenTreeSettingsKeyType(SettingsKeyType):
    """InvenTreeSettingsKeyType has additional properties only global settings support.

    Attributes:
        requires_restart: If True, a server restart is required after changing the setting
    """

    requires_restart: NotRequired[bool]
