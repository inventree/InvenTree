from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit

from .models import Company


"""
class EditSupplierOrderForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(EditSupplierOrderForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()

        self.helper.form_id = 'id-edit-part-form'
        self.helper.form_class = 'blueForms'
        self.helper.form_method = 'post'

        self.helper.add_input(Submit('submit', 'Submit'))

    class Meta:
        model = SupplierOrder
        fields = [
            'internal_ref',
            'supplier',
            'notes',
            'issued_date',
        ]
"""


class EditCompanyForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(EditCompanyForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()

        self.helper.form_id = 'id-edit-part-form'
        self.helper.form_class = 'blueForms'
        self.helper.form_method = 'post'

        self.helper.add_input(Submit('submit', 'Submit'))

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
            'image',
            'is_customer',
            'is_supplier',
            'notes'
        ]
