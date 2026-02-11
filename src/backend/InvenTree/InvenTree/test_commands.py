"""Tests for custom InvenTree management commands."""

from pathlib import Path

from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase


class CommandTestCase(TestCase):
    """Test case for custom management commands."""

    def test_schema(self):
        """Test the schema generation command."""
        output = call_command('schema', file='schema.yml', verbosity=0)
        self.assertEqual(output, 'done')

        Path('schema.yml').unlink()  # cleanup

    def test_remove_mfa(self):
        """Test the remove_mfa command."""

        def get_dummyuser(uname='admin'):
            admin = User.objects.create_user(
                username=uname, email=f'{uname}@example.org'
            )
            admin.authenticator_set.create(type='TOTP', data={})
            self.assertEqual(admin.authenticator_set.all().count(), 1)
            return admin

        # missing arg
        with self.assertRaises(Exception) as cm:
            call_command('remove_mfa', verbosity=0)
        self.assertEqual(
            'Error: one of the following arguments is required: mail, username',
            str(cm.exception),
        )

        # no user
        with self.assertLogs('inventree') as cm:
            self.assertFalse(
                call_command('remove_mfa', mail='admin@example.org', verbosity=0)
            )
        self.assertIn('No user with this mail associated', str(cm[1]))

        # correct removal
        my_admin1 = get_dummyuser()
        output = call_command('remove_mfa', mail=my_admin1.email, verbosity=0)
        self.assertEqual(output, 'done')
        self.assertEqual(my_admin1.authenticator_set.all().count(), 0)

        # two users with same email
        my_admin2 = User.objects.create_user(username='admin2', email=my_admin1.email)
        my_admin2.emailaddress_set.create(email='456')
        my_admin2.emailaddress_set.create(email='123')
        with self.assertLogs('inventree') as cm:
            self.assertFalse(
                call_command('remove_mfa', mail=my_admin1.email, verbosity=0)
            )
        self.assertIn('Multiple users found with the provided email', str(cm[1]))
        self.assertIn('admin, admin2', str(cm[1]))
        self.assertIn(f'123, 456, {my_admin1.email}', str(cm[1]))

        # correct removal by username
        my_admin3 = get_dummyuser('admin3')
        output = call_command('remove_mfa', username=my_admin3.username, verbosity=0)
        self.assertEqual(output, 'done')
        self.assertEqual(my_admin3.authenticator_set.all().count(), 0)
