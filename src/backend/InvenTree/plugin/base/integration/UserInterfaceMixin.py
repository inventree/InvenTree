"""UserInterfaceMixin class definition.

Allows integration of custom UI elements into the React user interface.
"""

import logging

from rest_framework.request import Request

logger = logging.getLogger('inventree')


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
        self.add_mixin('ui', True, __class__)

    def get_custom_panels(
        self, instance_type: str, instance_id: int, request: Request
    ) -> list:
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
            'name': 'panel_name',  # The name of the panel (required, must be a valid DOM ID)
            'label': 'Panel Title',  # The title of the panel (required, human readable)
            'icon': 'icon-name',  # Icon name (optional, must be a valid icon identifier)
            'content': 'Panel content',  # Raw content of the panel (optional)
            'source': 'static/plugin/panel.js',  # Path to a JavaScript file to be loaded (optional)
            'context': {'key': 'value'},  # Context data (JSON) to be passed to the client side rendering (optional)
        }

        - Either 'source' or 'content' must be provided

        """
        # Default implementation returns an empty list
        return []
