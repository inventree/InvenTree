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


class MFAMigrations(MigratorTestCase):
    """Test entire schema migration sequence for the users app."""

    migrate_from = ('users', '0012_alter_ruleset_can_view')
    migrate_to = ('users', '0013_migrate_mfa_20240408_1659')

    def prepare(self):
        """Setup the initial state of the database before migrations."""
        User = self.old_state.apps.get_model('auth', 'user')
        TOTPDevice = self.old_state.apps.get_model('otp_totp', 'TOTPDevice')
        StaticDevice = self.old_state.apps.get_model('otp_static', 'StaticDevice')

        abc = User.objects.create(
            username='fred', email='fred@fred.com', password='password'
        )
        TOTPDevice.objects.create(user=abc, confirmed=True, key='1234')
        abc1 = User.objects.create(
            username='brad', email='brad@fred.com', password='password'
        )
        TOTPDevice.objects.create(user=abc1, confirmed=False, key='1234')
        StaticDevice.objects.create(user=abc1, confirmed=True)

    def test_users_exist(self):
        """Test that users exist in the database."""
        User = self.new_state.apps.get_model('auth', 'user')
        Authenticator = self.new_state.apps.get_model('mfa', 'Authenticator')

        self.assertEqual(User.objects.count(), 2)
        # 2 Tokens - both for user 1
        self.assertEqual(Authenticator.objects.count(), 2)
        self.assertEqual([1, 1], [i.user_id for i in Authenticator.objects.all()])
