from rest_framework import serializers

from part.models import Part

from .models import Supplier, SupplierPart, SupplierPriceBreak
from .models import Manufacturer
from .models import Customer


class SupplierSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Supplier
        fields = '__all__'


class ManufacturerSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Manufacturer
        fields = '__all__'


class CustomerSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Customer
        fields = '__all__'


class SupplierPartSerializer(serializers.ModelSerializer):

    price_breaks = serializers.HyperlinkedRelatedField(many=True,
                                                       read_only=True,
                                                       view_name='supplierpricebreak-detail')

    part = serializers.HyperlinkedRelatedField(view_name='part-detail',
                                               queryset=Part.objects.all())

    supplier = serializers.HyperlinkedRelatedField(view_name='supplier-detail',
                                                   queryset=Supplier.objects.all())

    manufacturer = serializers.HyperlinkedRelatedField(view_name='manufacturer-detail',
                                                       queryset=Manufacturer.objects.all())

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
