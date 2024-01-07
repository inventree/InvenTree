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


class TestBomItemMigrations(MigratorTestCase):
    """Tests for BomItem migrations"""

    migrate_from = ('part', '0002_auto_20190520_2204')
    migrate_to = ('part', unit_test.getNewestMigrationFile('part'))

    def prepare(self):
        """Create initial dataset"""
        Part = self.old_state.apps.get_model('part', 'part')
        BomItem = self.old_state.apps.get_model('part', 'bomitem')

        a = Part.objects.create(name='Part A', description='My part A')
        b = Part.objects.create(name='Part B', description='My part B')
        c = Part.objects.create(name='Part C', description='My part C')

        BomItem.objects.create(part=a, sub_part=b, quantity=1)
        BomItem.objects.create(part=a, sub_part=c, quantity=1)

        self.assertEqual(BomItem.objects.count(), 2)

        # Initially we don't have the 'validated' field
        with self.assertRaises(AttributeError):
            print(b.validated)

    def test_validated_field(self):
        """Test that the 'validated' field is added to the BomItem objects"""
        BomItem = self.new_state.apps.get_model('part', 'bomitem')

        self.assertEqual(BomItem.objects.count(), 2)

        for bom_item in BomItem.objects.all():
            self.assertFalse(bom_item.validated)


class TestParameterMigrations(MigratorTestCase):
    """Unit test for part parameter migrations"""

    migrate_from = ('part', '0106_part_tags')
    migrate_to = ('part', unit_test.getNewestMigrationFile('part'))

    def prepare(self):
        """Create some parts, and templates with parameters"""
        Part = self.old_state.apps.get_model('part', 'part')
        PartParameter = self.old_state.apps.get_model('part', 'partparameter')
        PartParameterTemlate = self.old_state.apps.get_model(
            'part', 'partparametertemplate'
        )

        # Create some parts
        a = Part.objects.create(
            name='Part A', description='My part A', level=0, lft=0, rght=0, tree_id=0
        )

        b = Part.objects.create(
            name='Part B', description='My part B', level=0, lft=0, rght=0, tree_id=0
        )

        # Create some templates
        t1 = PartParameterTemlate.objects.create(name='Template 1', units='mm')
        t2 = PartParameterTemlate.objects.create(name='Template 2', units='AMPERE')

        # Create some parameter values
        PartParameter.objects.create(part=a, template=t1, data='1.0')
        PartParameter.objects.create(part=a, template=t2, data='-2mA')

        PartParameter.objects.create(part=b, template=t1, data='1/10 inch')
        PartParameter.objects.create(part=b, template=t2, data='abc')

    def test_data_migration(self):
        """Test that the template units and values have been updated correctly"""
        Part = self.new_state.apps.get_model('part', 'part')
        PartParameter = self.new_state.apps.get_model('part', 'partparameter')
        PartParameterTemlate = self.new_state.apps.get_model(
            'part', 'partparametertemplate'
        )

        # Extract the parts
        a = Part.objects.get(name='Part A')
        b = Part.objects.get(name='Part B')

        # Check that the templates have been updated correctly
        t1 = PartParameterTemlate.objects.get(name='Template 1')
        self.assertEqual(t1.units, 'mm')

        t2 = PartParameterTemlate.objects.get(name='Template 2')
        self.assertEqual(t2.units, 'ampere')

        # Check that the parameter values have been updated correctly
        p1 = PartParameter.objects.get(part=a, template=t1)
        self.assertEqual(p1.data, '1.0')
        self.assertEqual(p1.data_numeric, 1.0)

        p2 = PartParameter.objects.get(part=a, template=t2)
        self.assertEqual(p2.data, '-2mA')
        self.assertEqual(p2.data_numeric, -0.002)

        p3 = PartParameter.objects.get(part=b, template=t1)
        self.assertEqual(p3.data, '1/10 inch')
        self.assertEqual(p3.data_numeric, 2.54)

        # This one has not converted correctly
        p4 = PartParameter.objects.get(part=b, template=t2)
        self.assertEqual(p4.data, 'abc')
        self.assertEqual(p4.data_numeric, None)


class PartUnitsMigrationTest(MigratorTestCase):
    """Test for data migration of Part.units field"""

    migrate_from = ('part', '0109_auto_20230517_1048')
    migrate_to = ('part', unit_test.getNewestMigrationFile('part'))

    def prepare(self):
        """Prepare some parts with units"""
        Part = self.old_state.apps.get_model('part', 'part')

        units = ['mm', 'INCH', '', '%']

        for idx, unit in enumerate(units):
            Part.objects.create(
                name=f'Part {idx + 1}',
                description=f'My part at index {idx}',
                units=unit,
                level=0,
                lft=0,
                rght=0,
                tree_id=0,
            )

    def test_units_migration(self):
        """Test that the units have migrated OK"""
        Part = self.new_state.apps.get_model('part', 'part')

        part_1 = Part.objects.get(name='Part 1')
        part_2 = Part.objects.get(name='Part 2')
        part_3 = Part.objects.get(name='Part 3')
        part_4 = Part.objects.get(name='Part 4')

        self.assertEqual(part_1.units, 'mm')
        self.assertEqual(part_2.units, 'inch')
        self.assertEqual(part_3.units, '')
        self.assertEqual(part_4.units, 'percent')


class TestPartParameterTemplateMigration(MigratorTestCase):
    """Test for data migration of PartParameterTemplate

    Ref: https://github.com/inventree/InvenTree/pull/4987
    """

    migrate_from = ('part', '0110_alter_part_units')
    migrate_to = ('part', '0113_auto_20230531_1205')

    def prepare(self):
        """Prepare some parts with units"""
        PartParameterTemplate = self.old_state.apps.get_model(
            'part', 'partparametertemplate'
        )

        # Create a test template
        template = PartParameterTemplate.objects.create(
            name='Template 1', description='a part parameter template'
        )

        # Ensure that the 'choices' and 'checkbox' fields do not exist
        with self.assertRaises(AttributeError):
            template.choices

        with self.assertRaises(AttributeError):
            template.checkbox

    def test_units_migration(self):
        """Test that the new fields have been added correctly"""
        PartParameterTemplate = self.new_state.apps.get_model(
            'part', 'partparametertemplate'
        )

        template = PartParameterTemplate.objects.get(name='Template 1')

        self.assertEqual(template.choices, '')
        self.assertEqual(template.checkbox, False)
