"""Serializers for the tenant app."""

from rest_framework import serializers

from InvenTree.serializers import InvenTreeModelSerializer

from .models import Tenant


class TenantSerializerMixin(serializers.Serializer):
    """Mixin to add tenant field to any serializer.

    This provides a modular way to add tenant support to any model serializer.
    Usage: Add this mixin to any serializer that has a tenant ForeignKey field.

    By default, the tenant field is required. To make it optional, override in your serializer:
        tenant = serializers.PrimaryKeyRelatedField(
            queryset=Tenant.objects.all(),
            allow_null=True,
            required=False,
        )
    """

    tenant = serializers.PrimaryKeyRelatedField(
        queryset=Tenant.objects.all(),
        allow_null=False,
        required=True,
        label='Tenant',
        help_text='Tenant this entity belongs to',
    )

    tenant_detail = serializers.SerializerMethodField(
        read_only=True, label='Tenant Detail'
    )

    def get_tenant_detail(self, obj):
        """Return detailed tenant information."""
        if hasattr(obj, 'tenant') and obj.tenant:
            return TenantBriefSerializer(obj.tenant).data
        return None


class TenantSerializer(InvenTreeModelSerializer):
    """Serializer for the Tenant model."""

    class Meta:
        """Meta options for TenantSerializer."""

        model = Tenant
        fields = [
            'pk',
            'name',
            'description',
            'code',
            'is_active',
            'contact_name',
            'contact_email',
            'contact_phone',
            'metadata',
        ]

        read_only_fields = ['pk']


class TenantBriefSerializer(InvenTreeModelSerializer):
    """Brief serializer for the Tenant model (for nested serialization)."""

    class Meta:
        """Meta options for TenantBriefSerializer."""

        model = Tenant
        fields = ['pk', 'name', 'code', 'is_active']

        read_only_fields = ['pk']
