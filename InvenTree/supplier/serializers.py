from rest_framework import serializers

from .models import Supplier, SupplierPart, SupplierPriceBreak


class SupplierSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Supplier
        fields = '__all__'


class SupplierPartSerializer(serializers.ModelSerializer):

    price_breaks = serializers.HyperlinkedRelatedField(many=True,
                                                       read_only=True,
                                                       view_name='price_break-detail')

    class Meta:
        model = SupplierPart
        fields = ['url',
                  'part',
                  'supplier',
                  'SKU',
                  'manufacturer',
                  'MPN',
                  'URL',
                  'description',
                  'single_price',
                  'packaging',
                  'multiple',
                  'minimum',
                  'price_breaks',
                  'lead_time']


class SupplierPriceBreakSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = SupplierPriceBreak
        fields = ['url',
                  'part',
                  'quantity',
                  'cost']
