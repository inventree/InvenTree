from django import forms
from crispy_forms.helper import FormHelper

from .models import Part, PartCategory, BomItem
from .models import SupplierPart


class EditPartForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(EditPartForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()

        self.helper.form_tag = False

        initial = kwargs.get('initial', {})

        if 'category' in initial:
            self.fields['category'].disabled = True

    class Meta:
        model = Part
        fields = [
            'category',
            'name',
            'description',
            'IPN',
            'URL',
            'default_location',
            'default_supplier',
            'minimum_stock',
            'buildable',
            'trackable',
            'purchaseable',
            'salable',
            'notes',
        ]


class EditCategoryForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(EditCategoryForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()

        self.helper.form_tag = False

        initial = kwargs.get('initial', {})

        if 'category' in initial:
            self.fields['parent'].disabled = True

    class Meta:
        model = PartCategory
        fields = [
            'parent',
            'name',
            'description'
        ]


class EditBomItemForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(EditBomItemForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()

        self.helper.form_method = 'post'

        self.helper.form_tag = False

        initial = kwargs.get('initial', {})

        for field in ['part', 'sub_part']:
            if field in initial:
                self.fields[field].disabled = True

    class Meta:
        model = BomItem
        fields = [
            'part',
            'sub_part',
            'quantity'
        ]


class EditSupplierPartForm(forms.ModelForm):
        def __init__(self, *args, **kwargs):
            super(EditSupplierPartForm, self).__init__(*args, **kwargs)
            self.helper = FormHelper()

            self.helper.form_tag = False

            initial = kwargs.get('initial', {})

            for field in ['supplier', 'part']:
                if field in initial:
                    self.fields[field].disabled = True

        class Meta:
            model = SupplierPart
            fields = [
                'supplier',
                'SKU',
                'part',
                'description',
                'URL',
                'manufacturer',
                'MPN',
            ]
