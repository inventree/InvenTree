"""
Django Forms for interacting with Build objects
"""

# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _
from django import forms

from InvenTree.forms import HelperForm

from .models import Build


class BuildOutputCreateForm(HelperForm):
    """
    Form for creating a new build output.
    """

    def __init__(self, *args, **kwargs):

        build = kwargs.pop('build', None)

        if build:
            self.field_placeholder['serial_numbers'] = build.part.getSerialNumberString()

        super().__init__(*args, **kwargs)

    field_prefix = {
        'serial_numbers': 'fa-hashtag',
    }

    output_quantity = forms.IntegerField(
        label=_('Quantity'),
        help_text=_('Enter quantity for build output'),
    )

    serial_numbers = forms.CharField(
        label=_('Serial Numbers'),
        required=False,
        help_text=_('Enter serial numbers for build outputs'),
    )

    confirm = forms.BooleanField(
        required=True,
        label=_('Confirm'),
        help_text=_('Confirm creation of build output'),
    )

    class Meta:
        model = Build
        fields = [
            'output_quantity',
            'batch',
            'serial_numbers',
            'confirm',
        ]


class BuildOutputDeleteForm(HelperForm):
    """
    Form for deleting a build output.
    """

    confirm = forms.BooleanField(
        required=False,
        label=_('Confirm'),
        help_text=_('Confirm deletion of build output')
    )

    output_id = forms.IntegerField(
        required=True,
        widget=forms.HiddenInput()
    )

    class Meta:
        model = Build
        fields = [
            'confirm',
            'output_id',
        ]


class CompleteBuildForm(HelperForm):
    """
    Form for marking a build as complete
    """

    confirm = forms.BooleanField(
        required=True,
        label=_('Confirm'),
        help_text=_('Mark build as complete'),
    )

    class Meta:
        model = Build
        fields = [
            'confirm',
        ]


class CancelBuildForm(HelperForm):
    """ Form for cancelling a build """

    confirm_cancel = forms.BooleanField(required=False, label=_('Confirm cancel'), help_text=_('Confirm build cancellation'))

    class Meta:
        model = Build
        fields = [
            'confirm_cancel'
        ]
