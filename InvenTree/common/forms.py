"""
Django forms for interacting with common objects
"""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from InvenTree.forms import HelperForm

from .models import InvenTreeSetting


class SettingEditForm(HelperForm):
    """
    Form for creating / editing a settings object
    """

    class Meta:
        model = InvenTreeSetting

        fields = [
            'value'
        ]
