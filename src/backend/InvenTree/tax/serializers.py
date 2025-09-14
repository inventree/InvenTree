"""Serializers for tax models."""

from InvenTree.serializers import InvenTreeModelSerializer

from .models import TaxConfiguration


class TaxConfigurationSerializer(InvenTreeModelSerializer):
    """Serializer for TaxConfiguration model."""

    class Meta:
        """Meta options for TaxConfigurationSerializer."""

        model = TaxConfiguration
        fields = [
            'pk',
            'name',
            'description',
            'year',
            'rate',
            'currency',
            'is_active',
            'is_inclusive',
            'applies_to_sales',
            'applies_to_purchases',
            'metadata',
        ]
