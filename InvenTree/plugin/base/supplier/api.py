"""APIs for supplier plugins."""
from dataclasses import dataclass

from django.utils.translation import gettext_lazy as _

from rest_framework import permissions, serializers
from rest_framework.exceptions import NotFound, ValidationError

from common.models import WebConnection
from InvenTree.mixins import CreateAPI, ListAPI
from part.models import PartCategory
from plugin import registry
from plugin.base.supplier.mixins import SearchRunResult
from plugin.models import PluginConfig


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
        label=_('Suppier Connection'),
    )
    reference = serializers.CharField(
        required=True,
        label=_('Reference'),
    )
    category = serializers.PrimaryKeyRelatedField(queryset=PartCategory.objects.all())

    def save(self):
        """Save the serializer data. This tries to import the part."""
        data = self.validated_data
        plugin_cgf: PluginConfig = data['connection'].plugin

        # Checks
        # Plugin must be active
        if not plugin_cgf.active:
            raise NotFound(detail=f"Plugin '{plugin_cgf}' is not active")

        # Mixin and function must be present
        if not plugin_cgf.plugin.mixin_enabled('supplier'):
            raise ValidationError({'connection': _('This plugin does not provide the required mixin.')})
        if not hasattr(plugin_cgf.plugin, 'import_part'):
            raise ValidationError({'connection': _('This plugin does not provide the required function.')})

        # Try to import part
        plugin_cgf.plugin.import_part(
            term=data['reference'],
            category=data['category'],
            user=self.context['request'].user
        )


class ImportPluginSupplierPartView(CreateAPI):
    """API endpoint for importing a part from a supplier plugin."""
    permission_classes = [
        permissions.IsAuthenticated
    ]
    serializer_class = ImportPluginSupplierPartSerializer
