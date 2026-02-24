"""Tests for custom InvenTree management commands."""

from pathlib import Path

from django.conf import settings
from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase

from opentelemetry.instrumentation.sqlite3 import SQLite3Instrumentor

from InvenTree.config import get_testfolder_dir


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

    def test_backup_metadata(self):
        """Test the backup metadata functions."""
        from InvenTree.backup import (
            _gather_environment_metadata,
            _parse_environment_metadata,
        )

        metadata = _gather_environment_metadata()
        self.assertIn('ivt_1_version', metadata)
        self.assertIn('ivt_1_plugins_enabled', metadata)

        parsed = _parse_environment_metadata(metadata)
        self.assertIn('version', parsed)
        self.assertIn('plugins_enabled', parsed)

    def test_backup_command_e2e(self):
        """Test the backup command."""
        # disable tracing for now
        if (
            settings.TRACING_ENABLED
            and settings.DB_ENGINE == 'django.db.backends.sqlite3'
        ):
            print('Disabling tracing for backup command test')
            SQLite3Instrumentor().uninstrument()

        output_path = get_testfolder_dir().joinpath('backup.zip').resolve()

        # Backup
        with self.assertLogs() as cm:
            output = call_command(
                'dbbackup', noinput=True, verbosity=2, output_path=str(output_path)
            )
            self.assertIsNone(output)
        self.assertIn(f'Writing metadata file to {output_path}', str(cm[1]))

        # Restore
        with self.assertLogs() as cm:
            output = call_command(
                'dbrestore',
                noinput=True,
                interactive=False,
                verbosity=2,
                input_path=str(output_path),
            )
            self.assertIsNone(output)
        self.assertIn('Using connector from metadata', str(cm[1]))

        # Cleanup the generated backup file and metadata file
        output_path.unlink()
        Path(str(output_path) + '.metadata').unlink()

        if (
            settings.TRACING_ENABLED
            and settings.DB_ENGINE == 'django.db.backends.sqlite3'
        ):
            print('Re-enabling tracing for backup command test')
            SQLite3Instrumentor().instrument()
