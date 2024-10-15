"""UserInterfaceMixin class definition.

Allows integration of custom UI elements into the React user interface.
"""

import logging
from typing import Literal, TypedDict

from rest_framework.request import Request

logger = logging.getLogger('inventree')


# List of supported feature types
FeatureType = Literal[
    'dashboard',  # Custom dashboard items
    'panel',  # Custom panels
    'template_editor',  # Custom template editor
    'template_preview',  # Custom template preview
]


class UIFeature(TypedDict):
    """Base type definition for a ui feature.

    Attributes:
        feature_type: The feature type (required, see documentation for all available types)
        options: Feature options (required, see documentation for all available options for each type)
        source: The source of the feature (required, path to a JavaScript file).
    """

    feature_type: FeatureType
    options: dict
    source: str


class CustomPanelOptions(TypedDict):
    """Options type definition for a custom panel.

    Attributes:
        icon: The icon of the panel (optional, must be a valid icon identifier).
    """

    icon: str
    content: str
    source: str


class CustomDashboardItemOptions(TypedDict):
    """Options type definition for a custom dashboard item.

    Attributes:
        description: The long-form description of the dashboard item (required, human readable).
        width: The minimum width of the dashboard item (integer, defaults to 2)
        height: The minimum height of the dashboard item (integer, defaults to 2)
    """

    description: str
    width: int
    height: int
    source: str


class UserInterfaceMixin:
    """Plugin mixin class which handles injection of custom elements into the front-end interface.

    - All content is accessed via the API, as requested by the user interface.
    - This means that content can be dynamically generated, based on the current state of the system.
    """

    class MixinMeta:
        """Metaclass for this plugin mixin."""

        MIXIN_NAME = 'ui'

    def __init__(self):
        """Register mixin."""
        super().__init__()
        self.add_mixin('ui', True, __class__)  # type: ignore

    def get_ui_features(
        self, feature_type: FeatureType, context: dict, request: Request
    ) -> list[UIFeature]:
        """Return a list of custom features to be injected into the UI.

        Arguments:
            feature_type: The type of feature being requested
            context: Additional context data provided by the UI (query parameters)
            request: HTTPRequest object (including user information)

        Returns:
            list: A list of custom UIFeature dicts to be injected into the UI
        """
        print('get_ui_features:', feature_type, context, request)

        if feature_type == 'dashboard':
            return self.get_ui_dashboard_items(request, context=context)

        if feature_type == 'panel':
            return self.get_ui_panels()

        # Default implementation returns an empty list
        return []

    def get_ui_panels(
        self, request: Request, context: dict, **kwargs
    ) -> list[UIFeature]:
        """Return a list of custom panels to be injected into the UI.

        Args:
            request: HTTPRequest object (including user information)



        Returns:
            list: A list of custom panels to be injected into the UI
        """
        # Default implementation returns an empty list
        return []

    def get_ui_dashboard_items(
        self, request: Request, context: dict, **kwargs
    ) -> list[UIFeature]:
        """Return a list of custom dashboard items to be injected into the UI.

        Args:
            request: HTTPRequest object (including user information)

        Returns:
            list: A list of custom dashboard items to be injected into the UI
        """
        # Default implementation returns an empty list
        return []
