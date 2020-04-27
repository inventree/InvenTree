"""
JSON serializers for Build API
"""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework import serializers
from InvenTree.serializers import InvenTreeModelSerializer
from stock.serializers import StockItemSerializerBrief

from .models import Build, BuildItem
from part.serializers import PartBriefSerializer


class BuildSerializer(InvenTreeModelSerializer):
    """ Serializes a Build object """

    url = serializers.CharField(source='get_absolute_url', read_only=True)
    status_text = serializers.CharField(source='get_status_display', read_only=True)

    part_detail = PartBriefSerializer(source='part', many=False, read_only=True)

    quantity = serializers.FloatField()

    def __init__(self, *args, **kwargs):
        part_detail = kwargs.pop('part_detail', False)

        super().__init__(*args, **kwargs)

        if part_detail is not True:
            self.fields.pop('part_detail')

    class Meta:
        model = Build
        fields = [
            'pk',
            'url',
            'title',
            'creation_date',
            'completion_date',
            'part',
            'part_detail',
            'sales_order',
            'quantity',
            'status',
            'status_text',
            'notes',
            'link',
        ]

        read_only_fields = [
            'status',
            'creation_date',
            'completion_data',
            'status_text',
        ]


class BuildItemSerializer(InvenTreeModelSerializer):
    """ Serializes a BuildItem object """

    part = serializers.IntegerField(source='stock_item.part.pk', read_only=True)
    part_name = serializers.CharField(source='stock_item.part.full_name', read_only=True)
    part_image = serializers.CharField(source='stock_item.part.image', read_only=True)
    stock_item_detail = StockItemSerializerBrief(source='stock_item', read_only=True)

    quantity = serializers.FloatField()

    class Meta:
        model = BuildItem
        fields = [
            'pk',
            'build',
            'part',
            'part_name',
            'part_image',
            'stock_item',
            'stock_item_detail',
            'quantity'
        ]
