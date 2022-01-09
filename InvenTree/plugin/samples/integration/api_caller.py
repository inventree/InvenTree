"""
Sample plugin for calling an external API
"""
from plugin import IntegrationPluginBase
from plugin.mixins import APICallMixin, SettingsMixin


class SampleApiCallerPlugin(APICallMixin, SettingsMixin, IntegrationPluginBase):
    """
    A small api call sample
    """
    PLUGIN_NAME = "Sample API Caller"

    SETTINGS = {
        'API_TOKEN': {
            'name': 'API Token',
            'protected': True,
        },
        'API_URL': {
            'name': 'External URL',
            'description': 'Where is your API located?',
            'default': 'https://reqres.in',
        },
    }
    API_URL_SETTING = 'API_URL'
    API_TOKEN_SETTING = 'API_TOKEN'

    def get_external_url(self):
        """
        returns data from the sample endpoint
        """
        return self.api_call('api/users/2')
