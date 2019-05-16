"""
JSON serializers for Company app
"""

from rest_framework import serializers

from .models import Company


class CompanyBriefSerializer(serializers.ModelSerializer):
    """ Serializer for Company object (limited detail) """

    url = serializers.CharField(source='get_absolute_url', read_only=True)

    class Meta:
        model = Company
        fields = [
            'pk',
            'url',
            'name'
        ]


class CompanySerializer(serializers.ModelSerializer):
    """ Serializer for Company object (full detail) """

    url = serializers.CharField(source='get_absolute_url', read_only=True)
    part_count = serializers.CharField(read_only=True)

    class Meta:
        model = Company
        fields = [
            'id',
            'url',
            'name',
            'description',
            'website',
            'name',
            'phone',
            'address',
            'email',
            'contact',
            'URL',
            'image',
            'notes',
            'is_customer',
            'is_supplier',
            'part_count'
        ]
