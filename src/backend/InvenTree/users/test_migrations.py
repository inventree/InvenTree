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
        ApiToken = self.old_state.apps.get_model('users', 'ApiToken')

        fred = User.objects.create(
            username='fred', email='fred@fred.com', password='password'
        )

        User.objects.create(username='brad', email='brad@fred.com', password='password')

        ApiToken.objects.create(key='legacy-token', user=fred)

    def test_users_exist(self):
        """Test that users exist in the database."""
        User = self.new_state.apps.get_model('auth', 'user')

        self.assertEqual(User.objects.count(), 2)

    def test_existing_tokens_are_marked_as_v1(self):
        """Test that tokens created before v2 are marked as v1."""
        ApiToken = self.new_state.apps.get_model('users', 'ApiToken')

        token = ApiToken.objects.get(key='legacy-token')

        self.assertEqual(token.token_version, 1)

        # a new token should be a v2 token now
        new_token = ApiToken.objects.create(key='new-token', user=token.user)
        self.assertEqual(new_token.token_version, 2)
