from plugins.integration.integration import *

from django.http import HttpResponse
from django.utils.translation import ugettext_lazy as _


class NoIntegrationPlugin(IntegrationPlugin):
    """
    An basic integration plugin
    """

    PLUGIN_NAME = "NoIntegrationPlugin"


class WrongIntegrationPlugin(UrlsMixin, IntegrationPlugin):
    """
    An basic integration plugin
    """

    PLUGIN_NAME = "WrongIntegrationPlugin"
