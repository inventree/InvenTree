from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit

from .models import Part, PartCategory, BomItem


class EditPartForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(EditPartForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()

        self.helper.form_id = 'id-edit-part-form'
        #self.helper.form_class = 'blueForms'
        self.helper.form_method = 'post'
        #self.helper.form_action = 'submit'

        self.helper.add_input(Submit('submit', 'Submit'))

    class Meta:
        model = Part
        fields = [
            'category',
            'name',
            'description',
            'IPN',
            'URL',
            'minimum_stock',
            'trackable',
            'purchaseable',
        ]


class EditCategoryForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(EditCategoryForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()

        self.helper.form_id = 'id-edit-part-form'
        #self.helper.form_class = 'blueForms'
        self.helper.form_method = 'post'
        #self.helper.form_action = 'submit'

        self.helper.add_input(Submit('submit', 'Submit'))

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
        #self.helper.form_class = 'blueForms'
        self.helper.form_method = 'post'
        #self.helper.form_action = 'submit'

        self.helper.add_input(Submit('submit', 'Submit'))

    class Meta:
        model = BomItem
        fields = [
            'part',
            'sub_part',
            'quantity'
        ]