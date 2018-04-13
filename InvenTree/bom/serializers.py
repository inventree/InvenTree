from rest_framework import serializers

from .models import BomItem


class BomItemSerializer(serializers.ModelSerializer):

    class Meta:
        model = BomItem
        fields = ('url',
                  'part',
                  'sub_part',
                  'quantity')