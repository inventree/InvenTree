from rest_framework import serializers

from .models import StockItem, StockLocation


class StockItemSerializer(serializers.ModelSerializer):
    """ Serializer for a StockItem
    """

    class Meta:
        model = StockItem
        fields = [
            'pk',
            'url',
            'part',
            'supplier_part',
            'location',
            'in_stock',
            'belongs_to',
            'customer',
            'quantity',
            'serial',
            'batch',
            'status',
            'notes',
            'updated',
            'stocktake_date',
            'stocktake_user',
            'review_needed',
        ]

        """ These fields are read-only in this context.
        They can be updated by accessing the appropriate API endpoints
        """
        read_only_fields = [
            'stocktake_date',
            'stocktake_user',
            'updated',
            'quantity',
        ]


class StockQuantitySerializer(serializers.ModelSerializer):

    class Meta:
        model = StockItem
        fields = ('quantity',)


class LocationSerializer(serializers.HyperlinkedModelSerializer):
    """ Detailed information about a stock location
    """

    class Meta:
        model = StockLocation
        fields = ('url',
                  'name',
                  'description',
                  'parent',
                  'pathstring')
