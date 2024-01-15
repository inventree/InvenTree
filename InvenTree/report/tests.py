"""Unit testing for the various report models."""

import os
import shutil
from pathlib import Path

from django.conf import settings
from django.core.cache import cache
from django.http.response import StreamingHttpResponse
from django.test import TestCase
from django.urls import reverse
from django.utils.safestring import SafeString

from PIL import Image

import report.models as report_models
from build.models import Build
from common.models import InvenTreeSetting, InvenTreeUserSetting
from InvenTree.unit_test import InvenTreeAPITestCase
from report.templatetags import barcode as barcode_tags
from report.templatetags import report as report_tags
from stock.models import StockItem, StockItemAttachment


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


class BarcodeTagTest(TestCase):
    """Unit tests for the barcode template tags."""

    def test_barcode(self):
        """Test the barcode generation tag."""
        barcode = barcode_tags.barcode('12345')

        self.assertTrue(isinstance(barcode, str))
        self.assertTrue(barcode.startswith('data:image/png;'))

        # Try with a different format
        barcode = barcode_tags.barcode('99999', format='BMP')
        self.assertTrue(isinstance(barcode, str))
        self.assertTrue(barcode.startswith('data:image/bmp;'))

    def test_qrcode(self):
        """Test the qrcode generation tag."""
        # Test with default settings
        qrcode = barcode_tags.qrcode('hello world')
        self.assertTrue(isinstance(qrcode, str))
        self.assertTrue(qrcode.startswith('data:image/png;'))
        self.assertEqual(len(qrcode), 700)

        # Generate a much larger qrcode
        qrcode = barcode_tags.qrcode(
            'hello_world', version=2, box_size=50, format='BMP'
        )
        self.assertTrue(isinstance(qrcode, str))
        self.assertTrue(qrcode.startswith('data:image/bmp;'))
        self.assertEqual(len(qrcode), 309720)


