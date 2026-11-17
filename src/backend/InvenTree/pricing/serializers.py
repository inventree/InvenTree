"""DRF data serializers for the 'pricing' app."""

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from djmoney.contrib.exchange.exceptions import MissingRate
from djmoney.contrib.exchange.models import convert_money
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

import common.currency
import InvenTree.serializers
from importer.registry import register_importer
from InvenTree.mixins import DataImportExportSerializerMixin
from InvenTree.serializers import OptionalField
from users.serializers import UserSerializer

from .models import (
    PartInternalPriceBreak,
    PartPricing,
    PartSellPriceBreak,
    StockItemCost,
    StockItemCostEntry,
)


@register_importer()
class PartSalePriceSerializer(
    InvenTree.serializers.FilterableSerializerMixin,
    DataImportExportSerializerMixin,
    InvenTree.serializers.InvenTreeModelSerializer,
):
    """Serializer for sale prices for Part model."""

    no_filters = True

    class Meta:
        """Metaclass defining serializer fields."""

        model = PartSellPriceBreak
        fields = ['pk', 'part', 'quantity', 'price', 'price_currency']

    quantity = InvenTree.serializers.InvenTreeDecimalField()

    price = InvenTree.serializers.InvenTreeMoneySerializer(allow_null=True)

    price_currency = InvenTree.serializers.InvenTreeCurrencySerializer(
        help_text=_('Currency for this price break')
    )


@register_importer()
class PartInternalPriceSerializer(
    DataImportExportSerializerMixin, InvenTree.serializers.InvenTreeModelSerializer
):
    """Serializer for internal prices for Part model."""

    class Meta:
        """Metaclass defining serializer fields."""

        model = PartInternalPriceBreak
        fields = ['pk', 'part', 'quantity', 'price', 'price_currency']

    quantity = InvenTree.serializers.InvenTreeDecimalField()

    price = InvenTree.serializers.InvenTreeMoneySerializer(allow_null=True)

    price_currency = InvenTree.serializers.InvenTreeCurrencySerializer(
        help_text=_('Currency for this price break')
    )


@extend_schema_field(
    serializers.CharField(
        help_text=_('Select currency from available options')
        + '\n\n'
        + '\n'.join(
            f'* `{value}` - {label}'
            for value, label in common.currency.currency_code_mappings()
        )
        + "\n\nOther valid currencies may be found in the 'CURRENCY_CODES' global setting."
    )
)
class PartPricingCurrencySerializer(serializers.ChoiceField):
    """Serializer to allow annotating the schema to use String on currency fields."""


