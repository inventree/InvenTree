"""
Django Forms for interacting with Build objects
"""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from InvenTree.forms import HelperForm

from .models import Build


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
            'status',
            # 'completion_date',
        ]
