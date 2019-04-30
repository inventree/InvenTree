"""
Django Forms for interacting with Build objects
"""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from InvenTree.forms import HelperForm

from .models import Build, BuildItem


class EditBuildForm(HelperForm):
    """ Form for editing a Build object.
    """

    class Meta:
        model = Build
        fields = [
            'title',
            'part',
            'quantity',
            'batch',
            'URL',
            'notes',
        ]


class EditBuildItemForm(HelperForm):
    """ Form for adding a new BuildItem to a Build """

    class Meta:
        model = BuildItem
        fields = [
            'build',
            'stock_item',
            'quantity',
        ]
