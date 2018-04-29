# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from InvenTree.forms import HelperForm

from .models import Build


class EditBuildForm(HelperForm):

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
