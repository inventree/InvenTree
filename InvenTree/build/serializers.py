"""
JSON serializers for Build API
"""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db.models import Case, When, Value
from django.db.models import BooleanField

from rest_framework import serializers

from InvenTree.serializers import InvenTreeModelSerializer

from stock.serializers import StockItemSerializerBrief
from part.serializers import PartBriefSerializer

from .models import Build, BuildItem


class BuildSerializer(InvenTreeModelSerializer):
    """ Serializes a Build object """

    url = serializers.CharField(source='get_absolute_url', read_only=True)
    status_text = serializers.CharField(source='get_status_display', read_only=True)

    part_detail = PartBriefSerializer(source='part', many=False, read_only=True)

    quantity = serializers.FloatField()

    overdue = serializers.BooleanField(required=False, read_only=True)

    @staticmethod
    def annotate_queryset(queryset):
        """
        Add custom annotations to the BuildSerializer queryset,
        performing database queries as efficiently as possible.

        The following annoted fields are added:

        - overdue: True if the build is outstanding *and* the completion date has past

        """

        # Annotate a boolean 'overdue' flag

        queryset = queryset.annotate(
            overdue=Case(
                When(
                    Build.OVERDUE_FILTER, then=Value(True, output_field=BooleanField()),
                ),
                default=Value(False, output_field=BooleanField())
            )
        )

        return queryset

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
            'completed',
            'completion_date',
            'part',
            'part_detail',
            'overdue',
            'reference',
            'sales_order',
            'quantity',
            'status',
            'status_text',
            'target_date',
            'notes',
            'link',
        ]

        read_only_fields = [
            'completed',
            'creation_date',
            'completion_data',
            'status',
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
            'install_into',
            'part',
            'part_name',
            'part_image',
            'stock_item',
            'stock_item_detail',
            'quantity'
        ]
