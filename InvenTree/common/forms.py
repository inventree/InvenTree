"""
Django forms for interacting with common objects
"""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import forms
from django.utils.translation import gettext as _

from djmoney.forms.fields import MoneyField

from InvenTree.forms import HelperForm
from InvenTree.helpers import clean_decimal

from common.settings import currency_code_default

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
                widget=forms.Select(attrs={
                    'class': 'select fieldselect',
                })
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
        else:
            row_data = None

        super().__init__(*args, **kwargs)

        # Setup FileManager
        file_manager.setup()

        # Create fields
        if row_data:
            # Navigate row data
            for row in row_data:
                # Navigate column data
                for col in row['data']:
                    # Get column matching
                    col_guess = col['column'].get('guess', None)

                    # Create input for required headers
                    if col_guess in file_manager.REQUIRED_HEADERS:
                        # Set field name
                        field_name = col_guess.lower() + '-' + str(row['index'])
                        # Set field input box
                        if 'quantity' in col_guess.lower():
                            self.fields[field_name] = forms.CharField(
                                required=False,
                                widget=forms.NumberInput(attrs={
                                    'name': 'quantity' + str(row['index']),
                                    'class': 'numberinput',  # form-control',
                                    'type': 'number',
                                    'min': '0',
                                    'step': 'any',
                                    'value': clean_decimal(row.get('quantity', '')),
                                })
                            )

                    # Create item selection box
                    elif col_guess in file_manager.ITEM_MATCH_HEADERS:
                        # Get item options
                        item_options = [(option.id, option) for option in row['item_options']]
                        # Get item match
                        item_match = row['item_match']
                        # Set field name
                        field_name = 'item_select-' + str(row['index'])
                        # Set field select box
                        self.fields[field_name] = forms.ChoiceField(
                            choices=[('', '-' * 10)] + item_options,
                            required=False,
                            widget=forms.Select(attrs={
                                'class': 'select bomselect',
                            })
                        )
                        # Update select box when match was found
                        if item_match:
                            # Make it a required field: does not validate if
                            # removed using JS function
                            # self.fields[field_name].required = True
                            # Update initial value
                            self.fields[field_name].initial = item_match.id

                    # Optional entries
                    elif col_guess in file_manager.OPTIONAL_HEADERS:
                        # Set field name
                        field_name = col_guess.lower() + '-' + str(row['index'])
                        # Get value
                        value = row.get(col_guess.lower(), '')
                        # Set field input box
                        if 'price' in col_guess.lower():
                            self.fields[field_name] = MoneyField(
                                label=_(col_guess),
                                default_currency=currency_code_default(),
                                decimal_places=5,
                                max_digits=19,
                                required=False,
                                default_amount=clean_decimal(value),
                            )
                        else:
                            self.fields[field_name] = forms.CharField(
                                required=False,
                                initial=value,
                            )
