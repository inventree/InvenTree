
from InvenTree.serializers import InvenTreeModelSerializer
from .models import SalesOrderBasket

class SOBasketSerializer(InvenTreeModelSerializer):
    """
    Serializers for the SalesOrderAttachment model
    """


    class Meta:
        model = SalesOrderBasket

        fields = [
            'pk',
            'name',
            'status'
        ]