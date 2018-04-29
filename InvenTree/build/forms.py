# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import forms
from crispy_forms.helper import FormHelper

from .models import Build


class EditBuildForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(EditBuildForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()

        self.helper.form_tag = False

    class Meta:
        model = Build
        fields = [
            'title',
            'part',
            'quantity',
            'batch',
            'notes',
#            'status',
#            'completion_date',
        ]
