from rest_framework import serializers

from .models import Company


class CompanyBriefSerializer(serializers.ModelSerializer):

    url = serializers.CharField(source='get_absolute_url', read_only=True)

    class Meta:
        model = Company
        fields = [
            'pk',
            'url',
            'name'
        ]


class CompanySerializer(serializers.ModelSerializer):

    url = serializers.CharField(source='get_absolute_url', read_only=True)

    class Meta:
        model = Company
        fields = '__all__'
