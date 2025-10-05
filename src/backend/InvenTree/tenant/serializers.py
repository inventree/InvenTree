"""Serializers for the tenant app."""

from InvenTree.serializers import InvenTreeModelSerializer

from .models import Tenant


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
