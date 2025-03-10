"""UserInterfaceMixin class definition.

Allows integration of custom UI elements into the React user interface.
"""

from typing import Literal, TypedDict

import structlog
from rest_framework.request import Request

logger = structlog.get_logger('inventree')


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
        key: The key of the feature (required, must be a unique identifier)
        title: The title of the feature (required, human readable)
        description: The long-form description of the feature (optional, human readable)
        icon: The icon of the feature (optional, must be a valid icon identifier)
        feature_type: The feature type (required, see documentation for all available types)
        options: Feature options (required, see documentation for all available options for each type)
        context: Additional context data to be passed to the rendering function (optional, dict)
        source: The source of the feature (required, path to a JavaScript file, with optional function name).
    """

    key: str
    title: str
    description: str
    icon: str
    feature_type: FeatureType
    options: dict
    context: dict
    source: str


class CustomPanelOptions(TypedDict):
    """Options type definition for a custom panel.

    Attributes:
        icon: The icon of the panel (optional, must be a valid icon identifier).
    """


class CustomDashboardItemOptions(TypedDict):
    """Options type definition for a custom dashboard item.

    Attributes:
        width: The minimum width of the dashboard item (integer, defaults to 2)
        height: The minimum height of the dashboard item (integer, defaults to 2)
    """

    width: int
    height: int


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
        self, feature_type: FeatureType, context: dict, request: Request, **kwargs
    ) -> list[UIFeature]:
        """Return a list of custom features to be injected into the UI.

        Arguments:
            feature_type: The type of feature being requested
            context: Additional context data provided by the UI (query parameters)
            request: HTTPRequest object (including user information)

        Returns:
            list: A list of custom UIFeature dicts to be injected into the UI

        """
        feature_map = {
            'dashboard': self.get_ui_dashboard_items,
            'panel': self.get_ui_panels,
            'template_editor': self.get_ui_template_editors,
            'template_preview': self.get_ui_template_previews,
        }

        if feature_type in feature_map:
            return feature_map[feature_type](request, context, **kwargs)
        else:
            logger.warning(f'Invalid feature type: {feature_type}')
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

    def get_ui_template_editors(
        self, request: Request, context: dict, **kwargs
    ) -> list[UIFeature]:
        """Return a list of custom template editors to be injected into the UI.

        Args:
            request: HTTPRequest object (including user information)

        Returns:
            list: A list of custom template editors to be injected into the UI
        """
        # Default implementation returns an empty list
        return []

    def get_ui_template_previews(
        self, request: Request, context: dict, **kwargs
    ) -> list[UIFeature]:
        """Return a list of custom template previews to be injected into the UI.

        Args:
            request: HTTPRequest object (including user information)

        Returns:
            list: A list of custom template previews to be injected into the UI
        """
        # Default implementation returns an empty list
        return []
