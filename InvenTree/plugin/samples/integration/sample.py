"""
Sample implementations for IntegrationPlugin
"""

from plugin import IntegrationPluginBase
from plugin.mixins import AppMixin, SettingsMixin, UrlsMixin, NavigationMixin

from django.http import HttpResponse
from django.utils.translation import gettext_lazy as _
from django.urls import include, re_path


class SampleIntegrationPlugin(AppMixin, SettingsMixin, UrlsMixin, NavigationMixin, IntegrationPluginBase):
    """
    A full integration plugin example
    """

    PLUGIN_NAME = "SampleIntegrationPlugin"
    PLUGIN_SLUG = "sample"
    PLUGIN_TITLE = "Sample Plugin"

    NAVIGATION_TAB_NAME = "Sample Nav"
    NAVIGATION_TAB_ICON = 'fas fa-plus'

    def view_test(self, request):
        """very basic view"""
        return HttpResponse(f'Hi there {request.user.username} this works')

    def setup_urls(self):
        he_urls = [
            re_path(r'^he/', self.view_test, name='he'),
            re_path(r'^ha/', self.view_test, name='ha'),
        ]

        return [
            re_path(r'^hi/', self.view_test, name='hi'),
            re_path(r'^ho/', include(he_urls), name='ho'),
        ]

    SETTINGS = {
        'PO_FUNCTION_ENABLE': {
            'name': _('Enable PO'),
            'description': _('Enable PO functionality in InvenTree interface'),
            'default': True,
            'validator': bool,
        },
        'API_KEY': {
            'name': _('API Key'),
            'description': _('Key required for accessing external API'),
        },
        'NUMERICAL_SETTING': {
            'name': _('Numerical'),
            'description': _('A numerical setting'),
            'validator': int,
            'default': 123,
        },
        'CHOICE_SETTING': {
            'name': _("Choice Setting"),
            'description': _('A setting with multiple choices'),
            'choices': [
                ('A', 'Anaconda'),
                ('B', 'Bat'),
                ('C', 'Cat'),
                ('D', 'Dog'),
            ],
            'default': 'A',
        },
        'SELECT_COMPANY': {
            'name': 'Company',
            'description': 'Select a company object from the database',
            'model': 'company.company',
        },
        'SELECT_PART': {
            'name': 'Part',
            'description': 'Select a part object from the database',
            'model': 'part.part',
        },
    }

    NAVIGATION = [
        {'name': 'SampleIntegration', 'link': 'plugin:sample:hi'},
    ]
