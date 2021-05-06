"""
Django forms for interacting with common objects
"""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import forms
from django.utils.translation import gettext as _

from InvenTree.forms import HelperForm

from .files import FileManager
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


class UploadFile(forms.Form):
    """ Step 1 of FileManagementFormView """

    file = forms.FileField(
        label=_('File'),
        help_text=_('Select file to upload'),
    )

    def __init__(self, *args, **kwargs):
        """ Update label and help_text """

        # Get file name
        name = None
        if 'name' in kwargs:
            name = kwargs.pop('name')

        super().__init__(*args, **kwargs)

        if name:
            # Update label and help_text with file name
            self.fields['file'].label = _(f'{name.title()} File')
            self.fields['file'].help_text = _(f'Select {name} file to upload')

    def clean_file(self):
        """
            Run tabular file validation.
            If anything is wrong with the file, it will raise ValidationError
        """

        file = self.cleaned_data['file']

        # Validate file using FileManager class - will perform initial data validation
        # (and raise a ValidationError if there is something wrong with the file)
        FileManager.validate(file)

        return file


class MatchField(forms.Form):
    """ Step 2 of FileManagementFormView """
    
    def __init__(self, *args, **kwargs):

        # Get FileManager
        file_manager = None
        if 'file_manager' in kwargs:
            file_manager = kwargs.pop('file_manager')

        super().__init__(*args, **kwargs)

        # Setup headers
        file_manager.setup()
        columns = file_manager.columns()
        # Find headers choices
        headers_choices = [(header, header) for header in file_manager.HEADERS]
        
        # Create column fields
        for col in columns:
            field_name = col['name']
            self.fields[field_name] = forms.ChoiceField(
                choices=[('', '-' * 10)] + headers_choices,
                required=False,
            )
            if col['guess']:
                self.fields[field_name].initial = col['guess']


class MatchItem(forms.Form):
    """ Step 3 of FileManagementFormView """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
