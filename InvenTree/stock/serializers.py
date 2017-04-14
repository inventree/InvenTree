from rest_framework import serializers

from .models import StockItem, StockLocation


class StockItemSerializer(serializers.ModelSerializer):
    """ Serializer for a StockItem
    """

    class Meta:
        model = StockItem
        fields = ('pk',
                  'part',
                  'location',
                  'quantity',
                  'status',
                  'updated',
                  'last_checked',
                  'review_needed',
                  'expected_arrival')


class LocationSerializer(serializers.ModelSerializer):
    """ Detailed information about a stock location
    """

    class Meta:
        model = StockLocation
        fields = ('pk',
                  'name',
                  'description',
                  'parent',
                  'path')
