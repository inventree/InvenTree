"""
JSON serializers for Build API
"""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework import serializers
from InvenTree.serializers import InvenTreeModelSerializer
from stock.serializers import StockItemSerializerBrief

from .models import Build, BuildItem

class BuildSerializer(InvenTreeModelSerializer):
    """ Serializes a Build object """

    url = serializers.CharField(source='get_absolute_url', read_only=True)
    status_text = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Build
        fields = [
            'pk',
            'url',
            'title',
            'creation_date',
            'completion_date',
            'part',
            'quantity',
            'status',
            'status_text',
            'notes']


class BuildItemSerializer(InvenTreeModelSerializer):
    """ Serializes a BuildItem object """

    part = serializers.IntegerField(source='stock_item.part.pk', read_only=True)
    part_name = serializers.CharField(source='stock_item.part.name', read_only=True)
    stock_item_detail = StockItemSerializerBrief(source='stock_item', read_only=True)

    class Meta:
        model = BuildItem
        fields = [
            'pk',
            'build',
            'part',
            'part_name',
            'stock_item',
            'stock_item_detail',
            'quantity'
        ]
