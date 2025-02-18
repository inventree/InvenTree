"""Unit tests for the user model database migrations."""

from django_test_migrations.contrib.unittest_case import MigratorTestCase

from InvenTree import unit_test


class TestForwardMigrations(MigratorTestCase):
    """Test entire schema migration sequence for the users app."""

    migrate_from = ('users', unit_test.getOldestMigrationFile('users'))
    migrate_to = ('users', unit_test.getNewestMigrationFile('users'))

    def prepare(self):
        """Setup the initial state of the database before migrations."""
        User = self.old_state.apps.get_model('auth', 'user')

        User.objects.create(username='fred', email='fred@fred.com', password='password')

        User.objects.create(username='brad', email='brad@fred.com', password='password')

    def test_users_exist(self):
        """Test that users exist in the database."""
        User = self.new_state.apps.get_model('auth', 'user')

        self.assertEqual(User.objects.count(), 2)


class TestBackfillUserProfiles(MigratorTestCase):
    """Test backfill migration for user profiles."""

    migrate_from = ('users', '0012_alter_ruleset_can_view')
    migrate_to = ('users', '0013_userprofile')

    def prepare(self):
        """Setup the initial state of the database before migrations."""
        User = self.old_state.apps.get_model('auth', 'user')

        User.objects.create(
            username='fred', email='fred@example.org', password='password'
        )
        User.objects.create(
            username='brad', email='brad@example.org', password='password'
        )

    def test_backfill_user_profiles(self):
        """Test that user profiles are created during the migration."""
        User = self.new_state.apps.get_model('auth', 'user')
        UserProfile = self.new_state.apps.get_model('users', 'UserProfile')

        self.assertEqual(User.objects.count(), 2)
        self.assertEqual(UserProfile.objects.count(), 2)

        fred = User.objects.get(username='fred')
        brad = User.objects.get(username='brad')

        self.assertIsNotNone(UserProfile.objects.get(user=fred))
        self.assertIsNotNone(UserProfile.objects.get(user=brad))
