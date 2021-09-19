from plugins.integration.integration import *

from django.http import HttpResponse
from django.utils.translation import ugettext_lazy as _


class SimpleIntegrationPlugin(SettingsMixin, UrlsMixin, IntegrationPlugin):
    """
    An basic integration plugin
    """

    PLUGIN_NAME = "SimpleIntegrationPlugin"

    def view_test(self, request):
        return HttpResponse(f'Hi there {request.user.username} this works')

    def setup_urls(self):
        he = [
            url(r'^he/', self.view_test, name='he'),
            url(r'^ha/', self.view_test, name='ha'),
        ]

        return [
            url(r'^hi/', self.view_test, name='hi'),
            url(r'^ho/', include(he), name='ho'),
        ]

    SETTINGS = {
        'PO_FUNCTION_ENABLE': {
            'name': _('Enable PO'),
            'description': _('Enable PO functionality in InvenTree interface'),
            'default': True,
            'validator': bool,
        },
    }


class OtherIntegrationPlugin(UrlsMixin, IntegrationPlugin):
    """
    An basic integration plugin
    """

    PLUGIN_NAME = "OtherIntegrationPlugin"

    # @cls_login_required()
    def view_test(self, request):
        return HttpResponse(f'Hi there {request.user.username} this works')

    def setup_urls(self):
        he = [
            url(r'^he/', self.view_test, name='he'),
            url(r'^ha/', self.view_test, name='ha'),
        ]

        return [
            url(r'^hi/', self.view_test, name='hi'),
            url(r'^ho/', include(he), name='ho'),
        ]
