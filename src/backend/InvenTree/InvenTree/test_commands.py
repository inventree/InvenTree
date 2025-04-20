"""Tests for custom InvenTree management commands."""

from django.core.management import call_command
from django.test import TestCase


class CommandTestCase(TestCase):
    """Test case for custom management commands."""

    def test_schema(self):
        """Test the schema generation command."""
        output = call_command('schema', file='schema.yml', verbosity=0)
        self.assertEqual(output, 'done')
