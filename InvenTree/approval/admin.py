"""Admin class definitions for approval app"""

from django.contrib import admin

from .models import Approval, ApprovalDecision


class ApprovalDecisionInline(admin.TabularInline):
    """Inline for supplier-part pricing"""

    model = ApprovalDecision


@admin.register(Approval)
class ApprovalAdmin(admin.ModelAdmin):
    """Admin class for the SupplierPart model"""

    resource_class = ApprovalDecisionInline

    list_display = ('name', 'description', 'finalised')

    search_fields = [
        'name',
        'description',
        'reference',
    ]

    inlines = [ApprovalDecisionInline,]
