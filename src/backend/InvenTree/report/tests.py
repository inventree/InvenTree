"""Unit testing for the various report models."""

from io import StringIO

from django.apps import apps
from django.core.cache import cache
from django.urls import reverse

import report.models as report_models
from build.models import Build
from common.models import Attachment
from InvenTree.unit_test import AdminTestCase, InvenTreeAPITestCase
from order.models import ReturnOrder, SalesOrder
from part.models import Part
from plugin.registry import registry
from report.models import LabelTemplate, ReportTemplate
from stock.models import StockItem


class ReportTest(InvenTreeAPITestCase):
    """Base class for unit testing reporting models."""

    fixtures = [
        'category',
        'part',
        'company',
        'location',
        'test_templates',
        'supplier_part',
        'stock',
        'stock_tests',
        'bom',
        'build',
        'order',
        'return_order',
        'sales_order',
    ]

    superuser = True

    def setUp(self):
        """Ensure cache is cleared as part of test setup."""
        cache.clear()

        apps.get_app_config('report').create_default_reports()

        return super().setUp()

    def test_list_endpoint(self):
        """Test that the LIST endpoint works for each report."""
        url = reverse('api-report-template-list')

        response = self.get(url)
        self.assertEqual(response.status_code, 200)

        reports = ReportTemplate.objects.all()

        n = len(reports)
        # API endpoint must return correct number of reports
        self.assertEqual(len(response.data), n)

        # Filter by "enabled" status
        response = self.get(url, {'enabled': True})
        self.assertEqual(len(response.data), n)

        response = self.get(url, {'enabled': False})
        self.assertEqual(len(response.data), 0)

        # Disable each report
        for report in reports:
            report.enabled = False
            report.save()

        # Filter by "enabled" status
        response = self.get(url, {'enabled': True})
        self.assertEqual(len(response.data), 0)

        response = self.get(url, {'enabled': False})
        self.assertEqual(len(response.data), n)

        # Filter by items
        part_pk = Part.objects.first().pk
        report = ReportTemplate.objects.filter(model_type='part').first()

        try:
            response = self.get(
                url, {'model_type': 'part', 'items': part_pk}, expected_code=400
            )
            self.assertIn('model_type', response.data)
            self.assertIn(
                'Select a valid choice. part is not one of the available choices.',
                str(response.data),
            )
            return  # pragma: no cover
        except AssertionError:
            response = self.get(url, {'model_type': 'part', 'items': part_pk})

        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['pk'], report.pk)
        self.assertEqual(response.data[0]['name'], report.name)

    def test_create_endpoint(self):
        """Test that creating a new report works for each report."""
        url = reverse('api-report-template-list')

        # Create a new report
        # Django REST API "APITestCase" does not work like requests - to send a file without it existing on disk,
        # create it as a StringIO object, and upload it under parameter template
        filestr = StringIO(
            '{% extends "label/report_base.html" %}{% block content %}<pre>TEST REPORT</pre>{% endblock content %}'
        )
        filestr.name = 'ExampleTemplate.html'

        data = {
            'name': 'New report',
            'description': 'A fancy new report created through API test',
            'template': filestr,
            'model_type': 'part2',
        }

        # Test with invalid model type
        response = self.post(url, data=data, expected_code=400)

        self.assertIn('"part2" is not a valid choice', str(response.data['model_type']))

        # With valid model type
        data['model_type'] = 'part'
        filestr.seek(0)

        response = self.post(url, data=data, format=None, expected_code=201)

        # Make sure the expected keys are in the response
        self.assertIn('pk', response.data)
        self.assertIn('name', response.data)
        self.assertIn('description', response.data)
        self.assertIn('template', response.data)
        self.assertIn('filters', response.data)
        self.assertIn('enabled', response.data)

        self.assertEqual(response.data['name'], 'New report')
        self.assertEqual(
            response.data['description'], 'A fancy new report created through API test'
        )
        self.assertTrue(response.data['template'].endswith('ExampleTemplate.html'))

    def test_detail_endpoint(self):
        """Test that the DETAIL endpoint works for each report."""
        reports = ReportTemplate.objects.all()

        n = len(reports)

        # Make sure at least one report defined
        self.assertGreaterEqual(n, 1)

        # Check detail page for first report
        response = self.get(
            reverse('api-report-template-detail', kwargs={'pk': reports[0].pk}),
            expected_code=200,
        )

        # Make sure the expected keys are in the response
        self.assertIn('pk', response.data)
        self.assertIn('name', response.data)
        self.assertIn('description', response.data)
        self.assertIn('template', response.data)
        self.assertIn('filters', response.data)
        self.assertIn('enabled', response.data)

        filestr = StringIO(
            '{% extends "label/report_base.html" %}{% block content %}<pre>TEST REPORT VERSION 2</pre>{% endblock content %}'
        )
        filestr.name = 'ExampleTemplate_Updated.html'

        # Check PATCH method
        response = self.patch(
            reverse('api-report-template-detail', kwargs={'pk': reports[0].pk}),
            {
                'name': 'Changed name during test',
                'description': 'New version of the template',
                'template': filestr,
            },
            format=None,
            expected_code=200,
        )

        # Make sure the expected keys are in the response
        self.assertIn('pk', response.data)
        self.assertIn('name', response.data)
        self.assertIn('description', response.data)
        self.assertIn('template', response.data)
        self.assertIn('filters', response.data)
        self.assertIn('enabled', response.data)

        self.assertEqual(response.data['name'], 'Changed name during test')
        self.assertEqual(response.data['description'], 'New version of the template')

        self.assertTrue(
            response.data['template'].endswith('ExampleTemplate_Updated.html')
        )

        # Delete the last report
        response = self.delete(
            reverse('api-report-template-detail', kwargs={'pk': reports[n - 1].pk}),
            expected_code=204,
        )

    def test_metadata(self):
        """Unit tests for the metadata field."""
        p = ReportTemplate.objects.first()

        self.assertEqual(p.metadata, {})

        self.assertIsNone(p.get_metadata('test'))
        self.assertEqual(p.get_metadata('test', backup_value=123), 123)

        # Test update via the set_metadata() method
        p.set_metadata('test', 3)
        self.assertEqual(p.get_metadata('test'), 3)

        for k in ['apple', 'banana', 'carrot', 'carrot', 'banana']:
            p.set_metadata(k, k)

        self.assertEqual(len(p.metadata.keys()), 4)

    def test_report_template_permissions(self):
        """Test that the user permissions are correctly applied.

        - For all /api/report/ endpoints, any authenticated user should have full read access
        - Write access is limited to staff users
        - Non authenticated users should have no access at all
        """
        # First test the "report list" endpoint
        url = reverse('api-report-template-list')

        template = ReportTemplate.objects.first()

        detail_url = reverse('api-report-template-detail', kwargs={'pk': template.pk})

        # Non-authenticated user should have no access
        self.logout()

        self.get(url, expected_code=401)

        # Authenticated user should have read access
        self.user.is_staff = False
        self.user.save()

        self.login()

        # Check read access to template list URL
        self.get(url, expected_code=200)

        # Check read access to template detail URL
        self.get(detail_url, expected_code=200)

        # An update to the report template should fail
        self.patch(
            detail_url,
            data={'description': 'Some new description here?'},
            expected_code=403,
        )

        # Now, test with a staff user
        self.logout()

        self.user.is_staff = True
        self.user.save()

        self.login()

        self.patch(
            detail_url,
            data={'description': 'An updated description'},
            expected_code=200,
        )

        template.refresh_from_db()
        self.assertEqual(template.description, 'An updated description')

    def test_print(self):
        """Test that we can print a report manually."""
        # Find a suitable report template
        template = ReportTemplate.objects.filter(
            enabled=True, model_type='stockitem'
        ).first()

        # Gather some items
        items = StockItem.objects.all()[0:5]

        output = template.print(items)

        self.assertTrue(output.complete)
        self.assertEqual(output.items, 5)
        self.assertIsNotNone(output.output)
        self.assertTrue(output.output.name.endswith('.pdf'))


