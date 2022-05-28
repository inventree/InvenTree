"""Tests for the build model database migrations."""

from django_test_migrations.contrib.unittest_case import MigratorTestCase

from InvenTree import helpers


class TestForwardMigrations(MigratorTestCase):
    """Test entire schema migration sequence for the build app."""

    migrate_from = ('build', helpers.getOldestMigrationFile('build'))
    migrate_to = ('build', helpers.getNewestMigrationFile('build'))

    def prepare(self):
        """Create initial data!"""
        Part = self.old_state.apps.get_model('part', 'part')

        buildable_part = Part.objects.create(
            name='Widget',
            description='Buildable Part',
            active=True,
        )

        with self.assertRaises(TypeError):
            # Cannot set the 'assembly' field as it hasn't been added to the db schema
            Part.objects.create(
                name='Blorb',
                description='ABCDE',
                assembly=True
            )

        Build = self.old_state.apps.get_model('build', 'build')

        Build.objects.create(
            part=buildable_part,
            title='A build of some stuff',
            quantity=50
        )

    def test_items_exist(self):

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


class TestReferenceMigration(MigratorTestCase):
    """Test custom migration which adds 'reference' field to Build model."""

    migrate_from = ('build', helpers.getOldestMigrationFile('build'))
    migrate_to = ('build', '0018_build_reference')

    def prepare(self):
        """Create some builds."""
        Part = self.old_state.apps.get_model('part', 'part')

        part = Part.objects.create(
            name='Part',
            description='A test part'
        )

        Build = self.old_state.apps.get_model('build', 'build')

        Build.objects.create(
            part=part,
            title='My very first build',
            quantity=10
        )

        Build.objects.create(
            part=part,
            title='My very second build',
            quantity=10
        )

        Build.objects.create(
            part=part,
            title='My very third build',
            quantity=10
        )

        # Ensure that the builds *do not* have a 'reference' field
        for build in Build.objects.all():
            with self.assertRaises(AttributeError):
                print(build.reference)

    def test_build_reference(self):

        Build = self.new_state.apps.get_model('build', 'build')

        self.assertEqual(Build.objects.count(), 3)

        # Check that the build reference is properly assigned
        for build in Build.objects.all():
            self.assertEqual(str(build.reference), str(build.pk))
