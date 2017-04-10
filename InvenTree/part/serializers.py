from rest_framework import serializers

from .models import Part, PartCategory, PartParameter


class ParameterSerializer(serializers.ModelSerializer):
    class Meta:
        model = PartParameter
        fields = ('name',
                  'value',
                  'units')


class PartSerializer(serializers.ModelSerializer):
    params = ParameterSerializer(source='parameters', many=True)

    class Meta:
        model = Part
        fields = ('pk',
                  'name',
                  'IPN',
                  'description',
                  'category',
                  'stock',
                  'params')


class PartCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = PartCategory
        fields = ('pk',
                  'name',
                  'description',
                  'parent',
                  'path')
