# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from InvenTree.serializers import InvenTreeModelSerializer
from InvenTree.serializers import InvenTreeAttachmentSerializerField

from .models import StockItemLabel


class StockItemLabelSerializer(InvenTreeModelSerializer):
    """
    Serializes a StockItemLabel object.
    """

    label = InvenTreeAttachmentSerializerField(required=True)

    class Meta:
        model = StockItemLabel
        fields = [
            'pk',
            'name',
            'description',
            'label',
            'filters',
            'enabled',
        ]
