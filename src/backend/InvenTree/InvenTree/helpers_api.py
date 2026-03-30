"""Helpers for InvenTrees way of using drf viewset."""

from rest_framework import mixins, routers, viewsets

from InvenTree.api import BulkDeleteViewsetMixin


class RetrieveUpdateDestroyModelViewSet(
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
