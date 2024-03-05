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
            level=0, lft=0, rght=0, tree_id=0,
        )

        Build = self.old_state.apps.get_model('build', 'build')

        Build.objects.create(
            part=buildable_part,
            title='A build of some stuff',
            quantity=50,
        )

    def test_items_exist(self):
        """Test to ensure that the 'assembly' field is correctly configured"""
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

    migrate_from = ('build', unit_test.getOldestMigrationFile('build'))
    migrate_to = ('build', '0018_build_reference')

    def prepare(self):
        """Create some builds."""
        Part = self.old_state.apps.get_model('part', 'part')

        part = Part.objects.create(
            name='Part',
            description='A test part',
            level=0, lft=0, rght=0, tree_id=0,
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
        """Test that the build reference is correctly assigned to the PK of the Build"""
        Build = self.new_state.apps.get_model('build', 'build')

        self.assertEqual(Build.objects.count(), 3)

        # Check that the build reference is properly assigned
        for build in Build.objects.all():
            self.assertEqual(str(build.reference), str(build.pk))


class TestReferencePatternMigration(MigratorTestCase):
    """Unit test for data migration which converts reference to new format.

    Ref: https://github.com/inventree/InvenTree/pull/3267
    """

    migrate_from = ('build', '0019_auto_20201019_1302')
    migrate_to = ('build', unit_test.getNewestMigrationFile('build'))

    def prepare(self):
        """Create some initial data prior to migration"""
        Setting = self.old_state.apps.get_model('common', 'inventreesetting')

        # Create a custom existing prefix so we can confirm the operation is working
        Setting.objects.create(
            key='BUILDORDER_REFERENCE_PREFIX',
            value='BuildOrder-',
        )

        Part = self.old_state.apps.get_model('part', 'part')

        assembly = Part.objects.create(
            name='Assy 1',
            description='An assembly',
            level=0, lft=0, rght=0, tree_id=0,
        )

        Build = self.old_state.apps.get_model('build', 'build')

        for idx in range(1, 11):
            Build.objects.create(
                part=assembly,
                title=f"Build {idx}",
                quantity=idx,
                reference=f"{idx + 100}",
                level=0, lft=0, rght=0, tree_id=0,
            )

    def test_reference_migration(self):
        """Test that the reference fields have been correctly updated"""
        Build = self.new_state.apps.get_model('build', 'build')

        for build in Build.objects.all():
            self.assertTrue(build.reference.startswith('BuildOrder-'))

        Setting = self.new_state.apps.get_model('common', 'inventreesetting')

        pattern = Setting.objects.get(key='BUILDORDER_REFERENCE_PATTERN')

        self.assertEqual(pattern.value, 'BuildOrder-{ref:04d}')


class TestBuildLineCreation(MigratorTestCase):
    """Test that build lines are correctly created for existing builds.

    Ref: https://github.com/inventree/InvenTree/pull/4855

    This PR added the 'BuildLine' model, which acts as a link between a Build and a BomItem.

    - Migration 0044 creates BuildLine objects for existing builds.
    - Migration 0046 links any existing BuildItem objects to corresponding BuildLine
    """

    migrate_from = ('build', '0041_alter_build_title')
    migrate_to = ('build', '0047_auto_20230606_1058')

    def prepare(self):
        """Create data to work with"""
        # Model references
        Part = self.old_state.apps.get_model('part', 'part')
        BomItem = self.old_state.apps.get_model('part', 'bomitem')
        Build = self.old_state.apps.get_model('build', 'build')
        BuildItem = self.old_state.apps.get_model('build', 'builditem')
        StockItem = self.old_state.apps.get_model('stock', 'stockitem')

        # The "BuildLine" model does not exist yet
        with self.assertRaises(LookupError):
            self.old_state.apps.get_model('build', 'buildline')

        # Create a part
        assembly = Part.objects.create(
            name='Assembly',
            description='An assembly',
            assembly=True,
            level=0, lft=0, rght=0, tree_id=0,
        )

        # Create components
        for idx in range(1, 11):
            part = Part.objects.create(
                name=f"Part {idx}",
                description=f"Part {idx}",
                level=0, lft=0, rght=0, tree_id=0,
            )

            # Create plentiful stock
            StockItem.objects.create(
                part=part,
                quantity=1000,
                level=0, lft=0, rght=0, tree_id=0,
            )

            # Create a BOM item
            BomItem.objects.create(
                part=assembly,
                sub_part=part,
                quantity=idx,
                reference=f"REF-{idx}",
            )

        # Create some builds
        for idx in range(1, 4):
            build = Build.objects.create(
                part=assembly,
                title=f"Build {idx}",
                quantity=idx * 10,
                reference=f"REF-{idx}",
                level=0, lft=0, rght=0, tree_id=0,
            )

            # Allocate stock to the build
            for bom_item in BomItem.objects.all():
                stock_item = StockItem.objects.get(part=bom_item.sub_part)
                BuildItem.objects.create(
                    build=build,
                    bom_item=bom_item,
                    stock_item=stock_item,
                    quantity=bom_item.quantity,
                )

    def test_build_line_creation(self):
        """Test that the BuildLine objects have been created correctly"""
        Build = self.new_state.apps.get_model('build', 'build')
        BomItem = self.new_state.apps.get_model('part', 'bomitem')
        BuildLine = self.new_state.apps.get_model('build', 'buildline')
        BuildItem = self.new_state.apps.get_model('build', 'builditem')
        StockItem = self.new_state.apps.get_model('stock', 'stockitem')

        # There should be 3x builds
        self.assertEqual(Build.objects.count(), 3)

        # 10x BOMItem objects
        self.assertEqual(BomItem.objects.count(), 10)

        # 10x StockItem objects
        self.assertEqual(StockItem.objects.count(), 10)

        # And 30x BuildLine items (1 for each BomItem for each Build)
        self.assertEqual(BuildLine.objects.count(), 30)

        # And 30x BuildItem objects (1 for each BomItem for each Build)
        self.assertEqual(BuildItem.objects.count(), 30)

        # Check that each BuildItem has been linked to a BuildLine
        for item in BuildItem.objects.all():
            self.assertIsNotNone(item.build_line)
            self.assertEqual(
                item.stock_item.part,
                item.build_line.bom_item.sub_part,
            )

        item = BuildItem.objects.first()

        # Check that the "build" field has been removed
        with self.assertRaises(AttributeError):
            item.build

        # Check that the "bom_item" field has been removed
        with self.assertRaises(AttributeError):
            item.bom_item

        # Check that each BuildLine is correctly configured
        for line in BuildLine.objects.all():
            # Check that the quantity is correct
            self.assertEqual(
                line.quantity,
                line.build.quantity * line.bom_item.quantity,
            )

            # Check that the linked parts are correct
            self.assertEqual(
                line.build.part,
                line.bom_item.part,
            )
