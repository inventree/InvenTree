"""Admin class definitions for the 'pricing' app."""

from django.contrib import admin

from pricing import models


@admin.register(models.PartPricing)
class PartPricingAdmin(admin.ModelAdmin):
    """Admin class for PartPricing model."""

    list_display = ('part', 'overall_min', 'overall_max')

    search_fields = ['part__name', 'part__IPN', 'part__description']

    autocomplete_fields = ['part']


@admin.register(models.PartSellPriceBreak)
class PartSellPriceBreakAdmin(admin.ModelAdmin):
    """Admin class for the PartSellPriceBreak model."""

    class Meta:
        """Metaclass options."""

        model = models.PartSellPriceBreak

    list_display = ('part', 'quantity', 'price')

    search_fields = ['part__name', 'part__IPN']

    autocomplete_fields = ('part',)


@admin.register(models.PartInternalPriceBreak)
class PartInternalPriceBreakAdmin(admin.ModelAdmin):
    """Admin class for the PartInternalPriceBreak model."""

    class Meta:
        """Metaclass options."""

        model = models.PartInternalPriceBreak

    list_display = ('part', 'quantity', 'price')

    search_fields = ['part__name', 'part__IPN']

    autocomplete_fields = ('part',)
