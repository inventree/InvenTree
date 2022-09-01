"""APIs for supplier plugins."""
from dataclasses import dataclass

from rest_framework import permissions

from InvenTree.mixins import ListAPI
from plugin import registry
from plugin.base.supplier.mixins import SearchRunResult


@dataclass()
class DummySerializer:
    """Class that acts as a dump shell holding data so that a list can be passed to querset functions."""
    data: list


class PluginSearch(ListAPI):
    """Endpoint for search using a supplier plugin."""

    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Get dataset from plugin."""
        plg = registry.get_plugin(self.request.GET.get('plugin'))
        rslt: SearchRunResult = plg.search_action(term=self.request.GET.get('search'))

        # TODO save results

        return [{
            'id': a.id,
            'title': a.title,
            'description': a.description,
            'link': a.link,
        } for a in rslt.results]

    def get_serializer(self, *args, **kwargs):
        """Returns dummy data."""
        return DummySerializer(data=args[0])
