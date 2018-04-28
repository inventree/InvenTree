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

        initial = kwargs.get('initial', {})

        for field in ['part']:
            if field in initial:
                self.fields['field'].disabled = True

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
