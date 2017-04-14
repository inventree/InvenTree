from rest_framework import serializers

from .models import Supplier, SupplierPart, SupplierPriceBreak


class SupplierSerializer(serializers.ModelSerializer):

    class Meta:
        model = Supplier
        fields = '__all__'


class SupplierPartSerializer(serializers.ModelSerializer):

    price_breaks = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = SupplierPart
        fields = ['pk',
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


class SupplierPriceBreakSerializer(serializers.ModelSerializer):

    class Meta:
        model = SupplierPriceBreak
        fields = ['pk',
                  'part',
                  'quantity',
                  'cost']
