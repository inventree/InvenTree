"""Admin class for the 'company' app."""

from django.contrib import admin

import company.serializers

from .models import (
    Address,
    Company,
    Contact,
    ManufacturerPart,
    SupplierPart,
    SupplierPriceBreak,
)


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    """Admin class for the Company model."""

    serializer_class = company.serializers.CompanySerializer

    list_display = ('name', 'website', 'contact')

    search_fields = ['name', 'description']


class SupplierPriceBreakInline(admin.TabularInline):
    """Inline for supplier-part pricing."""

    model = SupplierPriceBreak


@admin.register(SupplierPart)
class SupplierPartAdmin(admin.ModelAdmin):
    """Admin class for the SupplierPart model."""

    list_display = ('part', 'supplier', 'SKU')

    search_fields = ['supplier__name', 'part__name', 'manufacturer_part__MPN', 'SKU']

    inlines = [SupplierPriceBreakInline]

    autocomplete_fields = ('part', 'supplier', 'manufacturer_part')


@admin.register(ManufacturerPart)
class ManufacturerPartAdmin(admin.ModelAdmin):
    """Admin class for ManufacturerPart model."""

    list_display = ('part', 'manufacturer', 'MPN')

    search_fields = ['manufacturer__name', 'part__name', 'MPN']

    autocomplete_fields = ('part', 'manufacturer')


@admin.register(SupplierPriceBreak)
class SupplierPriceBreakAdmin(admin.ModelAdmin):
    """Admin class for the SupplierPriceBreak model."""

    list_display = ('part', 'quantity', 'price')

    autocomplete_fields = ('part',)


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    """Admin class for the Address model."""

    list_display = ('company', 'line1', 'postal_code', 'country')

    search_fields = ['company', 'country', 'postal_code']

    autocomplete_fields = ['company']


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    """Admin class for the Contact model."""

    list_display = ('company', 'name', 'role', 'email', 'phone')

    search_fields = ['company', 'name', 'email']

    autocomplete_fields = ['company']
