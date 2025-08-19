"""Tests for custom InvenTree management commands."""

from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase


class CommandTestCase(TestCase):
    """Test case for custom management commands."""

    def test_schema(self):
        """Test the schema generation command."""
        output = call_command('schema', file='schema.yml', verbosity=0)
        self.assertEqual(output, 'done')

    def test_remove_mfa(self):
        """Test the remove_mfa command."""
        # missing arg
        with self.assertRaises(Exception) as cm:
            call_command('remove_mfa', verbosity=0)
        self.assertEqual(
            'Error: the following arguments are required: mail', str(cm.exception)
        )

        # no user
        with self.assertLogs('inventree') as cm:
            self.assertFalse(
                call_command('remove_mfa', 'admin@example.org', verbosity=0)
            )
        self.assertIn('No user with this mail associated', str(cm[1]))

        # correct removal
        my_admin = User.objects.create_user(username='admin', email='admin@example.org')
        my_admin.authenticator_set.create(type='TOTP', data={})
        output = call_command('remove_mfa', 'admin@example.org', verbosity=0)
        self.assertEqual(output, 'done')

        # two users with same email
        User.objects.create_user(username='admin2', email='admin@example.org')
        with self.assertLogs('inventree') as cm:
            self.assertFalse(
                call_command('remove_mfa', 'admin@example.org', verbosity=0)
            )
        self.assertIn('More than one user found with this mail', str(cm[1]))
