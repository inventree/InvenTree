"""Models for sample plugin."""

from django.contrib.auth.models import User

# from django.contrib.contenttypes.fields import GenericForeignKey
# from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

import InvenTree.models


class SampleModel(InvenTree.models.MetadataMixin, models.Model):
    """A sample model for testing full app integrations."""

    string_field = models.CharField(max_length=100, verbose_name=_('String field'))
    date_field = models.DateTimeField(
        auto_now_add=True, editable=False, verbose_name=_('Date field')
    )
    user_field = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('User field'),
        related_name='sample_plugin',
    )
    boolean_field = models.BooleanField(default=False, verbose_name=_('Boolean field'))
    # content_type = models.ForeignKey('ContentType', on_delete=models.CASCADE)
    # object_id = models.PositiveIntegerField()
    # content_object = GenericForeignKey('content_type', 'object_id')

    class Meta:
        """Meta class."""

        verbose_name = _('Sample Model')
        verbose_name_plural = _('Sample Models')
        app_label = 'app_sample'

    @staticmethod
    def get_api_url():
        """Return API detail URL for this object."""
        return reverse('plugin:app_sample:api-list')
