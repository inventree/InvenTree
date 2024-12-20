"""Admin class definitions for the 'part' app."""

from django.contrib import admin

from part import models


class PartParameterInline(admin.TabularInline):
    """Inline for part parameter data."""

    model = models.PartParameter


@admin.register(models.Part)
class PartAdmin(admin.ModelAdmin):
    """Admin class for the Part model."""

    list_display = ('full_name', 'description', 'total_stock', 'category')

    list_filter = ('active', 'assembly', 'is_template', 'virtual')

    search_fields = (
        'name',
        'description',
        'category__name',
        'category__description',
        'IPN',
    )

    autocomplete_fields = [
        'variant_of',
        'category',
        'default_location',
        'default_supplier',
        'bom_checked_by',
        'creation_user',
    ]

    inlines = [PartParameterInline]


@admin.register(models.PartPricing)
class PartPricingAdmin(admin.ModelAdmin):
    """Admin class for PartPricing model."""

    list_display = ('part', 'overall_min', 'overall_max')

    autocomplete_fields = ['part']


@admin.register(models.PartStocktake)
class PartStocktakeAdmin(admin.ModelAdmin):
    """Admin class for PartStocktake model."""

    list_display = ['part', 'date', 'quantity', 'user']


@admin.register(models.PartStocktakeReport)
class PartStocktakeReportAdmin(admin.ModelAdmin):
    """Admin class for PartStocktakeReport model."""

    list_display = ['date', 'user']


@admin.register(models.PartCategory)
class PartCategoryAdmin(admin.ModelAdmin):
    """Admin class for the PartCategory model."""

    list_display = ('name', 'pathstring', 'description')

    search_fields = ('name', 'description')

    autocomplete_fields = ('parent', 'default_location')


@admin.register(models.PartRelated)
class PartRelatedAdmin(admin.ModelAdmin):
    """Class to manage PartRelated objects."""

    autocomplete_fields = ('part_1', 'part_2')


@admin.register(models.PartTestTemplate)
class PartTestTemplateAdmin(admin.ModelAdmin):
    """Admin class for the PartTestTemplate model."""

    list_display = ('part', 'test_name', 'required')
    readonly_fields = ['key']

    autocomplete_fields = ('part',)


@admin.register(models.BomItem)
class BomItemAdmin(admin.ModelAdmin):
    """Admin class for the BomItem model."""

    list_display = ('part', 'sub_part', 'quantity')

    search_fields = (
        'part__name',
        'part__description',
        'sub_part__name',
        'sub_part__description',
    )

    autocomplete_fields = ('part', 'sub_part')


@admin.register(models.PartParameterTemplate)
class ParameterTemplateAdmin(admin.ModelAdmin):
    """Admin class for the PartParameterTemplate model."""

    list_display = ('name', 'units')

    search_fields = ('name', 'units')


@admin.register(models.PartParameter)
class ParameterAdmin(admin.ModelAdmin):
    """Admin class for the PartParameter model."""

    list_display = ('part', 'template', 'data')

    autocomplete_fields = ('part', 'template')


@admin.register(models.PartCategoryParameterTemplate)
class PartCategoryParameterAdmin(admin.ModelAdmin):
    """Admin class for the PartCategoryParameterTemplate model."""

    autocomplete_fields = ('category', 'parameter_template')


@admin.register(models.PartSellPriceBreak)
class PartSellPriceBreakAdmin(admin.ModelAdmin):
    """Admin class for the PartSellPriceBreak model."""

    class Meta:
        """Metaclass options."""

        model = models.PartSellPriceBreak

    list_display = ('part', 'quantity', 'price')


@admin.register(models.PartInternalPriceBreak)
class PartInternalPriceBreakAdmin(admin.ModelAdmin):
    """Admin class for the PartInternalPriceBreak model."""

    class Meta:
        """Metaclass options."""

        model = models.PartInternalPriceBreak

    list_display = ('part', 'quantity', 'price')

    autocomplete_fields = ('part',)
