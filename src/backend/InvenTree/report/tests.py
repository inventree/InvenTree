"""Unit testing for the various report models."""

from io import StringIO

from django.apps import apps
from django.conf import settings
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from django.utils.safestring import SafeString

import pytz
from PIL import Image

import report.models as report_models
from build.models import Build
from common.models import Attachment, InvenTreeSetting
from InvenTree.unit_test import AdminTestCase, InvenTreeAPITestCase
from order.models import ReturnOrder, SalesOrder
from plugin.registry import registry
from report.models import LabelTemplate, ReportTemplate
from report.templatetags import barcode as barcode_tags
from report.templatetags import report as report_tags
from stock.models import StockItem


class ReportTagTest(TestCase):
    """Unit tests for the report template tags."""

    def debug_mode(self, value: bool):
        """Enable or disable debug mode for reports."""
        InvenTreeSetting.set_setting('REPORT_DEBUG_MODE', value, change_user=None)

    def test_getindex(self):
        """Tests for the 'getindex' template tag."""
        fn = report_tags.getindex
        data = [1, 2, 3, 4, 5, 6]

        # Out of bounds or invalid
        self.assertEqual(fn(data, -1), None)
        self.assertEqual(fn(data, 99), None)
        self.assertEqual(fn(data, 'xx'), None)

        for idx in range(len(data)):
            self.assertEqual(fn(data, idx), data[idx])

    def test_getkey(self):
        """Tests for the 'getkey' template tag."""
        data = {'hello': 'world', 'foo': 'bar', 'with spaces': 'withoutspaces', 1: 2}

        for k, v in data.items():
            self.assertEqual(report_tags.getkey(data, k), v)

    def test_asset(self):
        """Tests for asset files."""
        # Test that an error is raised if the file does not exist
        for b in [True, False]:
            self.debug_mode(b)

            with self.assertRaises(FileNotFoundError):
                report_tags.asset('bad_file.txt')

        # Create an asset file
        asset_dir = settings.MEDIA_ROOT.joinpath('report', 'assets')
        asset_dir.mkdir(parents=True, exist_ok=True)
        asset_path = asset_dir.joinpath('test.txt')

        asset_path.write_text('dummy data')

        self.debug_mode(True)
        asset = report_tags.asset('test.txt')
        self.assertEqual(asset, '/media/report/assets/test.txt')

        # Ensure that a 'safe string' also works
        asset = report_tags.asset(SafeString('test.txt'))
        self.assertEqual(asset, '/media/report/assets/test.txt')

        self.debug_mode(False)
        asset = report_tags.asset('test.txt')
        self.assertEqual(asset, f'file://{asset_dir}/test.txt')

    def test_uploaded_image(self):
        """Tests for retrieving uploaded images."""
        # Test for a missing image
        for b in [True, False]:
            self.debug_mode(b)

            with self.assertRaises(FileNotFoundError):
                report_tags.uploaded_image(
                    '/part/something/test.png', replace_missing=False
                )

            img = str(report_tags.uploaded_image('/part/something/other.png'))

            if b:
                self.assertIn('blank_image.png', img)
            else:
                self.assertIn('data:image/png;charset=utf-8;base64,', img)

        # Create a dummy image
        img_path = 'part/images/'
        img_path = settings.MEDIA_ROOT.joinpath(img_path)
        img_file = img_path.joinpath('test.jpg')

        img_path.mkdir(parents=True, exist_ok=True)
        img_file.write_text('dummy data')

        # Test in debug mode. Returns blank image as dummy file is not a valid image
        self.debug_mode(True)
        img = report_tags.uploaded_image('part/images/test.jpg')
        self.assertEqual(img, '/static/img/blank_image.png')

        # Now, let's create a proper image
        img = Image.new('RGB', (128, 128), color='RED')
        img.save(img_file)

        # Try again
        img = report_tags.uploaded_image('part/images/test.jpg')
        self.assertEqual(img, '/media/part/images/test.jpg')

        # Ensure that a 'safe string' also works
        img = report_tags.uploaded_image(SafeString('part/images/test.jpg'))
        self.assertEqual(img, '/media/part/images/test.jpg')

        self.debug_mode(False)
        img = report_tags.uploaded_image('part/images/test.jpg')
        self.assertTrue(img.startswith('data:image/png;charset=utf-8;base64,'))

        img = report_tags.uploaded_image(SafeString('part/images/test.jpg'))
        self.assertTrue(img.startswith('data:image/png;charset=utf-8;base64,'))

    def test_part_image(self):
        """Unit tests for the 'part_image' tag."""
        with self.assertRaises(TypeError):
            report_tags.part_image(None)

    def test_company_image(self):
        """Unit tests for the 'company_image' tag."""
        with self.assertRaises(TypeError):
            report_tags.company_image(None)

    def test_logo_image(self):
        """Unit tests for the 'logo_image' tag."""
        # By default, should return the core InvenTree logo
        for b in [True, False]:
            self.debug_mode(b)
            logo = report_tags.logo_image()
            self.assertIn('inventree.png', logo)

    def test_maths_tags(self):
        """Simple tests for mathematical operator tags."""
        self.assertEqual(report_tags.add(1, 2), 3)
        self.assertEqual(report_tags.subtract(10, 4.2), 5.8)
        self.assertEqual(report_tags.multiply(2.3, 4), 9.2)
        self.assertEqual(report_tags.divide(100, 5), 20)

    @override_settings(TIME_ZONE='America/New_York')
    def test_date_tags(self):
        """Test for date formatting tags.

        - Source timezone is Australia/Sydney
        - Server timezone is America/New York
        """
        time = timezone.datetime(
            year=2024,
            month=3,
            day=13,
            hour=12,
            minute=30,
            second=0,
            tzinfo=pytz.timezone('Australia/Sydney'),
        )

        # Format a set of tests: timezone, format, expected
        tests = [
            (None, None, '2024-03-12T22:25:00-04:00'),
            (None, '%d-%m-%y', '12-03-24'),
            ('UTC', None, '2024-03-13T02:25:00+00:00'),
            ('UTC', '%d-%B-%Y', '13-March-2024'),
            ('Europe/Amsterdam', None, '2024-03-13T03:25:00+01:00'),
            ('Europe/Amsterdam', '%y-%m-%d %H:%M', '24-03-13 03:25'),
        ]

        for tz, fmt, expected in tests:
            result = report_tags.format_datetime(time, tz, fmt)
            self.assertEqual(result, expected)

    def test_icon(self):
        """Test the icon template tag."""
        for icon in [None, '', 'not:the-correct-format', 'any-non-existent-icon']:
            self.assertEqual(report_tags.icon(icon), '')

        self.assertEqual(
            report_tags.icon('ti:package:outline'),
            f'<i class="icon " style="font-family: inventree-icon-font-ti">{chr(int("eaff", 16))}</i>',
        )
        self.assertEqual(
            report_tags.icon(
                'ti:package:outline', **{'class': 'my-custom-class my-seconds-class'}
            ),
            f'<i class="icon my-custom-class my-seconds-class" style="font-family: inventree-icon-font-ti">{chr(int("eaff", 16))}</i>',
        )

    def test_include_icon_fonts(self):
        """Test the include_icon_fonts template tag."""
        style = report_tags.include_icon_fonts()

        self.assertIn('@font-face {', style)
        self.assertIn("font-family: 'inventree-icon-font-ti';", style)
        self.assertIn('tabler-icons/tabler-icons.ttf', style)
        self.assertIn('.icon {', style)