class PartPricingSerializer(InvenTree.serializers.InvenTreeModelSerializer):
    """Serializer for Part pricing information."""

    class Meta:
        """Metaclass defining serializer fields."""

        model = PartPricing
        fields = [
            'currency',
            'updated',
            'scheduled_for_update',
            'bom_cost_min',
            'bom_cost_max',
            'purchase_cost_min',
            'purchase_cost_max',
            'internal_cost_min',
            'internal_cost_max',
            'supplier_price_min',
            'supplier_price_max',
            'variant_cost_min',
            'variant_cost_max',
            'override_min',
            'override_min_currency',
            'override_max',
            'override_max_currency',
            'overall_min',
            'overall_max',
            'sale_price_min',
            'sale_price_max',
            'sale_history_min',
            'sale_history_max',
            'update',
        ]

    currency = InvenTree.serializers.InvenTreeCurrencySerializer(
        allow_null=True, read_only=True
    )

    updated = serializers.DateTimeField(allow_null=True, read_only=True)

    scheduled_for_update = serializers.BooleanField(read_only=True)

    # Custom serializers
    bom_cost_min = InvenTree.serializers.InvenTreeMoneySerializer(
        allow_null=True, read_only=True
    )
    bom_cost_max = InvenTree.serializers.InvenTreeMoneySerializer(
        allow_null=True, read_only=True
    )

    purchase_cost_min = InvenTree.serializers.InvenTreeMoneySerializer(
        allow_null=True, read_only=True
    )
    purchase_cost_max = InvenTree.serializers.InvenTreeMoneySerializer(
        allow_null=True, read_only=True
    )

    internal_cost_min = InvenTree.serializers.InvenTreeMoneySerializer(
        allow_null=True, read_only=True
    )
    internal_cost_max = InvenTree.serializers.InvenTreeMoneySerializer(
        allow_null=True, read_only=True
    )

    supplier_price_min = InvenTree.serializers.InvenTreeMoneySerializer(
        allow_null=True, read_only=True
    )
    supplier_price_max = InvenTree.serializers.InvenTreeMoneySerializer(
        allow_null=True, read_only=True
    )

    variant_cost_min = InvenTree.serializers.InvenTreeMoneySerializer(
        allow_null=True, read_only=True
    )
    variant_cost_max = InvenTree.serializers.InvenTreeMoneySerializer(
        allow_null=True, read_only=True
    )

    override_min = InvenTree.serializers.InvenTreeMoneySerializer(
        label=_('Minimum Price'),
        help_text=_('Override calculated value for minimum price'),
        allow_null=True,
        read_only=False,
        required=False,
    )

    override_min_currency = PartPricingCurrencySerializer(
        label=_('Minimum price currency'),
        read_only=False,
        required=False,
        choices=common.currency.currency_code_mappings(),
    )

    override_max = InvenTree.serializers.InvenTreeMoneySerializer(
        label=_('Maximum Price'),
        help_text=_('Override calculated value for maximum price'),
        allow_null=True,
        read_only=False,
        required=False,
    )

    override_max_currency = PartPricingCurrencySerializer(
        label=_('Maximum price currency'),
        read_only=False,
        required=False,
        choices=common.currency.currency_code_mappings(),
    )

    overall_min = InvenTree.serializers.InvenTreeMoneySerializer(
        allow_null=True, read_only=True
    )
    overall_max = InvenTree.serializers.InvenTreeMoneySerializer(
        allow_null=True, read_only=True
    )

    sale_price_min = InvenTree.serializers.InvenTreeMoneySerializer(
        allow_null=True, read_only=True
    )
    sale_price_max = InvenTree.serializers.InvenTreeMoneySerializer(
        allow_null=True, read_only=True
    )

    sale_history_min = InvenTree.serializers.InvenTreeMoneySerializer(
        allow_null=True, read_only=True
    )
    sale_history_max = InvenTree.serializers.InvenTreeMoneySerializer(
        allow_null=True, read_only=True
    )

    update = serializers.BooleanField(
        write_only=True,
        label=_('Update'),
        help_text=_('Update pricing for this part'),
        default=False,
        required=False,
        allow_null=True,
    )

    def validate(self, data):
        """Validate supplied pricing data."""
        super().validate(data)

        # Check that override_min is not greater than override_max
        # For a partial update, compare against the existing value of any field not provided
        def get_value(field):
            if field in data:
                return data[field]
            return getattr(self.instance, field, None)

        override_min = get_value('override_min')
        override_max = get_value('override_max')

        default_currency = common.currency.currency_code_default()

        if override_min is not None and override_max is not None:
            try:
                override_min = convert_money(override_min, default_currency)
                override_max = convert_money(override_max, default_currency)
            except MissingRate:
                raise ValidationError(
                    _(
                        'Could not convert from provided currencies to {currency}'
                    ).format(currency=default_currency)
                )

            if override_min > override_max:
                raise ValidationError({
                    'override_min': _(
                        'Minimum price must not be greater than maximum price'
                    ),
                    'override_max': _(
                        'Maximum price must not be less than minimum price'
                    ),
                })

        return data

    def save(self):
        """Called when the serializer is saved."""
        super().save()

        data = self.validated_data

        if data.get('update', False):
            # Update part pricing
            pricing = self.instance
            pricing.update_pricing()


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
            'cost_type',
            'cost_type_text',
            'source',
            'currency',
            'min_cost',
            'max_cost',
            'converted_currency',
            'converted_min_cost',
            'converted_max_cost',
            'date',
            'user',
            'user_detail',
            'source_data',
            'notes',
        ]

        read_only_fields = [
            'converted_currency',
            'converted_min_cost',
            'converted_max_cost',
            'date',
            'user',
        ]

    def __init__(self, *args, **kwargs):
        """Prevent an existing cost entry from being moved to a different stock item."""
        super().__init__(*args, **kwargs)

        if self.instance is not None and 'stock_item' in self.fields:
            self.fields['stock_item'].read_only = True

    cost_type_text = serializers.CharField(
        source='get_cost_type_display', read_only=True
    )

    currency = InvenTree.serializers.InvenTreeCurrencySerializer(
        help_text=_('Currency for the minimum and maximum cost')
    )

    min_cost = InvenTree.serializers.InvenTreeDecimalField(
        allow_null=True, required=False, help_text=_('Minimum unit cost')
    )

    max_cost = InvenTree.serializers.InvenTreeDecimalField(
        allow_null=True, required=False, help_text=_('Maximum unit cost')
    )

    converted_min_cost = InvenTree.serializers.InvenTreeDecimalField(
        read_only=True, allow_null=True
    )

    converted_max_cost = InvenTree.serializers.InvenTreeDecimalField(
        read_only=True, allow_null=True
    )

    user_detail = OptionalField(
        serializer_class=UserSerializer,
        serializer_kwargs={'source': 'user', 'read_only': True, 'allow_null': True},
        prefetch_fields=['user'],
    )


class StockItemCostSerializer(InvenTree.serializers.InvenTreeModelSerializer):
    """Serializer for the (read-only) StockItemCost summary model.

    This model is calculated automatically from StockItemCostEntry records.
    """

    class Meta:
        """Metaclass options."""

        model = StockItemCost
        fields = [
            'pk',
            'stock_item',
            'currency',
            'min_cost',
            'max_cost',
            'incomplete',
            'date',
        ]

        read_only_fields = fields

    min_cost = InvenTree.serializers.InvenTreeDecimalField(
        read_only=True, allow_null=True
    )

    max_cost = InvenTree.serializers.InvenTreeDecimalField(
        read_only=True, allow_null=True
    )


class StockItemCostBriefSerializer(InvenTree.serializers.InvenTreeModelSerializer):
    """Brief (read-only) serializer for the StockItemCost summary model.

    Used to embed the cost summary within a StockItem (see StockItemSerializer.pricing_detail).
    """

    class Meta:
        """Metaclass options."""

        model = StockItemCost
        fields = ['currency', 'min_cost', 'max_cost', 'incomplete', 'date']

        read_only_fields = fields

    min_cost = InvenTree.serializers.InvenTreeDecimalField(
        read_only=True, allow_null=True
    )

    max_cost = InvenTree.serializers.InvenTreeDecimalField(
        read_only=True, allow_null=True
    )
