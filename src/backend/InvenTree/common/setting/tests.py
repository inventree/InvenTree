"""Tests for the various validators in the settings."""

from django.core.exceptions import ValidationError
from django.test import TestCase

import common.setting.system


class SettingsValidatorTests(TestCase):
    """Tests settings validators."""

    def test_validate_part_name_format(self):
        """Test error cases for validate_part_name_format."""
        # No field
        with self.assertRaises(ValidationError) as err:
            common.setting.system.validate_part_name_format('abc{{}}')
        self.assertEqual(
            err.exception.messages[0],
            'At least one field must be present inside a jinja template container i.e {{}}',
        )

        # Wrong field name
        with self.assertRaises(ValidationError) as err:
            common.setting.system.validate_part_name_format('{{part.wrong}}')
        self.assertEqual(
            err.exception.messages[0], 'wrong does not exist in Part Model'
        )

        # Broken templates
        with self.assertRaises(ValidationError) as err:
            common.setting.system.validate_part_name_format('{{')
        self.assertEqual(err.exception.messages[0], "unexpected 'end of template'")

        with self.assertRaises(ValidationError) as err:
            common.setting.system.validate_part_name_format(None)
        self.assertEqual(err.exception.messages[0], "Can't compile non template nodes")

        # Correct template
        self.assertTrue(
            common.setting.system.validate_part_name_format('{{part.name}}'),
            'test part',
        )

    def test_update_instance_name_no_multi(self):
        """Test valid cases for update_instance_name."""
        self.assertIsNone(common.setting.system.update_instance_name('abc'))

    def test_update_instance_url_no_multi(self):
        """Test update_instance_url."""
        self.assertIsNone(common.setting.system.update_instance_url('abc.com'))
