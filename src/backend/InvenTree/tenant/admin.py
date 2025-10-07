"""Admin interface for the tenant app."""

from django.contrib import admin

from .models import Tenant


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    """Admin interface for Tenant model."""

    list_display = ('name', 'code', 'is_active', 'contact_name', 'contact_email')
    list_filter = ('is_active',)
    search_fields = ('name', 'description', 'code', 'contact_name', 'contact_email')
    ordering = ('name',)

    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of tenants to avoid accidental data loss."""
        return False
