from rest_framework import serializers

from .models import Part


class PartSerializer(serializers.ModelSerializer):
    """ Serializer for complete detail information of a part.
    Used when displaying all details of a single component.
    """

    def _category_name(self, part):
        if part.category:
            return part.category.name
        return ''

    def _category_url(self, part):
        if part.category:
            return part.category.get_absolute_url()
        return ''

    category_name = serializers.SerializerMethodField('_category_name')
    category_url = serializers.SerializerMethodField('_category_url')

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
            'category_name',
            'category_url',
            'total_stock',
            'available_stock',
            'units',
            'trackable',
            'buildable',
            'trackable',
            'salable',
        ]
