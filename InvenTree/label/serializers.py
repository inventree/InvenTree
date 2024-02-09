"""API serializers for the label app."""

import label.models
from InvenTree.serializers import (
    InvenTreeAttachmentSerializerField,
    InvenTreeModelSerializer,
)


class LabelSerializerBase(InvenTreeModelSerializer):
    """Base class for label serializer."""

    label = InvenTreeAttachmentSerializerField(required=True)

    @staticmethod
    def label_fields():
        """Generic serializer fields for a label template."""
        return ['pk', 'name', 'description', 'label', 'filters', 'enabled']


class StockItemLabelSerializer(LabelSerializerBase):
    """Serializes a StockItemLabel object."""

    class Meta:
        """Metaclass options."""

        model = label.models.StockItemLabel
        fields = LabelSerializerBase.label_fields()


class StockLocationLabelSerializer(LabelSerializerBase):
    """Serializes a StockLocationLabel object."""

    class Meta:
        """Metaclass options."""

        model = label.models.StockLocationLabel
        fields = LabelSerializerBase.label_fields()


class PartLabelSerializer(LabelSerializerBase):
    """Serializes a PartLabel object."""

    class Meta:
        """Metaclass options."""

        model = label.models.PartLabel
        fields = LabelSerializerBase.label_fields()


class BuildLineLabelSerializer(LabelSerializerBase):
    """Serializes a BuildLineLabel object."""

    class Meta:
        """Metaclass options."""

        model = label.models.BuildLineLabel
        fields = LabelSerializerBase.label_fields()
