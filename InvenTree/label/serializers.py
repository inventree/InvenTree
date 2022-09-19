"""API serializers for the label app"""

from InvenTree.serializers import (InvenTreeAttachmentSerializerField,
                                   InvenTreeModelSerializer)

from .models import PartLabel, StockItemLabel, StockLocationLabel


class StockItemLabelSerializer(InvenTreeModelSerializer):
    """Serializes a StockItemLabel object."""

    label = InvenTreeAttachmentSerializerField(required=True)

    class Meta:
        """Metaclass options."""

        model = StockItemLabel
        fields = [
            'pk',
            'name',
            'description',
            'label',
            'filters',
            'enabled',
        ]


class StockLocationLabelSerializer(InvenTreeModelSerializer):
    """Serializes a StockLocationLabel object."""

    label = InvenTreeAttachmentSerializerField(required=True)

    class Meta:
        """Metaclass options."""

        model = StockLocationLabel
        fields = [
            'pk',
            'name',
            'description',
            'label',
            'filters',
            'enabled',
        ]


class PartLabelSerializer(InvenTreeModelSerializer):
    """Serializes a PartLabel object."""

    label = InvenTreeAttachmentSerializerField(required=True)

    class Meta:
        """Metaclass options."""

        model = PartLabel
        fields = [
            'pk',
            'name',
            'description',
            'label',
            'filters',
            'enabled',
        ]
