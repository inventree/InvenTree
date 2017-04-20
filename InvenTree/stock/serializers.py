from rest_framework import serializers

from .models import StockItem, StockLocation, StockTracking


class StockItemSerializer(serializers.HyperlinkedModelSerializer):
    """ Serializer for a StockItem
    """

    class Meta:
        model = StockItem
        fields = ('url',
                  'part',
                  'supplier_part',
                  'location',
                  'quantity',
                  'status',
                  'notes',
                  'updated',
                  'stocktake_date',
                  'stocktake_user',
                  'review_needed',
                  'expected_arrival')

        """ These fields are read-only in this context.
        They can be updated by accessing the appropriate API endpoints
        """
        read_only_fields = ('stocktake_date', 'quantity',)


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
                  'path')


class StockTrackingSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = StockTracking
        fields = ('url',
                  'item',
                  'quantity',
                  'when')
