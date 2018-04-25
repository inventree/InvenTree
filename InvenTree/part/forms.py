from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit

from .models import Part, PartCategory, BomItem
from .models import SupplierPart


class EditPartForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(EditPartForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()

        self.helper.form_id = 'id-edit-part-form'
        self.helper.form_method = 'post'

        self.helper.add_input(Submit('submit', 'Submit'))

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

        #self.helper.form_id = 'id-edit-part-form'
        #self.helper.form_method = 'post'

        self.helper.form_tag = False
        #self.helper.add_input(Submit('submit', 'Submit'))

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

        self.helper.form_id = 'id-edit-part-form'
        self.helper.form_method = 'post'

        self.helper.add_input(Submit('submit', 'Submit'))

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

            self.helper.form_id = 'id-edit-part-form'
            self.helper.form_class = 'blueForms'
            self.helper.form_method = 'post'

            self.helper.add_input(Submit('submit', 'Submit'))

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
