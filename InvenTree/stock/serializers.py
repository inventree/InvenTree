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


class LocationBriefSerializer(serializers.ModelSerializer):
    """ Brief information about a stock location
    """

    class Meta:
        model = StockLocation
        fields = ('pk',
                  'name',
                  'description')


class LocationDetailSerializer(serializers.ModelSerializer):
    """ Detailed information about a stock location
    """

    # List of all stock items in this location
    items = StockItemSerializer(many=True)

    # List of all child locations under this one
    children = LocationBriefSerializer(many=True)

    class Meta:
        model = StockLocation
        fields = ('pk',
                  'name',
                  'description',
                  'parent',
                  'path',
                  'children',
                  'items')
