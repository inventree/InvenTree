"""Admin functionality for the 'label' app"""

from django import forms
from django.contrib import admin
from django.utils.translation import gettext_lazy as _

import label.models
from .models import (LabelTemplate, PartLabel, StockItemLabel,
                     StockLocationLabel, BuildLineLabel)

class LabelAdminForm(forms.ModelForm):
    """Custom form for the label's admin form to inject non-model fields"""
    class Meta:
        """Meta is necessary to set a more reasonable field order"""
        model = LabelTemplate
        fields = ['metadata', 'name', 'description', 'label', 'enabled', 'width', 'height',
                  'filename_pattern', 'multipage', 'pagesize_preset', 'page_orientation',
                  'page_width', 'page_height', 'multipage_border']

    pagesize_preset = forms.ChoiceField(
        choices=[
            ('custom', _('Custom')),
            ('210x297', _('A4')),
            ('297x420', _('A3')),
            ('148x210', _('A5')),
            ('215.9x279.4', _('Letter')),
            ('215.9x355.6', _('Legal')),
        ],
        label=_('Preset paper size'),
    )

    page_orientation = forms.ChoiceField(
        choices=[('portrait', _('Portrait')), ('landscape', _('Landscape'))],
    )


class StockItemLabelAdminForm(LabelAdminForm):
    """Custom form for the Stock item label's admin form"""
    class Meta:
        """Meta is just for adding the fields field to the right position (last field)"""
        model = StockItemLabel
        fields = LabelAdminForm.Meta.fields + ["filters"]


class StockLocationLabelAdminForm(LabelAdminForm):
    """Custom form for the Stock location label's admin form"""
    class Meta:
        """Meta is just for adding the fields field to the right position (last field)"""
        model = StockLocationLabel
        fields = LabelAdminForm.Meta.fields + ["filters"]


class PartLabelAdminForm(LabelAdminForm):
    """Custom form for the Part label's admin form"""
    class Meta:
        """Meta is just for adding the fields field to the right position (last field)"""
        model = PartLabel
        fields = LabelAdminForm.Meta.fields + ["filters"]

class BuildLineLabelAdminForm(LabelAdminForm):
    """Custom form for the Build line label's admin form"""
    class Meta:
        """Meta is just for adding the fields field to the right position (last field)"""
        model = PartLabel
        fields = LabelAdminForm.Meta.fields + ["filters"]


class LabelAdmin(admin.ModelAdmin):
    """Admin class for the various label models"""
    form = LabelAdminForm

    class Media:
        """For multi label input tweaks"""
        js = (
            'script/inventree/label_admin.js',
        )

class StockLabelAdmin(LabelAdmin):
    """Admin class for the Stock label models"""
    form = StockItemLabelAdminForm


class StockItemLabelAdmin(LabelAdmin):
    """Admin class for the Stock location label models"""
    form = StockLocationLabelAdminForm


class PartLabelAdmin(LabelAdmin):
    """Admin class for the Stock location label models"""
    form = PartLabelAdminForm

class BuildLineLabel(LabelAdmin):
    """Admin class for the Build line label models"""
    form = BuildLineLabelAdminForm

admin.site.register(label.models.StockItemLabel, LabelAdmin)
admin.site.register(label.models.StockLocationLabel, LabelAdmin)
admin.site.register(label.models.PartLabel, LabelAdmin)
admin.site.register(label.models.BuildLineLabel, LabelAdmin)

