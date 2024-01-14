"""Mixin class for making calls to an external API."""

import json as json_pkg
import logging

import requests

from plugin.helpers import MixinNotImplementedError

logger = logging.getLogger('inventree')


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
            raise MixinNotImplementedError('API_URL_SETTING must be defined')
        if not bool(self.API_TOKEN_SETTING):
            raise MixinNotImplementedError('API_TOKEN_SETTING must be defined')
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
        if getattr(self, 'API_TOKEN_SETTING', None):
            token = self.get_setting(self.API_TOKEN_SETTING)

            if token:
                headers[self.API_TOKEN] = token
                headers['Authorization'] = f'{self.API_TOKEN} {token}'

        return headers

    def api_build_url_args(self, arguments: dict) -> str:
        """Returns an encoded path for the provided dict."""
        groups = []
        for key, val in arguments.items():
            groups.append(f'{key}={",".join([str(a) for a in val])}')
        return f'?{"&".join(groups)}'

    def api_call(
        self,
        endpoint: str,
        method: str = 'GET',
        url_args: dict = None,
        data=None,
        json=None,
        headers: dict = None,
        simple_response: bool = True,
        endpoint_is_url: bool = False,
    ):
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
        kwargs = {'url': url, 'headers': headers}

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
