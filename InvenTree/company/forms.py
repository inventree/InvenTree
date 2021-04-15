"""
Django Forms for interacting with Company app
"""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from InvenTree.forms import HelperForm
from InvenTree.fields import RoundingDecimalFormField

from django.utils.translation import ugettext_lazy as _
import django.forms

import djmoney.settings
from djmoney.forms.fields import MoneyField

import common.settings

from .models import Company
from .models import ManufacturerPart
from .models import SupplierPart
from .models import SupplierPriceBreak


class EditCompanyForm(HelperForm):
    """ Form for editing a Company object """

    field_prefix = {
        'website': 'fa-globe-asia',
        'email': 'fa-at',
        'address': 'fa-envelope',
        'contact': 'fa-user-tie',
        'phone': 'fa-phone',
    }

    currency = django.forms.ChoiceField(
        required=False,
        label=_('Currency'),
        help_text=_('Default currency used for this company'),
        choices=[('', '----------')] + djmoney.settings.CURRENCY_CHOICES,
        initial=common.settings.currency_code_default,
    )

    class Meta:
        model = Company
        fields = [
            'name',
            'description',
            'website',
            'address',
            'currency',
            'phone',
            'email',
            'contact',
            'is_supplier',
            'is_manufacturer',
            'is_customer',
        ]


class CompanyImageForm(HelperForm):
    """ Form for uploading a Company image """

    class Meta:
        model = Company
        fields = [
            'image'
        ]


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


class EditManufacturerPartForm(HelperForm):
    """ Form for editing a ManufacturerPart object """

    field_prefix = {
        'link': 'fa-link',
        'MPN': 'fa-hashtag',
    }

    class Meta:
        model = ManufacturerPart
        fields = [
            'part',
            'manufacturer',
            'MPN',
            'description',
            'link',
        ]


class EditSupplierPartForm(HelperForm):
    """ Form for editing a SupplierPart object """

    field_prefix = {
        'link': 'fa-link',
        'SKU': 'fa-hashtag',
        'note': 'fa-pencil-alt',
    }

    single_pricing = MoneyField(
        label=_('Single Price'),
        default_currency='USD',
        help_text=_('Single quantity price'),
        decimal_places=4,
        max_digits=19,
        required=False,
    )

    manufacturer = django.forms.ChoiceField(
        required=False,
        help_text=_('Select manufacturer'),
        choices=[],
    )

    MPN = django.forms.CharField(
        required=False,
        help_text=_('Manufacturer Part Number'),
        max_length=100,
        label=_('MPN'),
    )

    class Meta:
        model = SupplierPart
        fields = [
            'part',
            'supplier',
            'SKU',
            'manufacturer',
            'MPN',
            'description',
            'link',
            'note',
            'single_pricing',
            # 'base_cost',
            # 'multiple',
            'packaging',
        ]

    def get_manufacturer_choices(self):
        """ Returns tuples for all manufacturers """
        empty_choice = [('', '----------')]

        manufacturers = [(manufacturer.id, manufacturer.name) for manufacturer in Company.objects.filter(is_manufacturer=True)]
        
        return empty_choice + manufacturers

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['manufacturer'].choices = self.get_manufacturer_choices()


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
