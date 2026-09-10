"""Tests for the company model database migrations."""

from django_test_migrations.contrib.unittest_case import MigratorTestCase

from InvenTree import unit_test


class TestForwardMigrations(MigratorTestCase):
    """Unit testing class for testing 'company' app migrations."""

    migrate_from = ('company', unit_test.getOldestMigrationFile('company'))
    migrate_to = ('company', unit_test.getNewestMigrationFile('company'))

    def prepare(self):
        """Create some simple Company data, and ensure that it migrates OK."""
        Company = self.old_state.apps.get_model('company', 'company')

        Company.objects.create(
            name='MSPC', description='Michael Scotts Paper Company', is_supplier=True
        )

    def test_migrations(self):
        """Test the database state after applying all migrations."""
        Company = self.new_state.apps.get_model('company', 'company')

        self.assertEqual(Company.objects.count(), 1)


class TestManufacturerPartParameterMigration(MigratorTestCase):
    """Test migration of ManufacturerPartParameter data.

    Ref: https://github.com/inventree/InvenTree/pull/10699

    In the referenced PR:

    - Generic ParameterTemplate and Parameter models were created
    - Existing ManufacturerPartParameter data was migrated to the new models
    - ManufacturerPartParameter model was removed
    """

    migrate_from = ('company', '0076_alter_company_image')
    migrate_to = ('company', '0077_delete_manufacturerpartparameter')

    def prepare(self):
        """Create some existing data before migration."""
        Part = self.old_state.apps.get_model('part', 'part')

        Company = self.old_state.apps.get_model('company', 'company')
        ManufacturerPart = self.old_state.apps.get_model('company', 'manufacturerpart')
        ManufacturerPartParameter = self.old_state.apps.get_model(
            'company', 'manufacturerpartparameter'
        )

        # Create a ManufacturerPart
        part = Part.objects.create(
            name='PART',
            description='A purchaseable part',
            purchaseable=True,
            level=0,
            tree_id=0,
            lft=0,
            rght=0,
        )

        manufacturer = Company.objects.create(
            name='Manufacturer', description='A manufacturer', is_manufacturer=True
        )

        manu_part = ManufacturerPart.objects.create(
            part=part, manufacturer=manufacturer, MPN='MPN-001'
        )

        # Create a parameter which does NOT correlate with any existing template
        for name in ['Width', 'Height', 'Depth']:
            ManufacturerPartParameter.objects.create(
                manufacturer_part=manu_part, name=name, value='100', units='mm'
            )

    def test_manufacturer_part_parameter_migration(self):
        """Test that ManufacturerPartParameter data has been migrated correctly."""
        ContentType = self.new_state.apps.get_model('contenttypes', 'contenttype')
        ParameterTemplate = self.new_state.apps.get_model('common', 'parametertemplate')
        Parameter = self.new_state.apps.get_model('common', 'parameter')
        ManufacturerPart = self.new_state.apps.get_model('company', 'manufacturerpart')

        # There should be 6 ParameterTemplate objects
        self.assertEqual(ParameterTemplate.objects.count(), 3)

        manu_part = ManufacturerPart.objects.first()

        content_type, _created = ContentType.objects.get_or_create(
            app_label='company', model='manufacturerpart'
        )

        # There should be 3 Parameter objects linked to the ManufacturerPart
        params = Parameter.objects.filter(
            model_type=content_type, model_id=manu_part.pk
        )

        self.assertEqual(params.count(), 3)

        for name in ['Width', 'Height', 'Depth']:
            self.assertTrue(params.filter(template__name=name).exists())
