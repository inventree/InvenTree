
from InvenTree.serializers import InvenTreeModelSerializer
from .models import SalesOrderBasket
from rest_framework import serializers
class SOBasketSerializer(InvenTreeModelSerializer):
    """
    Serializers for the SOBasket model
    """

    status_text = serializers.CharField(source='get_status_display', read_only=True)
    class Meta:
        model = SalesOrderBasket

        fields = [
            'pk',
            'name',
            'status',
            'status_text',
            'sales_orders',
            'creation_date',
        ]
        read_only_fields = [
            'sales_orders',
        ]
