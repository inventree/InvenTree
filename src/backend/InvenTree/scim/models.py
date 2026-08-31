"""Database models for the 'scim' app."""

import hashlib
import hmac
import secrets

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

import InvenTree.helpers


def _digest(secret: str) -> str:
    """Compute a hmac digest of a secret, seeded with the secret_key from settings."""
    return hmac.new(
        settings.SECRET_KEY.encode('utf-8'), secret.encode('utf-8'), hashlib.sha256
    ).hexdigest()


class ScimConfiguration(models.Model):
    """Simple model for storing config of SCIM."""

    class Meta:
        """Metaclass."""

        verbose_name = _('SCIM Configuration')

    enabled = models.BooleanField(
        default=False,
        verbose_name=_('Enabled'),
        help_text=_('Enable the SCIM provisioning endpoint'),
    )

    secret_digest = models.CharField(
        max_length=64,
        blank=True,
        verbose_name=_('Secret Digest'),
        help_text=_('HMAC digest of the current SCIM bearer secret'),
    )

    secret_generated = models.DateTimeField(
        null=True, blank=True, verbose_name=_('Secret Generated')
    )

    last_used = models.DateTimeField(null=True, blank=True, verbose_name=_('Last Used'))

    def __str__(self):
        """String representation of the SCIM configuration."""
        return 'SCIM Configuration'  # pragma: no cover

    def save(self, *args, **kwargs):
        """Ensure that only a single instance of this model can ever exist."""
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """Prevent deletion of the singleton configuration object."""

    @classmethod
    def load(cls) -> 'ScimConfiguration':
        """Return the (singleton) SCIM configuration object, creating it if required."""
        obj, _created = cls.objects.get_or_create(pk=1)
        return obj

    @property
    def has_secret(self) -> bool:
        """Return True if a bearer secret has been generated."""
        return bool(self.secret_digest)

    def generate_secret(self) -> str:
        """Generate a new bearer secret, persist its digest, and return the raw secret.

        The raw secret is only ever available at generation time - it cannot be
        recovered afterwards, only rotated.
        """
        secret = secrets.token_urlsafe(48)
        self.secret_digest = _digest(secret)
        self.secret_generated = InvenTree.helpers.current_time()
        self.last_used = None
        self.save()
        return secret

    def revoke(self):
        """Revoke the current secret and disable the SCIM provisioning."""
        self.enabled = False
        self.secret_digest = ''
        self.secret_generated = None
        self.save()

    def verify_secret(self, secret: str) -> bool:
        """Return True if the provided raw secret matches the stored digest."""
        if not self.enabled or not self.secret_digest or not secret:
            return False

        return hmac.compare_digest(self.secret_digest, _digest(secret))

    def mark_used(self):
        """Record that the SCIM endpoint was just used for a successful request."""
        self.last_used = InvenTree.helpers.current_time()
        self.save(update_fields=['last_used'])
