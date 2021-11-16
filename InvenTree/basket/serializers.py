
from InvenTree.serializers import InvenTreeModelSerializer
from .models import SalesOrderBasket
from rest_framework import serializers

class SOBasketSerializer(InvenTreeModelSerializer):
    """
    Serializers for the SalesOrderAttachment model
    """

    status_text = serializers.CharField(source='get_status_display', read_only=True)
    class Meta:
        model = SalesOrderBasket

        fields = [
            'pk',
            'name',
            'status',
            'status_text',
            'creation_date',
            'sales_orders',
        ]

        read_only_fields = [
            'status',
            'creation_date',
            'status_text',
        ]