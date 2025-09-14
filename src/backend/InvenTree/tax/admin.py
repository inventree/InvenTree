"""Admin interface for tax models."""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import TaxConfiguration


@admin.register(TaxConfiguration)
class TaxConfigurationAdmin(admin.ModelAdmin):
    """Admin interface for TaxConfiguration model."""

    list_display = [
        'name',
        'year',
        'rate',
        'currency',
        'is_active',
        'is_inclusive',
        'applies_to_sales',
        'applies_to_purchases',
    ]

    list_filter = [
        'year',
        'is_active',
        'is_inclusive',
        'applies_to_sales',
        'applies_to_purchases',
        'currency',
    ]

    search_fields = ['name', 'description']

    ordering = ['-year', '-is_active']

    fieldsets = (
        (
            _('Basic Information'),
            {'fields': ('name', 'description', 'year', 'is_active')},
        ),
        (_('Tax Settings'), {'fields': ('rate', 'currency', 'is_inclusive')}),
        (_('Application'), {'fields': ('applies_to_sales', 'applies_to_purchases')}),
        (_('Metadata'), {'fields': ('metadata',), 'classes': ('collapse',)}),
    )
