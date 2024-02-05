"""Sample plugin which demonstrates custom validation functionality."""

from datetime import datetime

from django.core.exceptions import ValidationError

from plugin import InvenTreePlugin
from plugin.mixins import SettingsMixin, ValidationMixin


class CustomValidationMixin(SettingsMixin, ValidationMixin, InvenTreePlugin):
    """A sample plugin class for demonstrating custom validation functions.

    Simple of examples of custom validator code.
    """

    NAME = 'CustomValidator'
    SLUG = 'validator'
    TITLE = 'Custom Validator Plugin'
    DESCRIPTION = 'A sample plugin for demonstrating custom validation functionality'
    VERSION = '0.3.0'

    SETTINGS = {
        'ILLEGAL_PART_CHARS': {
            'name': 'Illegal Part Characters',
            'description': 'Characters which are not allowed to appear in Part names',
            'default': '!@#$%^&*()~`',
        },
        'IPN_MUST_CONTAIN_Q': {
            'name': 'IPN Q Requirement',
            'description': 'Part IPN field must contain the character Q',
            'default': False,
            'validator': bool,
        },
        'SERIAL_MUST_BE_PALINDROME': {
            'name': 'Palindromic Serials',
            'description': 'Serial numbers must be palindromic',
            'default': False,
            'validator': bool,
        },
        'SERIAL_MUST_MATCH_PART': {
            'name': 'Serial must match part',
            'description': 'First letter of serial number must match first letter of part name',
            'default': False,
            'validator': bool,
        },
        'BATCH_CODE_PREFIX': {
            'name': 'Batch prefix',
            'description': 'Required prefix for batch code',
            'default': 'B',
        },
        'BOM_ITEM_INTEGER': {
            'name': 'Integer Bom Quantity',
            'description': 'Bom item quantity must be an integer',
            'default': False,
            'validator': bool,
        },
    }

    def validate_model_instance(self, instance):
        """Run validation against any saved model.

        - Check if the instance is a BomItem object
        - Test if the quantity is an integer
        """
        import part.models

        print('Validating model instance:', instance.__class__, f'<{instance.pk}>')

        if isinstance(instance, part.models.BomItem):
            if self.get_setting('BOM_ITEM_INTEGER'):
                if float(instance.quantity) != int(instance.quantity):
                    raise ValidationError({
                        'quantity': 'Bom item quantity must be an integer'
                    })

    def validate_part_name(self, name: str, part):
        """Custom validation for Part name field.

        Rules:
        - Name must be shorter than the description field
        - Name cannot contain illegal characters

        These examples are silly, but serve to demonstrate how the feature could be used.
        """
        if len(part.description) < len(name):
            raise ValidationError('Part description cannot be shorter than the name')

        illegal_chars = self.get_setting('ILLEGAL_PART_CHARS')

        for c in illegal_chars:
            if c in name:
                raise ValidationError(f"Illegal character in part name: '{c}'")

    def validate_part_ipn(self, ipn: str, part):
        """Validate part IPN.

        These examples are silly, but serve to demonstrate how the feature could be used
        """
        if self.get_setting('IPN_MUST_CONTAIN_Q') and 'Q' not in ipn:
            raise ValidationError("IPN must contain 'Q'")

    def validate_part_parameter(self, parameter, data):
        """Validate part parameter data.

        These examples are silly, but serve to demonstrate how the feature could be used
        """
        if parameter.template.name.lower() in ['length', 'width']:
            d = int(data)
            if d >= 100:
                raise ValidationError('Value must be less than 100')

    def validate_serial_number(self, serial: str, part):
        """Validate serial number for a given StockItem.

        These examples are silly, but serve to demonstrate how the feature could be used
        """
        if self.get_setting('SERIAL_MUST_BE_PALINDROME'):
            if serial != serial[::-1]:
                raise ValidationError('Serial must be a palindrome')

        if self.get_setting('SERIAL_MUST_MATCH_PART'):
            # Serial must start with the same letter as the linked part, for some reason
            if serial[0] != part.name[0]:
                raise ValidationError(
                    'Serial number must start with same letter as part'
                )

    def validate_batch_code(self, batch_code: str, item):
        """Ensure that a particular batch code meets specification.

        These examples are silly, but serve to demonstrate how the feature could be used
        """
        prefix = self.get_setting('BATCH_CODE_PREFIX')

        if len(batch_code) > 0:
            if prefix and not batch_code.startswith(prefix):
                raise ValidationError(f"Batch code must start with '{prefix}'")

    def generate_batch_code(self):
        """Generate a new batch code."""
        now = datetime.now()
        return f'BATCH-{now.year}:{now.month}:{now.day}'
