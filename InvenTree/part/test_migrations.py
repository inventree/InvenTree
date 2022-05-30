"""Unit tests for the part model database migrations."""

from django_test_migrations.contrib.unittest_case import MigratorTestCase

from InvenTree import helpers


class TestForwardMigrations(MigratorTestCase):
    """Test entire schema migration sequence for the part app."""

    migrate_from = ('part', helpers.getOldestMigrationFile('part'))
    migrate_to = ('part', helpers.getNewestMigrationFile('part'))

    def prepare(self):
        """Create initial data."""
        Part = self.old_state.apps.get_model('part', 'part')

        Part.objects.create(name='A', description='My part A')
        Part.objects.create(name='B', description='My part B')
        Part.objects.create(name='C', description='My part C')
        Part.objects.create(name='D', description='My part D')
        Part.objects.create(name='E', description='My part E')

        # Extract one part object to investigate
        p = Part.objects.all().last()

        # Initially some fields are not present
        with self.assertRaises(AttributeError):
            print(p.has_variants)

        with self.assertRaises(AttributeError):
            print(p.is_template)

    def test_models_exist(self):
        """Test that the Part model can still be accessed at the end of schema migration"""
        Part = self.new_state.apps.get_model('part', 'part')

        self.assertEqual(Part.objects.count(), 5)

        for part in Part.objects.all():
            part.is_template = True
            part.save()
            part.is_template = False
            part.save()

        for name in ['A', 'C', 'E']:
            part = Part.objects.get(name=name)
            self.assertEqual(part.description, f"My part {name}")
