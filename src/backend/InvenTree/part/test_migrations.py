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


class TestPartTestMigration(MigratorTestCase):
    """Test migration of PartTestTemplate entries to the PartTest model.

    - Each PartTestTemplate is linked to a Part via a new PartTest entry
    - Templates which share a key are merged into a single template
    - Test results are re-pointed to the merged template
    """

    migrate_from = ('part', '0154_remove_part_notes')
    migrate_to = ('part', '0157_remove_parttesttemplate_part')

    def prepare(self):
        """Create initial test templates and results."""
        Part = self.old_state.apps.get_model('part', 'part')
        PartTestTemplate = self.old_state.apps.get_model('part', 'parttesttemplate')
        StockItem = self.old_state.apps.get_model('stock', 'stockitem')
        StockItemTestResult = self.old_state.apps.get_model(
            'stock', 'stockitemtestresult'
        )

        tree = {'tree_id': 0, 'level': 0, 'lft': 0, 'rght': 0}

        a = Part.objects.create(name='A', testable=True, is_template=True, **tree)
        b = Part.objects.create(name='B', testable=True, **tree)
        v = Part.objects.create(name='V', testable=True, variant_of=a, **tree)

        def template(part, test_name, key, **kwargs):
            return PartTestTemplate.objects.create(
                part=part, test_name=test_name, key=key, **kwargs
            )

        # Duplicate key 'paint' - differing flags
        t1 = template(a, 'Paint', 'paint', required=True)
        t2 = template(
            b,
            'Paint',
            'paint',
            required=False,
            enabled=False,
            requires_value=True,
            choices='Red, Blue',
        )

        # Duplicate key 'weight' - differing choices
        t3 = template(a, 'Weight', 'weight', choices='Light, Heavy')
        t4 = template(
            b, 'weight', 'weight', choices='Heavy,Medium', requires_attachment=True
        )

        # Unique template
        t5 = template(v, 'Unique', 'unique', description='A unique test')

        self.template_ids = [t.pk for t in [t1, t2, t3, t4, t5]]
        self.part_ids = {'a': a.pk, 'b': b.pk, 'v': v.pk}

        item_a = StockItem.objects.create(part=a, quantity=1)
        item_b = StockItem.objects.create(part=b, quantity=1)

        for item, tmp in [(item_a, t1), (item_b, t2), (item_a, t3), (item_b, t4)]:
            StockItemTestResult.objects.create(
                stock_item=item, template=tmp, result=True
            )

        self.assertEqual(PartTestTemplate.objects.count(), 5)
        self.assertEqual(StockItemTestResult.objects.count(), 4)

    def test_migration(self):
        """Test that templates were merged and PartTest entries created."""
        PartTestTemplate = self.new_state.apps.get_model('part', 'parttesttemplate')
        PartTest = self.new_state.apps.get_model('part', 'parttest')
        StockItemTestResult = self.new_state.apps.get_model(
            'stock', 'stockitemtestresult'
        )

        t1, t2, t3, t4, t5 = self.template_ids
        a, b, v = self.part_ids['a'], self.part_ids['b'], self.part_ids['v']

        # Duplicates have been removed
        self.assertEqual(PartTestTemplate.objects.count(), 3)
        self.assertFalse(PartTestTemplate.objects.filter(pk__in=[t2, t4]).exists())

        # No results have been lost, and all point to the kept templates
        self.assertEqual(StockItemTestResult.objects.count(), 4)
        self.assertEqual(StockItemTestResult.objects.filter(template=t1).count(), 2)
        self.assertEqual(StockItemTestResult.objects.filter(template=t3).count(), 2)

        # 'paint' - flags are merged, t1 was unrestricted so choices remain empty
        paint = PartTestTemplate.objects.get(pk=t1)
        self.assertTrue(paint.requires_value)
        self.assertFalse(paint.requires_attachment)
        self.assertEqual(paint.choices, '')

        # 'weight' - choices are the ordered union, name from the kept template
        weight = PartTestTemplate.objects.get(pk=t3)
        self.assertEqual(weight.test_name, 'Weight')
        self.assertEqual(weight.choices, 'Light, Heavy, Medium')
        self.assertTrue(weight.requires_attachment)

        unique = PartTestTemplate.objects.get(pk=t5)
        self.assertEqual(unique.description, 'A unique test')

        # One PartTest per original template, with the original flags
        self.assertEqual(PartTest.objects.count(), 5)

        test = PartTest.objects.get(template=t1, part=a)
        self.assertTrue(test.enabled)
        self.assertTrue(test.required)

        test = PartTest.objects.get(template=t1, part=b)
        self.assertFalse(test.enabled)
        self.assertFalse(test.required)

        self.assertTrue(PartTest.objects.filter(template=t3, part=a).exists())
        self.assertTrue(PartTest.objects.filter(template=t3, part=b).exists())
        self.assertTrue(PartTest.objects.filter(template=t5, part=v).exists())


class TestPartTestReverseMigration(MigratorTestCase):
    """Test reverse migration of PartTest entries back to PartTestTemplate."""

    migrate_from = ('part', '0157_remove_parttesttemplate_part')
    migrate_to = ('part', '0155_parttest')

    def prepare(self):
        """Create templates which are linked to multiple parts."""
        Part = self.old_state.apps.get_model('part', 'part')
        PartTestTemplate = self.old_state.apps.get_model('part', 'parttesttemplate')
        PartTest = self.old_state.apps.get_model('part', 'parttest')

        tree = {'tree_id': 0, 'level': 0, 'lft': 0, 'rght': 0}

        a = Part.objects.create(name='A', testable=True, **tree)
        b = Part.objects.create(name='B', testable=True, **tree)

        shared = PartTestTemplate.objects.create(test_name='Shared', key='shared')
        single = PartTestTemplate.objects.create(test_name='Single', key='single')

        # Orphan template (no results) should be removed
        PartTestTemplate.objects.create(test_name='Orphan', key='orphan')

        PartTest.objects.create(template=shared, part=a, required=True)
        PartTest.objects.create(template=shared, part=b, required=False, enabled=False)
        PartTest.objects.create(template=single, part=b)

        self.part_ids = {'a': a.pk, 'b': b.pk}

    def test_reverse_migration(self):
        """Each PartTest is converted back to a part-linked template."""
        PartTestTemplate = self.new_state.apps.get_model('part', 'parttesttemplate')
        PartTest = self.new_state.apps.get_model('part', 'parttest')

        a, b = self.part_ids['a'], self.part_ids['b']

        # PartTest entries have been transferred back to the templates
        self.assertEqual(PartTest.objects.count(), 0)

        self.assertEqual(PartTestTemplate.objects.count(), 3)
        self.assertFalse(PartTestTemplate.objects.filter(key='orphan').exists())
        self.assertFalse(PartTestTemplate.objects.filter(part__isnull=True).exists())

        template = PartTestTemplate.objects.get(key='shared', part=a)
        self.assertTrue(template.enabled)
        self.assertTrue(template.required)

        template = PartTestTemplate.objects.get(key='shared', part=b)
        self.assertFalse(template.enabled)
        self.assertFalse(template.required)

        self.assertTrue(PartTestTemplate.objects.filter(key='single', part=b).exists())
