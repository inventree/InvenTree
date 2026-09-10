"""Tests for the build model database migrations."""

from django_test_migrations.contrib.unittest_case import MigratorTestCase

from InvenTree import unit_test


class TestForwardMigrations(MigratorTestCase):
    """Test entire schema migration sequence for the build app."""

    migrate_from = ('build', unit_test.getOldestMigrationFile('build'))
    migrate_to = ('build', unit_test.getNewestMigrationFile('build'))

    def prepare(self):
        """Create initial data!"""
        Part = self.old_state.apps.get_model('part', 'part')

        buildable_part = Part.objects.create(
            name='Widget',
            description='Buildable Part',
            active=True,
            level=0,
            tree_id=0,
            lft=0,
            rght=0,
        )

        Build = self.old_state.apps.get_model('build', 'build')

        Build.objects.create(
            part=buildable_part, title='A build of some stuff', quantity=50
        )

    def test_items_exist(self):
        """Test to ensure that the 'assembly' field is correctly configured."""
        Part = self.new_state.apps.get_model('part', 'part')

        self.assertEqual(Part.objects.count(), 1)

        Build = self.new_state.apps.get_model('build', 'build')

        self.assertEqual(Build.objects.count(), 1)

        # Check that the part object now has an assembly field
        part = Part.objects.all().first()
        part.assembly = True
        part.save()
        part.assembly = False
        part.save()
