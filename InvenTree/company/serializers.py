from rest_framework import serializers

from .models import Company


class CompanySerializer(serializers.HyperlinkedModelSerializer):

    url = serializers.CharField(source='get_absolute_url', read_only=True)

    class Meta:
        model = Company
        fields = '__all__'
