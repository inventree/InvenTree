"""
JSON serializers for common components
"""

from .models import Currency

from InvenTree.serializers import InvenTreeModelSerializer


class CurrencySerializer(InvenTreeModelSerializer):
    """ Serializer for Currency object """

    class Meta:
        model = Currency
        fields = [
            'pk',
            'symbol',
            'suffix',
            'description',
            'value',
            'base'
        ]
