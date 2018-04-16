from rest_framework import serializers

from .models import Part, PartCategory
from .models import BomItem


class BomItemSerializer(serializers.ModelSerializer):

    class Meta:
        model = BomItem
        fields = ('url',
                  'part',
                  'sub_part',
                  'quantity')


"""
class PartParameterSerializer(serializers.HyperlinkedModelSerializer):
    " Serializer for a PartParameter
    "

    class Meta:
        model = PartParameter
        fields = ('url',
                  'part',
                  'template',
                  'name',
                  'value',
                  'units')
"""


class PartSerializer(serializers.ModelSerializer):
    """ Serializer for complete detail information of a part.
    Used when displaying all details of a single component.
    """

    class Meta:
        model = Part
        fields = ('url',
                  'name',
                  'IPN',
                  'description',
                  'category',
                  'stock',
                  'units',
                  'trackable',
                  )


class PartCategorySerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = PartCategory
        fields = ('url',
                  'name',
                  'description',
                  'parent',
                  'pathstring')


"""
class PartTemplateSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = PartParameterTemplate
        fields = ('url',
                  'name',
                  'units',
                  'format')
"""
