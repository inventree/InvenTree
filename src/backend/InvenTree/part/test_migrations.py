"""Unit tests for the part model database migrations."""

from django_test_migrations.contrib.unittest_case import MigratorTestCase

from InvenTree import unit_test


class TestForwardMigrations(MigratorTestCase):
    """Test entire schema migration sequence for the part app."""

    migrate_from = ('part', unit_test.getOldestMigrationFile('part'))
    migrate_to = ('part', unit_test.getNewestMigrationFile('part'))

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
        """Test that the Part model can still be accessed at the end of schema migration."""
        Part = self.new_state.apps.get_model('part', 'part')

        self.assertEqual(Part.objects.count(), 5)

        for part in Part.objects.all():
            part.is_template = True
            part.save()
            part.is_template = False
            part.save()

        for name in ['A', 'C', 'E']:
            part = Part.objects.get(name=name)
            self.assertEqual(part.description, f'My part {name}')


class TestPartParameterDeletion(MigratorTestCase):
    """Test for PartParameter deletion migration.

    Ref: https://github.com/inventree/InvenTree/pull/10699

    In the linked PR:

    1. The Parameter and ParameterTemplate models are added
    2. Data is migrated from PartParameter to Parameter and PartParameterTemplate to ParameterTemplate
    3. The PartParameter and PartParameterTemplate models are deleted
    """

    UNITS = ['mm', 'Ampere', 'kg']

    migrate_from = ('part', '0143_alter_part_image')
    migrate_to = ('part', '0146_auto_20251203_1241')

    def prepare(self):
        """Prepare some parts and parameters."""
        Part = self.old_state.apps.get_model('part', 'part')
        PartParameter = self.old_state.apps.get_model('part', 'partparameter')
        PartParameterTemplate = self.old_state.apps.get_model(
            'part', 'partparametertemplate'
        )

        # Create some parts
        for i in range(3):
            Part.objects.create(
                name=f'Part {i + 1}',
                description=f'My part {i + 1}',
                level=0,
                lft=0,
                rght=0,
                tree_id=0,
            )

        self.templates = {}

        # Create some parameter templates
        for idx, units in enumerate(self.UNITS):
            template = PartParameterTemplate.objects.create(
                name=f'Template {idx + 1}',
                description=f'Description for template {idx + 1}',
                units=units,
            )

            self.templates[template.pk] = template

        # Keep track of the parameters we create
        # We need to ensure that the PK values are preserved across the migration
        self.parameters = {}

        # Create some parameters
        for ii, part in enumerate(Part.objects.all()):
            for jj, template in enumerate(PartParameterTemplate.objects.all()):
                parameter = PartParameter.objects.create(
                    part=part, template=template, data=str(ii * jj)
                )

                self.parameters[parameter.pk] = parameter

        self.assertEqual(Part.objects.count(), 3)
        self.assertEqual(PartParameterTemplate.objects.count(), 3)
        self.assertEqual(PartParameter.objects.count(), 9)

    def test_parameter_deletion(self):
        """Test that PartParameter objects have been deleted."""
        # Test that the PartParameter objects have been deleted
        with self.assertRaises(LookupError):
            self.new_state.apps.get_model('part', 'partparameter')

        # Load the new PartParameter model
        ParameterTemplate = self.new_state.apps.get_model('common', 'parametertemplate')
        Parameter = self.new_state.apps.get_model('common', 'parameter')
        Part = self.new_state.apps.get_model('part', 'part')
        ContentType = self.new_state.apps.get_model('contenttypes', 'contenttype')

        self.assertEqual(ParameterTemplate.objects.count(), 3)
        self.assertEqual(Parameter.objects.count(), 9)
        self.assertEqual(Part.objects.count(), 3)

        content_type, _created = ContentType.objects.get_or_create(
            app_label='part', model='part'
        )

        for p in Part.objects.all():
            params = Parameter.objects.filter(model_type=content_type, model_id=p.id)

            self.assertEqual(len(params), 3)

            for unit in self.UNITS:
                self.assertTrue(params.filter(template__units=unit).exists())

        # Test that each parameter has been migrated correctly
        for pk, old_parameter in self.parameters.items():
            new_parameter = Parameter.objects.get(pk=pk)

            self.assertEqual(new_parameter.data, old_parameter.data)
            self.assertEqual(new_parameter.template.name, old_parameter.template.name)
            self.assertEqual(new_parameter.template.units, old_parameter.template.units)

        # Test that each template has been migrated correctly
        for pk, old_template in self.templates.items():
            new_template = ParameterTemplate.objects.get(pk=pk)

            self.assertEqual(new_template.name, old_template.name)
            self.assertEqual(new_template.description, old_template.description)
            self.assertTrue(new_template.enabled)
