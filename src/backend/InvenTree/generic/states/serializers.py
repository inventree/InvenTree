"""Serializer classes for handling generic state information."""

from django.utils.translation import gettext_lazy as _

from rest_framework import serializers


class GenericStateValueSerializer(serializers.Serializer):
    """API serializer for generic state information."""

    class Meta:
        """Meta class for GenericStateValueSerializer."""

        fields = ['key', 'logical_key', 'name', 'label', 'color', 'custom']

    key = serializers.IntegerField(label=_('Key'), required=True)

    logical_key = serializers.CharField(label=_('Logical Key'), required=False)

    name = serializers.CharField(label=_('Name'), required=True)

    label = serializers.CharField(label=_('Label'), required=True)

    color = serializers.CharField(label=_('Color'), required=False)

    custom = serializers.BooleanField(label=_('Custom'), required=False)


class GenericStateClassSerializer(serializers.Serializer):
    """API serializer for generic state class information."""

    class Meta:
        """Meta class for GenericStateClassSerializer."""

        fields = ['status_class', 'values']

    status_class = serializers.CharField(label=_('Class'), read_only=True)

    values = serializers.DictField(
        child=GenericStateValueSerializer(), label=_('Values'), required=True
    )
