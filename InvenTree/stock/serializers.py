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
                  'last_checked',
                  'review_needed',
                  'expected_arrival')


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
