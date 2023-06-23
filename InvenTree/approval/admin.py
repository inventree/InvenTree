"""Admin class definitions for approval app"""

from django.contrib import admin

from .models import Approval, ApprovalDecision


class ApprovalDecisionInline(admin.TabularInline):
    """Inline for ApprovalDecision."""

    model = ApprovalDecision


@admin.register(Approval)
class ApprovalAdmin(admin.ModelAdmin):
    """Admin class for Approval model."""

    resource_class = ApprovalDecisionInline

    list_display = ('name', 'description', 'finalised')

    search_fields = [
        'name',
        'description',
        'reference',
    ]

    inlines = [ApprovalDecisionInline,]
