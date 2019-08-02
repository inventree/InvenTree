"""
JSON serializers for the Order API
"""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from InvenTree.serializers import InvenTreeModelSerializer

from .models import PurchaseOrder, PurchaseOrderLineItem


class POSerializer(InvenTreeModelSerializer):
    """ Serializes an Order object """

    class Meta:
        model = PurchaseOrder
        
        fields = [
            'pk',
            'supplier',
            'reference',
            'description',
            'URL',
            'status',
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
