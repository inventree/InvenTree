from rest_framework import serializers

from part.models import Part

from .models import Company

class CompanySerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Company
        fields = '__all__'
