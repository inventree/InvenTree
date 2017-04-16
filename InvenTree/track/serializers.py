from rest_framework import serializers

from .models import UniquePart, PartTrackingInfo


class UniquePartSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = UniquePart
        fields = ['url',
                  'part',
                  'creation_date',
                  'serial',
                  # 'createdBy',
                  'customer',
                  'status']


class PartTrackingInfoSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = PartTrackingInfo
        fields = '__all__'
