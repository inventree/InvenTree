"""Plugin mixin classes."""

import json as json_pkg
import logging

import requests

import part.models
import stock.models
from InvenTree.helpers import generateTestKey
from plugin.helpers import (MixinNotImplementedError, render_template,
                            render_text)

logger = logging.getLogger('inventree')


class ValidationMixin:
    """Mixin class that allows custom validation for various parts of InvenTree

    Custom generation and validation functionality can be provided for:

    - Part names
    - Part IPN (internal part number) values
    - Part parameter values
    - Serial numbers
    - Batch codes

    Notes:
    - Multiple ValidationMixin plugins can be used simultaneously
    - The stub methods provided here generally return None (null value).
    - The "first" plugin to return a non-null value for a particular method "wins"
    - In the case of "validation" functions, all loaded plugins are checked until an exception is thrown

    Implementing plugins may override any of the following methods which are of interest.

    For 'validation' methods, there are three 'acceptable' outcomes:
    - The method determines that the value is 'invalid' and raises a django.core.exceptions.ValidationError
    - The method passes and returns None (the code then moves on to the next plugin)
    - The method passes and returns True (and no subsequent plugins are checked)

    """

    class MixinMeta:
        """Metaclass for this mixin"""
        MIXIN_NAME = "Validation"

    def __init__(self):
        """Register the mixin"""
        super().__init__()
        self.add_mixin('validation', True, __class__)

    def validate_part_name(self, name: str, part: part.models.Part):
        """Perform validation on a proposed Part name

        Arguments:
            name: The proposed part name
            part: The part instance we are validating against

        Returns:
            None or True (refer to class docstring)

        Raises:
            ValidationError if the proposed name is objectionable
        """
        return None

    def validate_part_ipn(self, ipn: str, part: part.models.Part):
        """Perform validation on a proposed Part IPN (internal part number)

        Arguments:
            ipn: The proposed part IPN
            part: The Part instance we are validating against

        Returns:
            None or True (refer to class docstring)

        Raises:
            ValidationError if the proposed IPN is objectionable
        """
        return None

    def validate_batch_code(self, batch_code: str, item: stock.models.StockItem):
        """Validate the supplied batch code

        Arguments:
            batch_code: The proposed batch code (string)
            item: The StockItem instance we are validating against

        Returns:
            None or True (refer to class docstring)

        Raises:
            ValidationError if the proposed batch code is objectionable
        """
        return None

    def generate_batch_code(self):
        """Generate a new batch code

        Returns:
            A new batch code (string) or None
        """
        return None

    def validate_serial_number(self, serial: str, part: part.models.Part):
        """Validate the supplied serial number.

        Arguments:
            serial: The proposed serial number (string)
            part: The Part instance for which this serial number is being validated

        Returns:
            None or True (refer to class docstring)

        Raises:
            ValidationError if the proposed serial is objectionable
        """
        return None

    def convert_serial_to_int(self, serial: str):
        """Convert a serial number (string) into an integer representation.

        This integer value is used for efficient sorting based on serial numbers.

        A plugin which implements this method can either return:

        - An integer based on the serial string, according to some algorithm
        - A fixed value, such that serial number sorting reverts to the string representation
        - None (null value) to let any other plugins perform the converrsion

        Note that there is no requirement for the returned integer value to be unique.

        Arguments:
            serial: Serial value (string)

        Returns:
            integer representation of the serial number, or None
        """
        return None

    def increment_serial_number(self, serial: str):
        """Return the next sequential serial based on the provided value.

        A plugin which implements this method can either return:

        - A string which represents the "next" serial number in the sequence
        - None (null value) if the next value could not be determined

        Arguments:
            serial: Current serial value (string)
        """
        return None

    def validate_part_parameter(self, parameter, data):
        """Validate a parameter value.

        Arguments:
            parameter: The parameter we are validating
            data: The proposed parameter value

        Returns:
            None or True (refer to class docstring)

        Raises:
            ValidationError if the proposed parameter value is objectionable
        """
        pass


class NavigationMixin:
    """Mixin that enables custom navigation links with the plugin."""

    NAVIGATION_TAB_NAME = None
    NAVIGATION_TAB_ICON = "fas fa-question"

    class MixinMeta:
        """Meta options for this mixin."""

        MIXIN_NAME = 'Navigation Links'

    def __init__(self):
        """Register mixin."""
        super().__init__()
        self.add_mixin('navigation', 'has_naviation', __class__)
        self.navigation = self.setup_navigation()

    def setup_navigation(self):
        """Setup navigation links for this plugin."""
        nav_links = getattr(self, 'NAVIGATION', None)
        if nav_links:
            # check if needed values are configured
            for link in nav_links:
                if False in [a in link for a in ('link', 'name', )]:
                    raise MixinNotImplementedError('Wrong Link definition', link)
        return nav_links

    @property
    def has_naviation(self):
        """Does this plugin define navigation elements."""
        return bool(self.navigation)

    @property
    def navigation_name(self):
        """Name for navigation tab."""
        name = getattr(self, 'NAVIGATION_TAB_NAME', None)
        if not name:
            name = self.human_name
        return name

    @property
    def navigation_icon(self):
        """Icon-name for navigation tab."""
        return getattr(self, 'NAVIGATION_TAB_ICON', "fas fa-question")


