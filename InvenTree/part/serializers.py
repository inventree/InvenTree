from rest_framework import serializers

from .models import Part, PartCategory


class CategoryBriefSerializer(serializers.ModelSerializer):

    url = serializers.CharField(source='get_absolute_url', read_only=True)

    class Meta:
        model = PartCategory
        fields = [
            'pk',
            'name',
            'pathstring',
            'url',
        ]


class PartBriefSerializer(serializers.ModelSerializer):

    url = serializers.CharField(source='get_absolute_url', read_only=True)

    class Meta:
        model = Part
        fields = [
            'pk',
            'url',
            'name',
        ]


class PartSerializer(serializers.ModelSerializer):
    """ Serializer for complete detail information of a part.
    Used when displaying all details of a single component.
    """

    category = CategoryBriefSerializer(many=False, read_only=True)

    class Meta:
        model = Part
        fields = [
            'pk',
            'url',  # Link to the part detail page
            'name',
            'IPN',
            'URL',  # Link to an external URL (optional)
            'description',
            'category',
            'total_stock',
            'available_stock',
            'units',
            'trackable',
            'buildable',
            'trackable',
            'salable',
        ]
