"""
JSON serializers for Build API
"""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import transaction

from django.utils.translation import ugettext_lazy as _

from django.db.models import Case, When, Value
from django.db.models import BooleanField

from rest_framework import serializers
from rest_framework.serializers import ValidationError

from InvenTree.serializers import InvenTreeModelSerializer, InvenTreeAttachmentSerializer
from InvenTree.serializers import InvenTreeAttachmentSerializerField, UserSerializerBrief

import InvenTree.helpers

from stock.models import StockItem
from stock.serializers import StockItemSerializerBrief, LocationSerializer

from part.models import Part, BomItem
from part.serializers import PartSerializer, PartBriefSerializer
from users.serializers import OwnerSerializer

from .models import Build, BuildItem, BuildOrderAttachment


class BuildSerializer(InvenTreeModelSerializer):
    """
    Serializes a Build object
    """

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


class BuildAllocationItemSerializer(serializers.Serializer):
    """
    A serializer for allocating a single stock item against a build order
    """

    bom_item = serializers.PrimaryKeyRelatedField(
        queryset=BomItem.objects.all(),
        many=False,
        allow_null=False,
        required=True,
        label=_('BOM Item'),
    )

    def validate_bom_item(self, bom_item):
        
        build = self.context['build']

        # BomItem must point to the same 'part' as the parent build
        if build.part != bom_item.part:
            raise ValidationError(_("bom_item.part must point to the same part as the build order"))

        return bom_item

    stock_item = serializers.PrimaryKeyRelatedField(
        queryset=StockItem.objects.all(),
        many=False,
        allow_null=False,
        required=True,
        label=_('Stock Item'),
    )

    def validate_stock_item(self, stock_item):

        if not stock_item.in_stock:
            raise ValidationError(_("Item must be in stock"))
        
        return stock_item

    quantity = serializers.DecimalField(
        max_digits=15,
        decimal_places=5,
        min_value=0,
        required=True
    )

    def validate_quantity(self, quantity):

        if quantity <= 0:
            raise ValidationError(_("Quantity must be greater than zero"))

        return quantity

    output = serializers.PrimaryKeyRelatedField(
        queryset=StockItem.objects.filter(is_building=True),
        many=False,
        allow_null=True,
        required=False,
        label=_('Build Output'),
    )

    class Meta:
        fields = [
            'bom_item',
            'stock_item',
            'quantity',
            'output',
        ]

    def validate(self, data):

        super().validate(data)

        bom_item = data['bom_item']
        stock_item = data['stock_item']
        quantity = data['quantity']
        output = data.get('output', None)

        build = self.context['build']

        # TODO: Check that the "stock item" is valid for the referenced "sub_part"
        # Note: Because of allow_variants options, it may not be a direct match!

        # Check that the quantity does not exceed the available amount from the stock item
        q = stock_item.unallocated_quantity()

        if quantity > q:

            q = InvenTree.helpers.clean_decimal(q)

            raise ValidationError({
                'quantity': _(f"Available quantity ({q}) exceeded")
            })

        # Output *must* be set for trackable parts
        if output is None and bom_item.sub_part.trackable:
            raise ValidationError({
                'output': _('Build output must be specified for allocation of tracked parts')
            })

        # Output *cannot* be set for un-tracked parts
        if output is not None and not bom_item.sub_part.trackable:
            
            raise ValidationError({
                'output': _('Build output cannot be specified for allocation of untracked parts')
            }) 

        return data


class BuildAllocationSerializer(serializers.Serializer):
    """
    DRF serializer for allocation stock items against a build order
    """

    items = BuildAllocationItemSerializer(many=True)

    class Meta:
        fields = [
            'items',
        ]

    def validate(self, data):
        """
        Validation
        """
        
        super().validate(data)

        items = data.get('items', [])

        if len(items) == 0:
            raise ValidationError(_('Allocation items must be provided'))
        
        return data

    def save(self):

        data = self.validated_data

        items = data.get('items', [])

        build = self.context['build']

        with transaction.atomic():
            for item in items:
                bom_item = item['bom_item']
                stock_item = item['stock_item']
                quantity = item['quantity']
                output = item.get('output', None)

                # Create a new BuildItem to allocate stock
                build_item = BuildItem.objects.create(
                    build=build,
                    bom_item=bom_item,
                    stock_item=stock_item,
                    quantity=quantity,
                    install_into=output
                )


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
