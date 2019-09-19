"""
Helper forms which subclass Django forms to provide additional functionality
"""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import forms
from crispy_forms.helper import FormHelper
from django.contrib.auth.models import User


class HelperForm(forms.ModelForm):
    """ Provides simple integration of crispy_forms extension. """

    def __init__(self, *args, **kwargs):
        super(forms.ModelForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()

        self.helper.form_tag = False


class DeleteForm(forms.Form):
    """ Generic deletion form which provides simple user confirmation
    """

    confirm_delete = forms.BooleanField(
        required=False,
        initial=False,
        help_text='Confirm item deletion'
    )

    class Meta:
        fields = [
            'confirm_delete'
        ]


class EditUserForm(HelperForm):
    """ Form for editing user information
    """

    class Meta:
        model = User
        fields = [
            'username',
            'first_name',
            'last_name',
            'email'
        ]


class SetPasswordForm(HelperForm):
    """ Form for setting user password
    """

    enter_password = forms.CharField(max_length=100,
                                     min_length=8,
                                     required=True,
                                     initial='',
                                     widget=forms.PasswordInput(attrs={'autocomplete': 'off'}),
                                     help_text='Enter new password')

    confirm_password = forms.CharField(max_length=100,
                                       min_length=8,
                                       required=True,
                                       initial='',
                                       widget=forms.PasswordInput(attrs={'autocomplete': 'off'}),
                                       help_text='Confirm new password')

    class Meta:
        model = User
        fields = [
            'enter_password',
            'confirm_password'
        ]