class APICallMixin:
    """Mixin that enables easier API calls for a plugin.

    Steps to set up:
    1. Add this mixin before (left of) SettingsMixin and PluginBase
    2. Add two settings for the required url and token/password (use `SettingsMixin`)
    3. Save the references to keys of the settings in `API_URL_SETTING` and `API_TOKEN_SETTING`
    4. (Optional) Set `API_TOKEN` to the name required for the token by the external API - Defaults to `Bearer`
    5. (Optional) Override the `api_url` property method if the setting needs to be extended
    6. (Optional) Override `api_headers` to add extra headers (by default the token and Content-Type are contained)
    7. Access the API in you plugin code via `api_call`

    Example:
    ```
    from plugin import InvenTreePlugin
    from plugin.mixins import APICallMixin, SettingsMixin


    class SampleApiCallerPlugin(APICallMixin, SettingsMixin, InvenTreePlugin):
        '''
        A small api call sample
        '''
        NAME = "Sample API Caller"

        SETTINGS = {
            'API_TOKEN': {
                'name': 'API Token',
                'protected': True,
            },
            'API_URL': {
                'name': 'External URL',
                'description': 'Where is your API located?',
                'default': 'reqres.in',
            },
        }
        API_URL_SETTING = 'API_URL'
        API_TOKEN_SETTING = 'API_TOKEN'

        def get_external_url(self):
            '''
            returns data from the sample endpoint
            '''
            return self.api_call('api/users/2')
    ```
    """
    API_METHOD = 'https'
    API_URL_SETTING = None
    API_TOKEN_SETTING = None

    API_TOKEN = 'Bearer'

    class MixinMeta:
        """Meta options for this mixin."""
        MIXIN_NAME = 'API calls'

    def __init__(self):
        """Register mixin."""
        super().__init__()
        self.add_mixin('api_call', 'has_api_call', __class__)

    @property
    def has_api_call(self):
        """Is the mixin ready to call external APIs?"""
        if not bool(self.API_URL_SETTING):
            raise MixinNotImplementedError("API_URL_SETTING must be defined")
        if not bool(self.API_TOKEN_SETTING):
            raise MixinNotImplementedError("API_TOKEN_SETTING must be defined")
        return True

    @property
    def api_url(self):
        """Base url path."""
        return f'{self.API_METHOD}://{self.get_setting(self.API_URL_SETTING)}'

    @property
    def api_headers(self):
        """Returns the default headers for requests with api_call.

        Contains a header with the key set in `API_TOKEN` for the plugin it `API_TOKEN_SETTING` is defined.
        Check the mixin class docstring for a full example.
        """
        headers = {'Content-Type': 'application/json'}
        if getattr(self, 'API_TOKEN_SETTING'):
            token = self.get_setting(self.API_TOKEN_SETTING)

            if token:
                headers[self.API_TOKEN] = token
                headers['Authorization'] = f"{self.API_TOKEN} {token}"

        return headers

    def api_build_url_args(self, arguments: dict) -> str:
        """Returns an encoded path for the provided dict."""
        groups = []
        for key, val in arguments.items():
            groups.append(f'{key}={",".join([str(a) for a in val])}')
        return f'?{"&".join(groups)}'

    def api_call(self, endpoint: str, method: str = 'GET', url_args: dict = None, data=None, json=None, headers: dict = None, simple_response: bool = True, endpoint_is_url: bool = False):
        """Do an API call.

        Simplest call example:
        ```python
        self.api_call('hello')
        ```
        Will call the `{base_url}/hello` with a GET request and - if set - the token for this plugin.

        Args:
            endpoint (str): Path to current endpoint. Either the endpoint or the full or if the flag is set
            method (str, optional): HTTP method that should be uses - capitalized. Defaults to 'GET'.
            url_args (dict, optional): arguments that should be appended to the url. Defaults to None.
            data (Any, optional): Data that should be transmitted in the body - url-encoded. Defaults to None.
            json (Any, optional): Data that should be transmitted in the body - must be JSON serializable. Defaults to None.
            headers (dict, optional): Headers that should be used for the request. Defaults to self.api_headers.
            simple_response (bool, optional): Return the response as JSON. Defaults to True.
            endpoint_is_url (bool, optional): The provided endpoint is the full url - do not use self.api_url as base. Defaults to False.

        Returns:
            Response
        """
        if url_args:
            endpoint += self.api_build_url_args(url_args)

        if headers is None:
            headers = self.api_headers

        if endpoint_is_url:
            url = endpoint
        else:

            if endpoint.startswith('/'):
                endpoint = endpoint[1:]

            url = f'{self.api_url}/{endpoint}'

        # build kwargs for call
        kwargs = {
            'url': url,
            'headers': headers,
        }

        if data and json:
            raise ValueError('You can either pass `data` or `json` to this function.')

        if json:
            kwargs['data'] = json_pkg.dumps(json)

        if data:
            kwargs['data'] = data

        # run command
        response = requests.request(method, **kwargs)

        # return
        if simple_response:
            return response.json()
        return response


