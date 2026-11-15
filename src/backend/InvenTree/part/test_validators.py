"""Unit tests for part app validators."""

from django.core.exceptions import ValidationError
from django.test import TestCase

import part.validators


class PartValidatorTests(TestCase):
    """Tests for part validators."""

    def test_validate_part_name_format(self):
        """Test error cases for validate_part_name_format."""
        # No field
        with self.assertRaises(ValidationError) as err:
            part.validators.validate_part_name_format('abc{{}}')
        self.assertEqual(
            err.exception.messages[0],
            'At least one field must be present inside a jinja template container i.e {{}}',
        )

        # Wrong field name
        with self.assertRaises(ValidationError) as err:
            part.validators.validate_part_name_format('{{part.wrong}}')
        self.assertEqual(
            err.exception.messages[0], 'wrong does not exist in Part Model'
        )

        # Broken templates
        with self.assertRaises(ValidationError) as err:
            part.validators.validate_part_name_format('{{')
        self.assertEqual(err.exception.messages[0], "unexpected 'end of template'")

        with self.assertRaises(ValidationError) as err:
            part.validators.validate_part_name_format(None)
        self.assertEqual(err.exception.messages[0], "Can't compile non template nodes")

        # Correct template
        self.assertTrue(
            part.validators.validate_part_name_format('{{part.name}}'), 'test part'
        )
