"""
JSON serializers for the Order API
"""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework import serializers

from sql_util.utils import SubqueryCount

from InvenTree.serializers import InvenTreeModelSerializer
from InvenTree.serializers import InvenTreeAttachmentSerializerField

from company.serializers import CompanyBriefSerializer, SupplierPartSerializer
from part.serializers import PartBriefSerializer

from .models import PurchaseOrder, PurchaseOrderLineItem
from .models import PurchaseOrderAttachment, SalesOrderAttachment
from .models import SalesOrder, SalesOrderLineItem
from .models import SalesOrderAllocation


class POSerializer(InvenTreeModelSerializer):
    """ Serializer for a PurchaseOrder object """

    def __init__(self, *args, **kwargs):

        supplier_detail = kwargs.pop('supplier_detail', False)

        super().__init__(*args, **kwargs)

        if supplier_detail is not True:
            self.fields.pop('supplier_detail')

    @staticmethod
    def annotate_queryset(queryset):
        """
        Add extra information to the queryset
        """

        queryset = queryset.annotate(
            line_items=SubqueryCount('lines')
        )

        return queryset

    supplier_detail = CompanyBriefSerializer(source='supplier', many=False, read_only=True)
    
    line_items = serializers.IntegerField(read_only=True)

    status_text = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = PurchaseOrder
        
        fields = [
            'pk',
            'issue_date',
            'complete_date',
            'creation_date',
            'description',
            'line_items',
            'link',
            'reference',
            'supplier',
            'supplier_detail',
            'supplier_reference',
            'status',
            'status_text',
            'notes',
        ]
        
        read_only_fields = [
            'reference',
            'status'
        ]


class POLineItemSerializer(InvenTreeModelSerializer):

    def __init__(self, *args, **kwargs):

        part_detail = kwargs.pop('part_detail', False)

        super().__init__(*args, **kwargs)

        if part_detail is not True:
            self.fields.pop('part_detail')
            self.fields.pop('supplier_part_detail')

    quantity = serializers.FloatField()
    received = serializers.FloatField()
    
    part_detail = PartBriefSerializer(source='get_base_part', many=False, read_only=True)
    supplier_part_detail = SupplierPartSerializer(source='part', many=False, read_only=True)
    
    class Meta:
        model = PurchaseOrderLineItem

        fields = [
            'pk',
            'quantity',
            'reference',
            'notes',
            'order',
            'part',
            'part_detail',
            'supplier_part_detail',
            'received',
        ]


class POAttachmentSerializer(InvenTreeModelSerializer):
    """
    Serializers for the PurchaseOrderAttachment model
    """

    attachment = InvenTreeAttachmentSerializerField(required=True)

    class Meta:
        model = PurchaseOrderAttachment
        
        fields = [
            'pk',
            'order',
            'attachment',
            'comment',
        ]


class SalesOrderSerializer(InvenTreeModelSerializer):
    """
    Serializers for the SalesOrder object
    """

    def __init__(self, *args, **kwargs):

        customer_detail = kwargs.pop('customer_detail', False)

        super().__init__(*args, **kwargs)

        if customer_detail is not True:
            self.fields.pop('customer_detail')

    @staticmethod
    def annotate_queryset(queryset):
        """
        Add extra information to the queryset
        """

        queryset = queryset.annotate(
            line_items=SubqueryCount('lines')
        )

        return queryset

    customer_detail = CompanyBriefSerializer(source='customer', many=False, read_only=True)

    line_items = serializers.IntegerField(read_only=True)

    status_text = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = SalesOrder

        fields = [
            'pk',
            'shipment_date',
            'creation_date',
            'description',
            'line_items',
            'link',
            'reference',
            'customer',
            'customer_detail',
            'customer_reference',
            'status',
            'status_text',
            'shipment_date',
            'notes',
        ]

        read_only_fields = [
            'reference',
            'status'
        ]


class SalesOrderAllocationSerializer(InvenTreeModelSerializer):
    """
    Serializer for the SalesOrderAllocation model.
    This includes some fields from the related model objects.
    """

    location_path = serializers.CharField(source='get_location_path')
    location_id = serializers.IntegerField(source='get_location')
    serial = serializers.CharField(source='get_serial')
    quantity = serializers.FloatField()

    class Meta:
        model = SalesOrderAllocation

        fields = [
            'pk',
            'line',
            'serial',
            'quantity',
            'location_id',
            'location_path',
            'item',
        ]


class SOLineItemSerializer(InvenTreeModelSerializer):
    """ Serializer for a SalesOrderLineItem object """

    def __init__(self, *args, **kwargs):

        part_detail = kwargs.pop('part_detail', False)
        order_detail = kwargs.pop('order_detail', False)
        allocations = kwargs.pop('allocations', False)

        super().__init__(*args, **kwargs)

        if part_detail is not True:
            self.fields.pop('part_detail')

        if order_detail is not True:
            self.fields.pop('order_detail')

        if allocations is not True:
            self.fields.pop('allocations')
            
    order_detail = SalesOrderSerializer(source='order', many=False, read_only=True)
    part_detail = PartBriefSerializer(source='part', many=False, read_only=True)
    allocations = SalesOrderAllocationSerializer(many=True, read_only=True)

    quantity = serializers.FloatField()
    allocated = serializers.FloatField(source='allocated_quantity', read_only=True)
    fulfilled = serializers.FloatField(source='fulfilled_quantity', read_only=True)

    class Meta:
        model = SalesOrderLineItem

        fields = [
            'pk',
            'allocated',
            'allocations',
            'quantity',
            'fulfilled',
            'reference',
            'notes',
            'order',
            'order_detail',
            'part',
            'part_detail',
        ]


class SOAttachmentSerializer(InvenTreeModelSerializer):
    """
    Serializers for the SalesOrderAttachment model
    """

    attachment = InvenTreeAttachmentSerializerField(required=True)

    class Meta:
        model = SalesOrderAttachment
        
        fields = [
            'pk',
            'order',
            'attachment',
            'comment',
        ]