class PanelMixin:
    """Mixin which allows integration of custom 'panels' into a particular page.

    The mixin provides a number of key functionalities:

    - Adds an (initially hidden) panel to the page
    - Allows rendering of custom templated content to the panel
    - Adds a menu item to the 'navbar' on the left side of the screen
    - Allows custom javascript to be run when the panel is initially loaded

    The PanelMixin class allows multiple panels to be returned for any page,
    and also allows the plugin to return panels for many different pages.

    Any class implementing this mixin must provide the 'get_custom_panels' method,
    which dynamically returns the custom panels for a particular page.

    This method is provided with:

    - view : The View object which is being rendered
    - request : The HTTPRequest object

    Note that as this is called dynamically (per request),
    then the actual panels returned can vary depending on the particular request or page

    The 'get_custom_panels' method must return a list of dict objects, each with the following keys:

    - title : The title of the panel, to appear in the sidebar menu
    - description : Extra descriptive text (optional)
    - icon : The icon to appear in the sidebar menu
    - content : The HTML content to appear in the panel, OR
    - content_template : A template file which will be rendered to produce the panel content
    - javascript : The javascript content to be rendered when the panel is loade, OR
    - javascript_template : A template file which will be rendered to produce javascript

    e.g.

    {
        'title': "Updates",
        'description': "Latest updates for this part",
        'javascript': 'alert("You just loaded this panel!")',
        'content': '<b>Hello world</b>',
    }
    """

    class MixinMeta:
        """Meta for mixin."""

        MIXIN_NAME = 'Panel'

    def __init__(self):
        """Register mixin."""
        super().__init__()
        self.add_mixin('panel', True, __class__)

    def get_custom_panels(self, view, request):
        """This method *must* be implemented by the plugin class."""
        raise MixinNotImplementedError(f"{__class__} is missing the 'get_custom_panels' method")

    def get_panel_context(self, view, request, context):
        """Build the context data to be used for template rendering.

        Custom class can override this to provide any custom context data.

        (See the example in "custom_panel_sample.py")
        """
        # Provide some standard context items to the template for rendering
        context['plugin'] = self
        context['request'] = request
        context['user'] = getattr(request, 'user', None)
        context['view'] = view

        try:
            context['object'] = view.get_object()
        except AttributeError:  # pragma: no cover
            pass

        return context

    def render_panels(self, view, request, context):
        """Get panels for a view.

        Args:
            view: Current view context
            request: Current request for passthrough
            context: Rendering context

        Returns:
            Array of panels
        """

        panels = []

        # Construct an updated context object for template rendering
        ctx = self.get_panel_context(view, request, context)

        custom_panels = self.get_custom_panels(view, request) or []

        for panel in custom_panels:

            content_template = panel.get('content_template', None)
            javascript_template = panel.get('javascript_template', None)

            if content_template:
                # Render content template to HTML
                panel['content'] = render_template(self, content_template, ctx)
            else:
                # Render content string to HTML
                panel['content'] = render_text(panel.get('content', ''), ctx)

            if javascript_template:
                # Render javascript template to HTML
                panel['javascript'] = render_template(self, javascript_template, ctx)
            else:
                # Render javascript string to HTML
                panel['javascript'] = render_text(panel.get('javascript', ''), ctx)

            # Check for required keys
            required_keys = ['title', 'content']

            if any(key not in panel for key in required_keys):
                logger.warning(f"Custom panel for plugin {__class__} is missing a required parameter")
                continue

            # Add some information on this plugin
            panel['plugin'] = self
            panel['slug'] = self.slug

            # Add a 'key' for the panel, which is mostly guaranteed to be unique
            panel['key'] = generateTestKey(self.slug + panel.get('title', 'panel'))

            panels.append(panel)

        return panels


class SettingsContentMixin:
    """Mixin which allows integration of custom HTML content into a plugins settings page.

    The 'get_settings_content' method must return the HTML content to appear in the section
    """

    class MixinMeta:
        """Meta for mixin."""

        MIXIN_NAME = 'SettingsContent'

    def __init__(self):
        """Register mixin."""
        super().__init__()
        self.add_mixin('settingscontent', True, __class__)

    def get_settings_content(self, view, request):
        """This method *must* be implemented by the plugin class."""
        raise MixinNotImplementedError(f"{__class__} is missing the 'get_settings_content' method")
