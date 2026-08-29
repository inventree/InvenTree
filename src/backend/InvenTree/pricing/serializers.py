"""DRF API serializers for the pricing app."""

import InvenTree.serializers
import stock.serializers as stock_serializers
from InvenTree.serializers import OptionalField
from users.serializers import UserSerializer

from .models import StockItemCost, StockItemCostEntry


class StockItemCostEntrySerializer(
    InvenTree.serializers.FilterableSerializerMixin,
    InvenTree.serializers.InvenTreeModelSerializer,
):
    """Serializer for the StockItemCostEntry model."""

    class Meta:
        """Metaclass options."""

        model = StockItemCostEntry
        fields = [
            'pk',
            'stock_item',
            'stock_item_detail',
            'cost_type',
            'min_cost',
            'min_cost_currency',
            'max_cost',
            'max_cost_currency',
            'date',
            'user',
            'user_detail',
            'source_data',
            'notes',
        ]

        read_only_fields = ['date']

    min_cost = InvenTree.serializers.InvenTreeMoneySerializer(allow_null=True)
    min_cost_currency = InvenTree.serializers.InvenTreeCurrencySerializer()

    max_cost = InvenTree.serializers.InvenTreeMoneySerializer(allow_null=True)
    max_cost_currency = InvenTree.serializers.InvenTreeCurrencySerializer()

    stock_item_detail = OptionalField(
        serializer_class=stock_serializers.StockItemSerializer,
        serializer_kwargs={
            'source': 'stock_item',
            'read_only': True,
            'allow_null': True,
        },
        default_include=False,
        prefetch_fields=['stock_item'],
    )

    user_detail = OptionalField(
        serializer_class=UserSerializer,
        serializer_kwargs={'source': 'user', 'read_only': True, 'allow_null': True},
        default_include=False,
        prefetch_fields=['user'],
    )

    def __init__(self, *args, **kwargs):
        """Custom initialization for StockItemCostEntrySerializer.

        The 'user' field is set automatically from the request, and is not directly writeable.
        """
        super().__init__(*args, **kwargs)

        self.fields['user'].read_only = True


class StockItemCostSerializer(InvenTree.serializers.InvenTreeModelSerializer):
    """Serializer for the (read-only) StockItemCost summary model.

    This model is automatically recalculated from StockItemCostEntry records
    (see pricing.models), so every field here is read-only - it is exposed
    purely so that the calculated summary can be looked up or embedded.
    """

    class Meta:
        """Metaclass options."""

        model = StockItemCost
        fields = [
            'pk',
            'stock_item',
            'min_cost',
            'min_cost_currency',
            'max_cost',
            'max_cost_currency',
            'date',
        ]

        read_only_fields = fields

    min_cost = InvenTree.serializers.InvenTreeMoneySerializer(allow_null=True)
    min_cost_currency = InvenTree.serializers.InvenTreeCurrencySerializer()

    max_cost = InvenTree.serializers.InvenTreeMoneySerializer(allow_null=True)
    max_cost_currency = InvenTree.serializers.InvenTreeCurrencySerializer()