class ReportTest(InvenTreeAPITestCase):
    """Base class for unit testing reporting models."""

    fixtures = [
        'category',
        'part',
        'company',
        'location',
        'supplier_part',
        'stock',
        'stock_tests',
        'bom',
        'build',
    ]

    superuser = True

    model = None
    list_url = None
    detail_url = None
    print_url = None

    def setUp(self):
        """Ensure cache is cleared as part of test setup."""
        cache.clear()
        return super().setUp()

    def copyReportTemplate(self, filename, description):
        """Copy the provided report template into the required media directory."""
        src_dir = Path(__file__).parent.joinpath('templates', 'report')

        template_dir = os.path.join('report', 'inventree', self.model.getSubdir())

        dst_dir = settings.MEDIA_ROOT.joinpath(template_dir)

        if not dst_dir.exists():  # pragma: no cover
            dst_dir.mkdir(parents=True, exist_ok=True)

        src_file = src_dir.joinpath(filename)
        dst_file = dst_dir.joinpath(filename)

        if not dst_file.exists():  # pragma: no cover
            shutil.copyfile(src_file, dst_file)

        # Convert to an "internal" filename
        db_filename = os.path.join(template_dir, filename)

        # Create a database entry for this report template!
        self.model.objects.create(
            name=os.path.splitext(filename)[0],
            description=description,
            template=db_filename,
            enabled=True,
        )

    def test_list_endpoint(self):
        """Test that the LIST endpoint works for each report."""
        if not self.list_url:
            return

        url = reverse(self.list_url)

        response = self.get(url)
        self.assertEqual(response.status_code, 200)

        reports = self.model.objects.all()

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
        if not self.list_url:
            return

        url = reverse(self.list_url)

        # Create a new report
        response = self.post(
            url,
            data={
                'name': 'New report',
                'description': 'A fancy new report created through API test',
            },
            files={
                'template': (
                    'ExampleTemplate.html',
                    '{% extends "label/report_base.html" %}<pre>TEST REPORT</pre>{% endblock content %}',
                )
            },
            expected_code=200,
        )

        # Make sure the expected keys are in the response
        self.assertIn('pk', response.data)
        self.assertIn('name', response.data)
        self.assertIn('description', response.data)
        self.assertIn('template', response.data)
        self.assertIn('filters', response.data)
        self.assertIn('enabled', response.data)

        self.assertEqual(response.data['name'], 'New report')
        self.assertEqual(
            response.data['name'], 'A fancy new report created through API test'
        )
        self.assertTrue(response.data['template'].endswith('ExampleTemplate.html'))

    def test_detail_endpoint(self):
        """Test that the DETAIL endpoint works for each report."""
        if not self.detail_url:
            return

        reports = self.model.objects.all()

        n = len(reports)

        # Make sure at least one report defined
        self.assertGreaterEqual(n, 1)

        # Check detail page for first report
        response = self.get(
            reverse(self.detail_url, kwargs={'pk': reports[0].pk}), expected_code=200
        )

        # Make sure the expected keys are in the response
        self.assertIn('pk', response.data)
        self.assertIn('name', response.data)
        self.assertIn('description', response.data)
        self.assertIn('template', response.data)
        self.assertIn('filters', response.data)
        self.assertIn('enabled', response.data)

        # Check PATCH method
        response = self.patch(
            reverse(self.detail_url, kwargs={'pk': reports[0].pk}),
            {'name': 'Changed name during test'},
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

        # Delete the last report
        response = self.delete(
            reverse(self.detail_url, kwargs={'pk': reports[-1].pk}), expected_code=204
        )

    def test_metadata(self):
        """Unit tests for the metadata field."""
        if self.model is not None:
            p = self.model.objects.first()

            self.assertEqual(p.metadata, {})

            self.assertIsNone(p.get_metadata('test'))
            self.assertEqual(p.get_metadata('test', backup_value=123), 123)

            # Test update via the set_metadata() method
            p.set_metadata('test', 3)
            self.assertEqual(p.get_metadata('test'), 3)

            for k in ['apple', 'banana', 'carrot', 'carrot', 'banana']:
                p.set_metadata(k, k)

            self.assertEqual(len(p.metadata.keys()), 4)


class TestReportTest(ReportTest):
    """Unit testing class for the stock item TestReport model."""

    model = report_models.TestReport

    list_url = 'api-stockitem-testreport-list'
    detail_url = 'api-stockitem-testreport-detail'
    print_url = 'api-stockitem-testreport-print'

    def setUp(self):
        """Setup function for the stock item TestReport."""
        self.copyReportTemplate('inventree_test_report.html', 'stock item test report')

        return super().setUp()

    def test_print(self):
        """Printing tests for the TestReport."""
        report = self.model.objects.first()

        url = reverse(self.print_url, kwargs={'pk': report.pk})

        # Try to print without providing a valid StockItem
        response = self.get(url, expected_code=400)

        # Try to print with an invalid StockItem
        response = self.get(url, {'item': 9999}, expected_code=400)

        # Now print with a valid StockItem
        item = StockItem.objects.first()

        response = self.get(url, {'item': item.pk}, expected_code=200)

        # Response should be a StreamingHttpResponse (PDF file)
        self.assertEqual(type(response), StreamingHttpResponse)

        headers = response.headers
        self.assertEqual(headers['Content-Type'], 'application/pdf')

        # By default, this should *not* have created an attachment against this stockitem
        self.assertFalse(StockItemAttachment.objects.filter(stock_item=item).exists())

        # Change the setting, now the test report should be attached automatically
        InvenTreeSetting.set_setting('REPORT_ATTACH_TEST_REPORT', True, None)

        response = self.get(url, {'item': item.pk}, expected_code=200)

        headers = response.headers
        self.assertEqual(headers['Content-Type'], 'application/pdf')

        # Check that a report has been uploaded
        attachment = StockItemAttachment.objects.filter(stock_item=item).first()
        self.assertIsNotNone(attachment)


class BuildReportTest(ReportTest):
    """Unit test class for the BuildReport model."""

    model = report_models.BuildReport

    list_url = 'api-build-report-list'
    detail_url = 'api-build-report-detail'
    print_url = 'api-build-report-print'

    def setUp(self):
        """Setup unit testing functions."""
        self.copyReportTemplate('inventree_build_order.html', 'build order template')

        return super().setUp()

    def test_print(self):
        """Printing tests for the BuildReport."""
        report = self.model.objects.first()

        url = reverse(self.print_url, kwargs={'pk': report.pk})

        # Try to print without providing a valid BuildOrder
        response = self.get(url, expected_code=400)

        # Try to print with an invalid BuildOrder
        response = self.get(url, {'build': 9999}, expected_code=400)

        # Now print with a valid BuildOrder

        build = Build.objects.first()

        response = self.get(url, {'build': build.pk})

        self.assertEqual(type(response), StreamingHttpResponse)

        headers = response.headers

        self.assertEqual(headers['Content-Type'], 'application/pdf')
        self.assertEqual(
            headers['Content-Disposition'], 'attachment; filename="report.pdf"'
        )

        # Now, set the download type to be "inline"
        inline = InvenTreeUserSetting.get_setting_object(
            'REPORT_INLINE', cache=False, user=self.user
        )
        inline.value = True
        inline.save()

        response = self.get(url, {'build': 1})
        headers = response.headers
        self.assertEqual(headers['Content-Type'], 'application/pdf')
        self.assertEqual(
            headers['Content-Disposition'], 'inline; filename="report.pdf"'
        )


class BOMReportTest(ReportTest):
    """Unit test class for the BillOfMaterialsReport model."""

    model = report_models.BillOfMaterialsReport

    list_url = 'api-bom-report-list'
    detail_url = 'api-bom-report-detail'
    print_url = 'api-bom-report-print'

    def setUp(self):
        """Setup function for the bill of materials Report."""
        self.copyReportTemplate(
            'inventree_bill_of_materials_report.html', 'bill of materials report'
        )

        return super().setUp()


class PurchaseOrderReportTest(ReportTest):
    """Unit test class for the PurchaseOrderReport model."""

    model = report_models.PurchaseOrderReport

    list_url = 'api-po-report-list'
    detail_url = 'api-po-report-detail'
    print_url = 'api-po-report-print'

    def setUp(self):
        """Setup function for the purchase order Report."""
        self.copyReportTemplate('inventree_po_report.html', 'purchase order report')

        return super().setUp()


class SalesOrderReportTest(ReportTest):
    """Unit test class for the SalesOrderReport model."""

    model = report_models.SalesOrderReport

    list_url = 'api-so-report-list'
    detail_url = 'api-so-report-detail'
    print_url = 'api-so-report-print'

    def setUp(self):
        """Setup function for the sales order Report."""
        self.copyReportTemplate('inventree_so_report.html', 'sales order report')

        return super().setUp()


class ReturnOrderReportTest(ReportTest):
    """Unit tests for the ReturnOrderReport model."""

    model = report_models.ReturnOrderReport
    list_url = 'api-return-order-report-list'
    detail_url = 'api-return-order-report-detail'
    print_url = 'api-return-order-report-print'

    def setUp(self):
        """Setup function for the ReturnOrderReport tests."""
        self.copyReportTemplate(
            'inventree_return_order_report.html', 'return order report'
        )

        return super().setUp()


class StockLocationReportTest(ReportTest):
    """Unit tests for the StockLocationReport model."""

    model = report_models.StockLocationReport
    list_url = 'api-stocklocation-report-list'
    detail_url = 'api-stocklocation-report-detail'
    print_url = 'api-stocklocation-report-print'

    def setUp(self):
        """Setup function for the StockLocationReport tests."""
        self.copyReportTemplate('inventree_slr_report.html', 'stock location report')

        return super().setUp()
