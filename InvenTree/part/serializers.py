from rest_framework import serializers

from .models import Part


class PartSerializer(serializers.ModelSerializer):
    """ Serializer for complete detail information of a part.
    Used when displaying all details of a single component.
    """

    class Meta:
        model = Part
        fields = [
            'url',  # Link to the part detail page
            'name',
            'IPN',
            'URL',  # Link to an external URL (optional)
            'description',
            'category',
            'category_path',
            'total_stock',
            'available_stock',
            'units',
            'trackable',
            'buildable',
            'trackable',
            'salable',
        ]
