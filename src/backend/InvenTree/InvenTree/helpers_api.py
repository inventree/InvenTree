"""Helpers for InvenTrees way of using drf viewset."""

from rest_framework import mixins, routers, viewsets
from rest_framework.settings import api_settings

from InvenTree.api import BulkDeleteViewsetMixin
from InvenTree.mixins import CleanMixin, CleanUpdateOnlyMixin


class ViewSetCleanMixin:
    """Mixin class which cleans inputs using nh3."""

    def get_success_headers(self, data):
        """Return the success headers for a create/update response."""
        try:
            return {'Location': str(data[api_settings.URL_FIELD_NAME])}
        except (TypeError, KeyError):
            return {}


class CleanModelViewSet(CleanMixin, ViewSetCleanMixin, viewsets.ModelViewSet):
    """Viewset which provides 'retrieve', 'create', 'update', 'destroy' and 'list' actions."""


class RetrieveUpdateDestroyModelViewSet(
    CleanUpdateOnlyMixin,
    ViewSetCleanMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    """Viewset which provides 'retrieve', 'update', 'destroy' and 'list' actions."""


class RetrieveDestroyModelViewSet(
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    """Viewset which provides 'retrieve', 'destroy' and 'list' actions."""


class InvenTreeApiRouter(routers.SimpleRouter):
    """Custom router which adds various specific functions.

    Currently adds the following features:
    - support for bulk delete operations
    """

    def get_routes(self, viewset):
        """Override the default get_routes method to add bulk delete support."""
        routes = super().get_routes(viewset)

        if issubclass(viewset, BulkDeleteViewsetMixin):
            list_route = next(
                (route for route in routes if route.mapping.get('get') == 'list'), None
            )
            list_route.mapping['delete'] = 'bulk_delete'

        return routes

    def get_default_basename(self, viewset):
        """Extract the default base name from the viewset."""
        basename = super().get_default_basename(viewset)
        return 'api-' + basename
