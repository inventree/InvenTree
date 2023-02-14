"""Django views for interacting with supplier plugins."""

from django.views.generic import TemplateView

from InvenTree.views import InvenTreeRoleMixin


class PluginSupplierIndex(InvenTreeRoleMixin, TemplateView):
    """View for displaying supplier index page."""

    template_name = 'plugin/supplier/index.html'