class LabelTest(InvenTreeAPITestCase):
    """Unit tests for label templates."""

    fixtures = [
        'category',
        'part',
        'company',
        'location',
        'test_templates',
        'supplier_part',
        'stock',
        'stock_tests',
        'bom',
        'build',
        'order',
        'return_order',
        'sales_order',
    ]

    superuser = True

    def setUp(self):
        """Ensure cache is cleared as part of test setup."""
        cache.clear()

        apps.get_app_config('report').create_default_labels()

        return super().setUp()

    def test_print(self):
        """Test manual printing of label templates."""
        # Find a suitable label template
        template = LabelTemplate.objects.filter(enabled=True, model_type='part').first()

        # Gather some items
        parts = Part.objects.all()[0:10]

        # Find the label plugin (render to pdf)
        plugin = registry.get_plugin('inventreelabel')

        self.assertIsNotNone(template)
        self.assertIsNotNone(plugin)

        output = template.print(items=parts, plugin=plugin)

        self.assertTrue(output.complete)
        self.assertEqual(output.items, 10)
        self.assertIsNotNone(output.output)
        self.assertTrue(output.output.name.endswith('.pdf'))


class PrintTestMixins:
    """Mixin that enables e2e printing tests."""

    plugin_ref = 'samplelabelprinter'

    def do_activate_plugin(self):
        """Activate the 'samplelabel' plugin."""
        plugin = registry.get_plugin(self.plugin_ref)
        self.assertIsNotNone(plugin)
        config = plugin.plugin_config()
        self.assertIsNotNone(config)
        config.active = True
        config.save()

    def run_print_test(self, qs, model_type, label: bool = True):
        """Run tests on single and multiple page printing.

        Args:
            qs: class of the base queryset
            model_type: the model type of the queryset
            label: whether the model is a label or report
        """
        mdl = LabelTemplate if label else ReportTemplate
        url = reverse('api-label-print' if label else 'api-report-print')

        qs = qs.objects.all()
        template = mdl.objects.filter(enabled=True, model_type=model_type).first()
        plugin = registry.get_plugin(self.plugin_ref)

        # Single page printing
        self.post(
            url,
            {'template': template.pk, 'plugin': plugin.pk, 'items': [qs[0].pk]},
            expected_code=201,
        )

        # Multi page printing
        self.post(
            url,
            {
                'template': template.pk,
                'plugin': plugin.pk,
                'items': [item.pk for item in qs],
            },
            expected_code=201,
            max_query_time=15,
            max_query_count=500 * len(qs),
        )

        # Test with wrong dimensions
        if not hasattr(template, 'width'):
            return

        org_width = template.width
        template.width = 0
        template.save()
        response = self.post(
            url,
            {'template': template.pk, 'plugin': plugin.pk, 'items': [qs[0].pk]},
            expected_code=400,
        )
        self.assertEqual(str(response.data['template'][0]), 'Invalid label dimensions')
        template.width = org_width
        template.save()


