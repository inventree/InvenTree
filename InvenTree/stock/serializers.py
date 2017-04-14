from rest_framework import serializers

from .models import StockItem, StockLocation


class StockItemSerializer(serializers.HyperlinkedModelSerializer):
    """ Serializer for a StockItem
    """

    class Meta:
        model = StockItem
        fields = ('url',
                  'part',
                  'location',
                  'quantity',
                  'status',
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
