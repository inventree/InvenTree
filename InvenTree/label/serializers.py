from InvenTree.serializers import InvenTreeModelSerializer
from InvenTree.serializers import InvenTreeAttachmentSerializerField

from .models import StockItemLabel, StockLocationLabel, PartLabel


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


class StockLocationLabelSerializer(InvenTreeModelSerializer):
    """
    Serializes a StockLocationLabel object
    """

    label = InvenTreeAttachmentSerializerField(required=True)

    class Meta:
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
    """
    Serializes a PartLabel object
    """

    label = InvenTreeAttachmentSerializerField(required=True)

    class Meta:
        model = PartLabel
        fields = [
            'pk',
            'name',
            'description',
            'label',
            'filters',
            'enabled',
        ]
