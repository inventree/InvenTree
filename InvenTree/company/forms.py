"""
Django Forms for interacting with Company app
"""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from InvenTree.forms import HelperForm
from InvenTree.fields import RoundingDecimalFormField

from .models import Company
from .models import SupplierPart
from .models import SupplierPriceBreak


class EditCompanyForm(HelperForm):
    """ Form for editing a Company object """

    class Meta:
        model = Company
        fields = [
            'name',
            'description',
            'website',
            'address',
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


class EditSupplierPartForm(HelperForm):
    """ Form for editing a SupplierPart object """

    class Meta:
        model = SupplierPart
        fields = [
            'part',
            'supplier',
            'SKU',
            'description',
            'manufacturer',
            'manufacturer_name',
            'MPN',
            'link',
            'note',
            'base_cost',
            'multiple',
            'packaging',
            # 'lead_time'
        ]


class EditPriceBreakForm(HelperForm):
    """ Form for creating / editing a supplier price break """

    quantity = RoundingDecimalFormField(max_digits=10, decimal_places=5)

    cost = RoundingDecimalFormField(max_digits=10, decimal_places=5)

    class Meta:
        model = SupplierPriceBreak
        fields = [
            'part',
            'quantity',
            'cost',
            'currency',
        ]
