"""
JSON serializers for Build API
"""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db.models import Case, When, Value
from django.db.models import BooleanField

from rest_framework import serializers

from InvenTree.serializers import InvenTreeModelSerializer, InvenTreeAttachmentSerializer
from InvenTree.serializers import InvenTreeAttachmentSerializerField, UserSerializerBrief

from stock.serializers import StockItemSerializerBrief
from stock.serializers import LocationSerializer
from part.serializers import PartSerializer, PartBriefSerializer
from users.serializers import OwnerSerializer

from .models import Build, BuildItem, BuildOrderAttachment


class BuildSerializer(InvenTreeModelSerializer):
    """ Serializes a Build object """

    url = serializers.CharField(source='get_absolute_url', read_only=True)
    status_text = serializers.CharField(source='get_status_display', read_only=True)

    part_detail = PartBriefSerializer(source='part', many=False, read_only=True)

    quantity = serializers.FloatField()

    overdue = serializers.BooleanField(required=False, read_only=True)

    issued_by_detail = UserSerializerBrief(source='issued_by', read_only=True)

    responsible_detail = OwnerSerializer(source='responsible', read_only=True)

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
        part_detail = kwargs.pop('part_detail', True)

        super().__init__(*args, **kwargs)

        if part_detail is not True:
            self.fields.pop('part_detail')

    class Meta:
        model = Build
        fields = [
            'pk',
            'url',
            'title',
            'batch',
            'creation_date',
            'completed',
            'completion_date',
            'destination',
            'parent',
            'part',
            'part_detail',
            'overdue',
            'reference',
            'sales_order',
            'quantity',
            'status',
            'status_text',
            'target_date',
            'take_from',
            'notes',
            'link',
            'issued_by',
            'issued_by_detail',
            'responsible',
            'responsible_detail',
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

    bom_part = serializers.IntegerField(source='bom_item.sub_part.pk', read_only=True)
    part = serializers.IntegerField(source='stock_item.part.pk', read_only=True)
    location = serializers.IntegerField(source='stock_item.location.pk', read_only=True)

    # Extra (optional) detail fields
    part_detail = PartSerializer(source='stock_item.part', many=False, read_only=True)
    build_detail = BuildSerializer(source='build', many=False, read_only=True)
    stock_item_detail = StockItemSerializerBrief(source='stock_item', read_only=True)
    location_detail = LocationSerializer(source='stock_item.location', read_only=True)

    quantity = serializers.FloatField()

    def __init__(self, *args, **kwargs):

        build_detail = kwargs.pop('build_detail', False)
        part_detail = kwargs.pop('part_detail', False)
        location_detail = kwargs.pop('location_detail', False)

        super().__init__(*args, **kwargs)

        if not build_detail:
            self.fields.pop('build_detail')

        if not part_detail:
            self.fields.pop('part_detail')

        if not location_detail:
            self.fields.pop('location_detail')

    class Meta:
        model = BuildItem
        fields = [
            'pk',
            'bom_part',
            'build',
            'build_detail',
            'install_into',
            'location',
            'location_detail',
            'part',
            'part_detail',
            'stock_item',
            'stock_item_detail',
            'quantity'
        ]


class BuildAttachmentSerializer(InvenTreeAttachmentSerializer):
    """
    Serializer for a BuildAttachment
    """

    attachment = InvenTreeAttachmentSerializerField(required=True)

    class Meta:
        model = BuildOrderAttachment

        fields = [
            'pk',
            'build',
            'attachment',
            'filename',
            'comment',
            'upload_date',
        ]

        read_only_fields = [
            'upload_date',
        ]
