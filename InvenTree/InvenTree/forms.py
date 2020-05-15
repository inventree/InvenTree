"""
Helper forms which subclass Django forms to provide additional functionality
"""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field
from crispy_forms.bootstrap import PrependedAppendedText
from django.contrib.auth.models import User


class HelperForm(forms.ModelForm):
    """ Provides simple integration of crispy_forms extension. """

    # Custom field decorations can be specified here, per form class
    prefix = {}
    suffix = {}
    placeholder = {}

    def __init__(self, *args, **kwargs):
        super(forms.ModelForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()

        self.helper.form_tag = False

        """
        Create a default 'layout' for this form.
        Ref: https://django-crispy-forms.readthedocs.io/en/latest/layouts.html
        This is required to do fancy things later (like adding PrependedText, etc).

        Simply create a 'blank' layout for each available field.
        """

        layouts = []

        for field in self.fields:
            prefix = self.prefix.get(field, None)
            suffix = self.suffix.get(field, None)
            placeholder = self.placeholder.get(field, None)

            # Look for font-awesome icons
            if prefix and prefix.startswith('fa-'):
                prefix = "<span class='fas {fa}'></span>".format(fa=prefix)

            if suffix and suffix.startswith('fa-'):
                suffix = "<span class='fas {fa}'></span>".format(fa=suffix)

            if prefix or suffix or placeholder:
                layouts.append(
                    Field(
                        PrependedAppendedText(
                            field,
                            prepended_text=prefix,
                            appended_text=suffix,
                            placeholder=placeholder
                        )
                    )
                )

            else:
                layouts.append(Field(field))

        self.helper.layout = Layout(*layouts)


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
