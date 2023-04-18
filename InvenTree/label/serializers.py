"""API serializers for the label app"""

from InvenTree.serializers import (InvenTreeAttachmentSerializerField,
                                   InvenTreeModelSerializer)

from .models import PartLabel, StockItemLabel, StockLocationLabel


class StockItemLabelSerializer(InvenTreeModelSerializer):
    """Serializes a StockItemLabel object."""

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

    label = InvenTreeAttachmentSerializerField(required=True)


class StockLocationLabelSerializer(InvenTreeModelSerializer):
    """Serializes a StockLocationLabel object."""

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

    label = InvenTreeAttachmentSerializerField(required=True)


class PartLabelSerializer(InvenTreeModelSerializer):
    """Serializes a PartLabel object."""

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

    label = InvenTreeAttachmentSerializerField(required=True)
