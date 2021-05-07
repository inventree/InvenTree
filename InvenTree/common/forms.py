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

        # Setup FileManager
        file_manager.setup()
        # Get columns
        columns = file_manager.columns()
        # Get headers choices
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

        # Get FileManager
        file_manager = None
        if 'file_manager' in kwargs:
            file_manager = kwargs.pop('file_manager')

        if 'row_data' in kwargs:
            row_data = kwargs.pop('row_data')

        super().__init__(*args, **kwargs)

        # Setup FileManager
        file_manager.setup()
        # Get columns
        columns = file_manager.columns()

        # Create fields
        # Item selection
        for row in row_data:
            for col in row['data']:
                if col['column']['guess'] in file_manager.REQUIRED_HEADERS:
                    field_name = col['column']['guess'].lower() + '-' + str(row['index'] - 1)
                    if 'quantity' in col['column']['guess'].lower():
                        self.fields[field_name] = forms.CharField(
                            required=True,
                            widget=forms.NumberInput(attrs={
                                'name': 'quantity' + str(row['index']),
                                'class': 'numberinput',
                                'type': 'number',
                                'min': '1',
                                'step': 'any',
                                'value': row['quantity'],
                            })
                        )
                    else:
                        self.fields[field_name] = forms.Input(
                            required=True,
                            widget=forms.Select(attrs={
                            })
                        )
                elif col['column']['guess'] in file_manager.ITEM_MATCH_HEADERS:
                    print(f'{row["index"]=} | {col["column"]["guess"]=} | {row.get("item_match", "No Match")}')
                    
                    # Get item options
                    item_options = [(option.id, option) for option in row['item_options']]
                    # Get item match
                    item_match = row['item_match']

                    field_name = col['column']['guess'].lower() + '-' + str(row['index'] - 1)
                    self.fields[field_name] = forms.ChoiceField(
                        choices=[('', '-' * 10)] + item_options,
                        required=True,
                        widget=forms.Select(attrs={'class': 'bomselect'})
                    )
                    if item_match:
                        print(f'{item_match=}')
                        self.fields[field_name].initial = item_match.id