class TestReportTest(PrintTestMixins, ReportTest):
    """Unit testing class for the stock item TestReport model."""

    model = report_models.ReportTemplate

    list_url = 'api-report-template-list'
    detail_url = 'api-report-template-detail'
    print_url = 'api-report-print'

    def setUp(self):
        """Setup function for the stock item TestReport."""
        apps.get_app_config('report').create_default_reports()
        self.do_activate_plugin()

        return super().setUp()

    def test_print(self):
        """Printing tests for the TestReport."""
        template = ReportTemplate.objects.filter(
            enabled=True, model_type='stockitem'
        ).first()

        self.assertIsNotNone(template)

        # Ensure that the 'attach_to_model' attribute is initially False
        template.attach_to_model = False
        template.save()
        template.refresh_from_db()

        self.assertFalse(template.attach_to_model)

        url = reverse(self.print_url)

        # Try to print without providing a valid StockItem
        self.post(url, {'template': template.pk}, expected_code=400)

        # Try to print with an invalid StockItem
        self.post(url, {'template': template.pk, 'items': [9999]}, expected_code=400)

        # Now print with a valid StockItem
        item = StockItem.objects.first()

        n = item.attachments.count()

        response = self.post(
            url, {'template': template.pk, 'items': [item.pk]}, expected_code=201
        )

        # There should be a link to the generated PDF
        self.assertTrue(response.data['output'].startswith('/media/report/'))
        self.assertTrue(response.data['output'].endswith('.pdf'))

        # By default, this should *not* have created an attachment against this stockitem
        self.assertEqual(n, item.attachments.count())
        self.assertFalse(
            Attachment.objects.filter(model_id=item.pk, model_type='stockitem').exists()
        )

        # Now try again, but attach the generated PDF to the StockItem
        template.attach_to_model = True
        template.save()

        response = self.post(
            url, {'template': template.pk, 'items': [item.pk]}, expected_code=201
        )

        # A new attachment should have been created
        self.assertEqual(n + 1, item.attachments.count())
        attachment = item.attachments.order_by('-pk').first()

        # The attachment should be a PDF
        self.assertTrue(attachment.attachment.name.endswith('.pdf'))

    def test_mdl_build(self):
        """Test the Build model."""
        self.run_print_test(Build, 'build', label=False)

    def test_mdl_returnorder(self):
        """Test the ReturnOrder model."""
        self.run_print_test(ReturnOrder, 'returnorder', label=False)

    def test_mdl_salesorder(self):
        """Test the SalesOrder model."""
        self.run_print_test(SalesOrder, 'salesorder', label=False)


class AdminTest(AdminTestCase):
    """Tests for the admin interface integration."""

    def test_admin(self):
        """Test the admin URL."""
        self.helper(model=ReportTemplate)
