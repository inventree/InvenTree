"""Unit tests for the user model database migrations."""

from django_test_migrations.contrib.unittest_case import MigratorTestCase

from InvenTree import helpers


class TestForwardMigrations(MigratorTestCase):
    """Test entire schema migration sequence for the users app."""

    migrate_from = ('users', helpers.getOldestMigrationFile('users'))
    migrate_to = ('users', helpers.getNewestMigrationFile('users'))

    def prepare(self):
        """Setup the initial state of the database before migrations"""
        User = self.old_state.apps.get_model('auth', 'user')

        User.objects.create(
            username='fred',
            email='fred@fred.com',
            password='password'
        )

        User.objects.create(
            username='brad',
            email='brad@fred.com',
            password='password'
        )

    def test_users_exist(self):
        """Test that users exist in the database"""
        User = self.new_state.apps.get_model('auth', 'user')

        self.assertEqual(User.objects.count(), 2)
