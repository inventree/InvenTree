"""Serializer definitions for the supplier plugin base."""

from rest_framework import serializers

import part.models as part_models
from part.serializers import PartSerializer


class SearchResultSerializer(serializers.Serializer):
    """Serializer for a search result."""

    class Meta:
        """Meta options for the SearchResultSerializer."""

        fields = [
            'id',
            'sku',
            'name',
            'exact',
            'description',
            'price',
            'link',
            'image_url',
            'existing_part_id',
        ]
        read_only_fields = fields

    id = serializers.CharField()
    sku = serializers.CharField()
    name = serializers.CharField()
    exact = serializers.BooleanField()
    description = serializers.CharField()
    price = serializers.CharField()
    link = serializers.CharField()
    image_url = serializers.CharField()
    existing_part_id = serializers.SerializerMethodField()

    def get_existing_part_id(self, value):
        """Return the ID of the existing part if available."""
        return getattr(value.existing_part, 'pk', None)


class ImportParameterSerializer(serializers.Serializer):
    """Serializer for a ImportParameter."""

    class Meta:
        """Meta options for the ImportParameterSerializer."""

        fields = ['name', 'value', 'parameter_template', 'on_category']

    name = serializers.CharField()
    value = serializers.CharField()
    parameter_template = serializers.SerializerMethodField()
    on_category = serializers.BooleanField()

    def get_parameter_template(self, value):
        """Return the ID of the parameter template if available."""
        return getattr(value.parameter_template, 'pk', None)


class ImportRequestSerializer(serializers.Serializer):
    """Serializer for the import request."""

    supplier = serializers.CharField(required=True)
    part_import_id = serializers.CharField(required=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=part_models.PartCategory.objects.all(),
        many=False,
        required=False,
        allow_null=True,
    )
    part_id = serializers.PrimaryKeyRelatedField(
        queryset=part_models.Part.objects.all(),
        many=False,
        required=False,
        allow_null=True,
    )


class ImportResultSerializer(serializers.Serializer):
    """Serializer for the import result."""

    class Meta:
        """Meta options for the ImportResultSerializer."""

        fields = [
            'part_id',
            'part_detail',
            'manufacturer_part_id',
            'supplier_part_id',
            'pricing',
            'parameters',
        ]

    part_id = serializers.IntegerField()
    part_detail = PartSerializer()
    manufacturer_part_id = serializers.IntegerField()
    supplier_part_id = serializers.IntegerField()
    pricing = serializers.SerializerMethodField()
    parameters = ImportParameterSerializer(many=True)

    def get_pricing(self, value: dict[str, list[tuple[int, str]]]):
        """Return the pricing data as a dictionary."""
        return value['pricing']
