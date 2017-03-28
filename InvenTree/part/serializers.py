from rest_framework import serializers

from .models import Part, PartCategory

class PartSerializer(serializers.ModelSerializer):
    class Meta:
        model = Part
        fields = ('pk',
                  'IPN',
                  'description',
                  'category',
                  'quantity')
        
class PartCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = PartCategory
        fields = ('pk',
                  'name',
                  'description',
                  'path')