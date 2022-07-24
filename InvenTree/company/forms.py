"""Django Forms for interacting with Company app."""

import django.forms
from django.utils.translation import gettext_lazy as _

from InvenTree.forms import HelperForm

from .models import Company


class CompanyImageDownloadForm(HelperForm):
    """Form for downloading an image from a URL."""

    url = django.forms.URLField(
        label=_('URL'),
        help_text=_('Image URL'),
        required=True
    )

    class Meta:
        """Metaclass options."""

        model = Company
        fields = [
            'url',
        ]
