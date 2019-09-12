"""
Django Forms for interacting with Company app
"""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from InvenTree.forms import HelperForm

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
            'is_customer',
            'is_supplier',
            'notes'
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
            'MPN',
            'URL',
            'note',
            'base_cost',
            'multiple',
            'packaging',
            # 'lead_time'
        ]


class EditPriceBreakForm(HelperForm):
    """ Form for creating / editing a supplier price break """

    class Meta:
        model = SupplierPriceBreak
        fields = [
            'part',
            'quantity',
            'cost',
            'currency',
        ]
