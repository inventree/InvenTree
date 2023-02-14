"""APIs for supplier plugins."""
from dataclasses import dataclass

from django.utils.translation import gettext_lazy as _

from rest_framework import permissions, serializers

from common.models import WebConnection
from InvenTree.mixins import CreateAPI, ListAPI
from part.models import PartCategory
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


class ImportPluginSupplierPartSerializer(serializers.Serializer):
    """DRF serializer for importing a part from a supplier plugin."""

    connection = serializers.PrimaryKeyRelatedField(
        queryset=WebConnection.objects.all(),
        many=False,
        required=True,
        label=_('Vendor Connection'),
    )
    reference = serializers.CharField(
        required=True,
        label=_('Reference'),
    )
    category = serializers.PrimaryKeyRelatedField(queryset=PartCategory.objects.all())

    def save(self):
        """Save the serializer data. This tries to import the part."""
        build = self.context['build']

        data = self.validated_data

        build.unallocateStock(
            bom_item=data['bom_item'],
            output=data['output']
        )


class ImportPluginSupplierPartView(CreateAPI):
    """API endpoint for importing a part from a supplier plugin."""
    permission_classes = [
        permissions.IsAuthenticated
    ]

    serializer_class = ImportPluginSupplierPartSerializer

    def get_serializer_context(self):
        """Add extra context information to the endpoint serializer."""
        ctx = super().get_serializer_context()
        # ctx['request'] = self.request

        return ctx
