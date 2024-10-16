"""UserInterfaceMixin class definition.

Allows integration of custom UI elements into the React user interface.
"""

import logging
from typing import Literal, TypedDict

from rest_framework.request import Request

logger = logging.getLogger('inventree')


class CustomPanel(TypedDict):
    """Type definition for a custom panel.

    Attributes:
        name: The name of the panel (required, used as a DOM identifier).
        label: The label of the panel (required, human readable).
        icon: The icon of the panel (optional, must be a valid icon identifier).
        content: The content of the panel (optional, raw HTML).
        context: Optional context data (dict / JSON) which will be passed to the front-end rendering function
        source: The source of the panel (optional, path to a JavaScript file).
    """

    name: str
    label: str
    icon: str
    content: str
    context: dict
    source: str


FeatureType = Literal['template_editor', 'template_preview']


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

    def get_ui_panels(
        self, instance_type: str, instance_id: int, request: Request, **kwargs
    ) -> list[CustomPanel]:
        """Return a list of custom panels to be injected into the UI.

        Args:
            instance_type: The type of object being viewed (e.g. 'part')
            instance_id: The ID of the object being viewed (e.g. 123)
            request: HTTPRequest object (including user information)

        Returns:
            list: A list of custom panels to be injected into the UI

        - The returned list should contain a dict for each custom panel to be injected into the UI:
        - The following keys can be specified:
        {
            'name': 'panel_name',  # The name of the panel (required, must be unique)
            'label': 'Panel Title',  # The title of the panel (required, human readable)
            'icon': 'icon-name',  # Icon name (optional, must be a valid icon identifier)
            'content': '<p>Panel content</p>',  # HTML content to be rendered in the panel (optional)
            'context': {'key': 'value'},  # Context data to be passed to the front-end rendering function (optional)
            'source': 'static/plugin/panel.js',  # Path to a JavaScript file to be loaded (optional)
        }

        - Either 'source' or 'content' must be provided

        """
        # Default implementation returns an empty list
        return []

    def get_ui_features(
        self, feature_type: FeatureType, context: dict, request: Request
    ) -> list[UIFeature]:
        """Return a list of custom features to be injected into the UI.

        Arguments:
            feature_type: The type of feature being requested
            context: Additional context data provided by the UI
            request: HTTPRequest object (including user information)

        Returns:
            list: A list of custom UIFeature dicts to be injected into the UI
        """
        # Default implementation returns an empty list
        return []
