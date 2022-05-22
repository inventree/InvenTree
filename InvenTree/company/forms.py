"""
Django Forms for interacting with Company app
"""

import django.forms
from django.utils.translation import gettext_lazy as _

from InvenTree.fields import RoundingDecimalFormField
from InvenTree.forms import HelperForm

from .models import Company, SupplierPriceBreak


class CompanyImageDownloadForm(HelperForm):
    """
    Form for downloading an image from a URL
    """

    url = django.forms.URLField(
        label=_('URL'),
        help_text=_('Image URL'),
        required=True
    )

    class Meta:
        model = Company
        fields = [
            'url',
        ]


class EditPriceBreakForm(HelperForm):
    """ Form for creating / editing a supplier price break """

    quantity = RoundingDecimalFormField(
        max_digits=10,
        decimal_places=5,
        label=_('Quantity'),
        help_text=_('Price break quantity'),
    )

    class Meta:
        model = SupplierPriceBreak
        fields = [
            'part',
            'quantity',
            'price',
        ]
