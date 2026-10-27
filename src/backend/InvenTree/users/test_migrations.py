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


class TestPricingRoleMigration(MigratorTestCase):
    """Test that the 'pricing' role is copied from the existing 'part' role."""

    migrate_from = ('users', '0018_tippresult')
    migrate_to = ('users', '0019_pricing_role')

    def prepare(self):
        """Create groups with a variety of 'part' role permissions."""
        Group = self.old_state.apps.get_model('auth', 'group')
        RuleSet = self.old_state.apps.get_model('users', 'RuleSet')

        viewer = Group.objects.create(name='viewer')
        editor = Group.objects.create(name='editor')
        nobody = Group.objects.create(name='nobody')

        RuleSet.objects.create(group=viewer, name='part', can_view=True)
        RuleSet.objects.create(
            group=editor,
            name='part',
            can_view=True,
            can_add=True,
            can_change=True,
            can_delete=True,
        )
        RuleSet.objects.create(group=nobody, name='part')

        # A group without a 'part' ruleset at all
        Group.objects.create(name='empty')

    def test_pricing_role(self):
        """Pricing role permissions should match the part role for each group."""
        RuleSet = self.new_state.apps.get_model('users', 'RuleSet')

        self.assertEqual(RuleSet.objects.filter(name='pricing').count(), 3)

        for name in ['viewer', 'editor', 'nobody']:
            part = RuleSet.objects.get(group__name=name, name='part')
            pricing = RuleSet.objects.get(group__name=name, name='pricing')

            for perm in ['can_view', 'can_add', 'can_change', 'can_delete']:
                self.assertEqual(getattr(part, perm), getattr(pricing, perm))

        self.assertTrue(
            RuleSet.objects.get(group__name='editor', name='pricing').can_delete
        )
        self.assertFalse(
            RuleSet.objects.filter(group__name='empty', name='pricing').exists()
        )
