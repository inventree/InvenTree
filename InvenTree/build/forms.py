# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit

from .models import Build


class EditBuildForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(EditBuildForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()

        self.helper.form_id = 'id-edit-part-form'
        self.helper.form_class = 'blueForms'
        self.helper.form_method = 'post'

        self.helper.add_input(Submit('submit', 'Submit'))

    class Meta:
        model = Build
        fields = [
            'title',
            'notes',
            'part',
            'batch',
            'quantity',
            'status',
            'completion_date',
        ]