"""Tenant models for InvenTree multi-tenancy support."""

from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

import InvenTree.models


class Tenant(InvenTree.models.InvenTreeMetadataModel):
    """Model for managing tenants in the system.

    Tenants allow for data filtering and organization without user isolation.
    All users can access all tenants, but specific entities can be filtered by tenant.

    Attributes:
        name: Unique name for the tenant
        description: Optional description of the tenant
        code: Optional unique code/identifier for the tenant
        is_active: Whether this tenant is currently active
        contact_name: Optional contact person name
        contact_email: Optional contact email
        contact_phone: Optional contact phone number
    """

    class Meta:
        """Meta options for Tenant."""

        app_label = 'tenant'
        verbose_name = _('Tenant')
        verbose_name_plural = _('Tenants')
        ordering = ['name']

    @staticmethod
    def get_api_url():
        """Return the API URL associated with the Tenant model."""
        return reverse('api-tenant-list')

    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name=_('Name'),
        help_text=_('Unique name for the tenant'),
    )

    description = models.TextField(
        blank=True,
        verbose_name=_('Description'),
        help_text=_('Optional description of the tenant'),
    )

    code = models.CharField(
        max_length=50,
        unique=True,
        blank=True,
        null=True,
        verbose_name=_('Code'),
        help_text=_('Optional unique code/identifier for the tenant'),
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Active'),
        help_text=_('Whether this tenant is currently active'),
    )

    contact_name = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Contact Name'),
        help_text=_('Optional contact person name'),
    )

    contact_email = models.EmailField(
        blank=True,
        verbose_name=_('Contact Email'),
        help_text=_('Optional contact email'),
    )

    contact_phone = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_('Contact Phone'),
        help_text=_('Optional contact phone number'),
    )

    def __str__(self):
        """String representation of the tenant."""
        return self.name


class TenantMixin(models.Model):
    """Abstract mixin to add tenant filtering to models.

    Any model that inherits from this mixin will have a required tenant field
    and can be filtered by tenant in the API.

    The tenant field is required by default (not null, not blank).
    To make it optional, override the field in your model with blank=True, null=True.
    """

    class Meta:
        """Meta options for TenantMixin."""

        abstract = True

    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name='%(class)s_set',
        verbose_name=_('Tenant'),
        help_text=_('Tenant this entity belongs to'),
    )