class BarcodeTagTest(TestCase):
    """Unit tests for the barcode template tags."""

    def test_barcode(self):
        """Test the barcode generation tag."""
        barcode = barcode_tags.barcode('12345')

        self.assertIsInstance(barcode, str)
        self.assertTrue(barcode.startswith('data:image/png;'))

        # Try with a different format
        barcode = barcode_tags.barcode('99999', format='BMP')
        self.assertIsInstance(barcode, str)
        self.assertTrue(barcode.startswith('data:image/bmp;'))

    def test_qrcode(self):
        """Test the qrcode generation tag."""
        # Test with default settings
        qrcode = barcode_tags.qrcode('hello world')
        self.assertIsInstance(qrcode, str)
        self.assertTrue(qrcode.startswith('data:image/png;'))
        self.assertEqual(len(qrcode), 700)

        # Generate a much larger qrcode
        qrcode = barcode_tags.qrcode(
            'hello_world', version=2, box_size=50, format='BMP'
        )
        self.assertIsInstance(qrcode, str)
        self.assertTrue(qrcode.startswith('data:image/bmp;'))
        self.assertEqual(len(qrcode), 309720)


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

        url = reverse(self.print_url)

        # Try to print without providing a valid StockItem
        self.post(url, {'template': template.pk}, expected_code=400)

        # Try to print with an invalid StockItem
        self.post(url, {'template': template.pk, 'items': [9999]}, expected_code=400)

        # Now print with a valid StockItem
        item = StockItem.objects.first()

        response = self.post(
            url, {'template': template.pk, 'items': [item.pk]}, expected_code=201
        )

        # There should be a link to the generated PDF
        self.assertEqual(response.data['output'].startswith('/media/report/'), True)

        # By default, this should *not* have created an attachment against this stockitem
        self.assertFalse(
            Attachment.objects.filter(model_id=item.pk, model_type='stockitem').exists()
        )

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
