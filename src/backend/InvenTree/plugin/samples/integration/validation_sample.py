"""Sample plugin which demonstrates custom validation functionality."""

from datetime import datetime

from plugin import InvenTreePlugin
from plugin.mixins import SettingsMixin, ValidationMixin


class SampleValidatorPlugin(SettingsMixin, ValidationMixin, InvenTreePlugin):
    """A sample plugin class for demonstrating custom validation functions.

    Simple of examples of custom validator code.
    """

    NAME = 'SampleValidator'
    SLUG = 'validator'
    TITLE = 'Sample Validator Plugin'
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

    def validate_model_instance(self, instance, deltas=None):
        """Run validation against any saved model.

        - Check if the instance is a BomItem object
        - Test if the quantity is an integer
        """
        import part.models

        # Print debug message to console (intentional)
        print('Validating model instance:', instance.__class__, f'<{instance.pk}>')

        if isinstance(instance, part.models.BomItem):
            if self.get_setting('BOM_ITEM_INTEGER'):
                if float(instance.quantity) != int(instance.quantity):
                    self.raise_error({
                        'quantity': 'Bom item quantity must be an integer'
                    })

        if isinstance(instance, part.models.Part):
            # If the part description is being updated, prevent it from being reduced in length

            if deltas and 'description' in deltas:
                old_desc = deltas['description']['old']
                new_desc = deltas['description']['new']

                if len(new_desc) < len(old_desc):
                    self.raise_error({
                        'description': 'Part description cannot be shortened'
                    })

    def validate_part_name(self, name: str, part):
        """Custom validation for Part name field.

        Rules:
        - Name must be shorter than the description field
        - Name cannot contain illegal characters

        These examples are silly, but serve to demonstrate how the feature could be used.
        """
        if len(part.description) < len(name):
            self.raise_error('Part description cannot be shorter than the name')

        illegal_chars = self.get_setting('ILLEGAL_PART_CHARS')

        for c in illegal_chars:
            if c in name:
                self.raise_error(f"Illegal character in part name: '{c}'")

    def validate_part_ipn(self, ipn: str, part):
        """Validate part IPN.

        These examples are silly, but serve to demonstrate how the feature could be used
        """
        if self.get_setting('IPN_MUST_CONTAIN_Q') and 'Q' not in ipn:
            self.raise_error("IPN must contain 'Q'")

    def validate_part_parameter(self, parameter, data):
        """Validate part parameter data.

        These examples are silly, but serve to demonstrate how the feature could be used
        """
        if parameter.template.name.lower() in ['length', 'width']:
            d = int(data)
            if d >= 100:
                self.raise_error('Value must be less than 100')

    def validate_serial_number(self, serial: str, part, stock_item=None):
        """Validate serial number for a given StockItem.

        These examples are silly, but serve to demonstrate how the feature could be used
        """
        if self.get_setting('SERIAL_MUST_BE_PALINDROME'):
            if serial != serial[::-1]:
                self.raise_error('Serial must be a palindrome')

        if self.get_setting('SERIAL_MUST_MATCH_PART'):
            # Serial must start with the same letter as the linked part, for some reason
            if serial[0] != part.name[0]:
                self.raise_error('Serial number must start with same letter as part')

        # Prevent serial numbers which are a multiple of 5
        try:
            sn = int(serial)
            if sn % 5 == 0:
                self.raise_error('Serial number cannot be a multiple of 5')
        except ValueError:
            pass

    def increment_serial_number(self, serial: str, part=None, **kwargs):
        """Increment a serial number.

        These examples are silly, but serve to demonstrate how the feature could be used
        """
        try:
            sn = int(serial)
            sn += 1

            # Skip any serial number which is a multiple of 5
            if sn % 5 == 0:
                sn += 1

            return str(sn)
        except ValueError:
            pass

        # Return "None" to defer to the next plugin or builtin functionality
        return None

    def validate_batch_code(self, batch_code: str, item):
        """Ensure that a particular batch code meets specification.

        These examples are silly, but serve to demonstrate how the feature could be used
        """
        prefix = self.get_setting('BATCH_CODE_PREFIX')

        if len(batch_code) > 0 and prefix and not batch_code.startswith(prefix):
            self.raise_error(f"Batch code must start with '{prefix}'")

    def generate_batch_code(self, **kwargs):
        """Generate a new batch code."""
        now = datetime.now()
        batch = f'SAMPLE-BATCH-{now.year}:{now.month}:{now.day}'

        # If a Part instance is provided, prepend the part name to the batch code
        if part := kwargs.get('part'):
            batch = f'{part.name}-{batch}'

        # If a Build instance is provided, prepend the build number to the batch code
        if build := kwargs.get('build_order'):
            batch = f'{build.reference}-{batch}'

        return batch
