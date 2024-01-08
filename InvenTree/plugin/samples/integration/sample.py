"""Sample implementations for IntegrationPlugin."""

import json

from django.core.exceptions import ValidationError
from django.http import HttpResponse
from django.urls import include, path, re_path
from django.utils.translation import gettext_lazy as _

from plugin import InvenTreePlugin
from plugin.mixins import AppMixin, NavigationMixin, SettingsMixin, UrlsMixin


def validate_json(value):
    """Example validator for json input."""
    try:
        json.loads(value)
    except Exception as e:
        raise ValidationError(str(e))


class SampleIntegrationPlugin(AppMixin, SettingsMixin, UrlsMixin, NavigationMixin, InvenTreePlugin):
    """A full plugin example."""

    NAME = "SampleIntegrationPlugin"
    SLUG = "sample"
    TITLE = "Sample Plugin"

    NAVIGATION_TAB_NAME = "Sample Nav"
    NAVIGATION_TAB_ICON = 'fas fa-plus'

    def view_test(self, request):
        """Very basic view."""
        return HttpResponse(f'Hi there {request.user.username} this works')

    def setup_urls(self):
        """Urls that are exposed by this plugin."""
        he_urls = [
            re_path(r'^he/', self.view_test, name='he'),
            re_path(r'^ha/', self.view_test, name='ha'),
        ]

        return [
            re_path(r'^hi/', self.view_test, name='hi'),
            path('ho/', include(he_urls), name='ho'),
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
            'required': True,
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
        'PROTECTED_SETTING': {
            'name': 'Protected Setting',
            'description': 'A protected setting, hidden from the UI',
            'default': 'ABC-123',
            'protected': True,
        },
        'VALIDATOR_SETTING': {
            'name': 'JSON validator Setting',
            'description': 'A setting using a JSON validator',
            'validator': validate_json,
        }
    }

    NAVIGATION = [
        {'name': 'SampleIntegration', 'link': 'plugin:sample:hi'},
    ]
