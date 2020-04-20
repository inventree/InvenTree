"""
JSON serializers for the Order API
"""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework import serializers

from django.db.models import Count

from InvenTree.serializers import InvenTreeModelSerializer
from company.serializers import CompanyBriefSerializer

from .models import PurchaseOrder, PurchaseOrderLineItem
from .models import SalesOrder, SalesOrderLineItem


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

        return queryset.annotate(
            line_items=Count('lines'),
        )

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

    class Meta:
        model = PurchaseOrderLineItem

        fields = [
            'pk',
            'quantity',
            'reference',
            'notes',
            'order',
            'part',
            'received',
        ]


class SalseOrderSerializer(InvenTreeModelSerializer):
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

        return queryset.annotate(
            line_items=Count('lines'),
        )

    customer_detail = CompanyBriefSerializer(source='customer', many=False, read_only=True)

    line_items = serializers.IntegerField(read_only=True)

    status_text = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = SalesOrder

        fields = [
            'pk',
            'issue_date',
            'complete_date',
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
            'notes',
        ]

        read_only_fields = [
            'reference',
            'status'
        ]
