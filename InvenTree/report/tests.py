"""Unit testing for the various report models"""

import os
import shutil
from pathlib import Path

from django.conf import settings
from django.core.cache import cache
from django.http.response import StreamingHttpResponse
from django.test import TestCase
from django.urls import reverse

from PIL import Image

import report.models as report_models
from build.models import Build
from common.models import InvenTreeSetting, InvenTreeUserSetting
from InvenTree.api_tester import InvenTreeAPITestCase
from report.templatetags import barcode as barcode_tags
from report.templatetags import report as report_tags
from stock.models import StockItem, StockItemAttachment


class ReportTagTest(TestCase):
    """Unit tests for the report template tags"""

    def debug_mode(self, value: bool):
        """Enable or disable debug mode for reports"""
        InvenTreeSetting.set_setting('REPORT_DEBUG_MODE', value, change_user=None)

    def test_asset(self):
        """Tests for asset files"""

        # Test that an error is raised if the file does not exist
        for b in [True, False]:
            self.debug_mode(b)

            with self.assertRaises(FileNotFoundError):
                report_tags.asset("bad_file.txt")

        # Create an asset file
        asset_dir = settings.MEDIA_ROOT.joinpath('report', 'assets')
        asset_dir.mkdir(parents=True, exist_ok=True)
        asset_path = asset_dir.joinpath('test.txt')

        asset_path.write_text("dummy data")

        self.debug_mode(True)
        asset = report_tags.asset('test.txt')
        self.assertEqual(asset, '/media/report/assets/test.txt')

        self.debug_mode(False)
        asset = report_tags.asset('test.txt')
        self.assertEqual(asset, f'file://{asset_dir}/test.txt')

    def test_uploaded_image(self):
        """Tests for retrieving uploaded images"""

        # Test for a missing image
        for b in [True, False]:
            self.debug_mode(b)

            with self.assertRaises(FileNotFoundError):
                report_tags.uploaded_image('/part/something/test.png', replace_missing=False)

            img = report_tags.uploaded_image('/part/something/other.png')
            self.assertTrue('blank_image.png' in img)

        # Create a dummy image
        img_path = 'part/images/'
        img_path = settings.MEDIA_ROOT.joinpath(img_path)
        img_file = img_path.joinpath('test.jpg')

        img_path.mkdir(exist_ok=True)
        img_file.write_text("dummy data")

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

        self.debug_mode(False)
        img = report_tags.uploaded_image('part/images/test.jpg')
        self.assertEqual(img, f'file://{img_path}test.jpg')

    def test_part_image(self):
        """Unit tests for the 'part_image' tag"""

        with self.assertRaises(TypeError):
            report_tags.part_image(None)

    def test_company_image(self):
        """Unit tests for the 'company_image' tag"""

        with self.assertRaises(TypeError):
            report_tags.company_image(None)

    def test_logo_image(self):
        """Unit tests for the 'logo_image' tag"""

        # By default, should return the core InvenTree logo
        for b in [True, False]:
            self.debug_mode(b)
            logo = report_tags.logo_image()
            self.assertIn('inventree.png', logo)


class BarcodeTagTest(TestCase):
    """Unit tests for the barcode template tags"""

    def test_barcode(self):
        """Test the barcode generation tag"""

        barcode = barcode_tags.barcode("12345")

        self.assertTrue(type(barcode) == str)
        self.assertTrue(barcode.startswith('data:image/png;'))

        # Try with a different format
        barcode = barcode_tags.barcode('99999', format='BMP')
        self.assertTrue(type(barcode) == str)
        self.assertTrue(barcode.startswith('data:image/bmp;'))

    def test_qrcode(self):
        """Test the qrcode generation tag"""

        # Test with default settings
        qrcode = barcode_tags.qrcode("hello world")
        self.assertTrue(type(qrcode) == str)
        self.assertTrue(qrcode.startswith('data:image/png;'))
        self.assertEqual(len(qrcode), 700)

        # Generate a much larger qrcode
        qrcode = barcode_tags.qrcode(
            "hello_world",
            version=2,
            box_size=50,
            format='BMP',
        )
        self.assertTrue(type(qrcode) == str)
        self.assertTrue(qrcode.startswith('data:image/bmp;'))
        self.assertEqual(len(qrcode), 309720)


class ReportTest(InvenTreeAPITestCase):
    """Base class for unit testing reporting models"""
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

    model = None
    list_url = None
    detail_url = None
    print_url = None

    def setUp(self):
        """Ensure cache is cleared as part of test setup"""
        cache.clear()
        return super().setUp()

    def copyReportTemplate(self, filename, description):
        """Copy the provided report template into the required media directory."""
        src_dir = Path(__file__).parent.joinpath(
            'templates',
            'report'
        )

        template_dir = os.path.join(
            'report',
            'inventree',
            self.model.getSubdir(),
        )

        dst_dir = settings.MEDIA_ROOT.joinpath(template_dir)

        if not dst_dir.exists():  # pragma: no cover
            dst_dir.mkdir(exist_ok=True)

        src_file = src_dir.joinpath(filename)
        dst_file = dst_dir.joinpath(filename)

        if not dst_file.exists():  # pragma: no cover
            shutil.copyfile(src_file, dst_file)

        # Convert to an "internal" filename
        db_filename = os.path.join(
            template_dir,
            filename
        )

        # Create a database entry for this report template!
        self.model.objects.create(
            name=os.path.splitext(filename)[0],
            description=description,
            template=db_filename,
            enabled=True
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


class TestReportTest(ReportTest):
    """Unit testing class for the stock item TestReport model"""
    model = report_models.TestReport

    list_url = 'api-stockitem-testreport-list'
    detail_url = 'api-stockitem-testreport-detail'
    print_url = 'api-stockitem-testreport-print'

    def setUp(self):
        """Setup function for the stock item TestReport"""
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
    """Unit test class for the BuildReport model"""
    model = report_models.BuildReport

    list_url = 'api-build-report-list'
    detail_url = 'api-build-report-detail'
    print_url = 'api-build-report-print'

    def setUp(self):
        """Setup unit testing functions"""
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
        self.assertEqual(headers['Content-Disposition'], 'attachment; filename="report.pdf"')

        # Now, set the download type to be "inline"
        inline = InvenTreeUserSetting.get_setting_object('REPORT_INLINE', user=self.user)
        inline.value = True
        inline.save()

        response = self.get(url, {'build': 1})
        headers = response.headers
        self.assertEqual(headers['Content-Type'], 'application/pdf')
        self.assertEqual(headers['Content-Disposition'], 'inline; filename="report.pdf"')


class BOMReportTest(ReportTest):
    """Unit test class fot the BillOfMaterialsReport model"""
    model = report_models.BillOfMaterialsReport

    list_url = 'api-bom-report-list'
    detail_url = 'api-bom-report-detail'
    print_url = 'api-bom-report-print'


class PurchaseOrderReportTest(ReportTest):
    """Unit test class fort he PurchaseOrderReport model"""
    model = report_models.PurchaseOrderReport

    list_url = 'api-po-report-list'
    detail_url = 'api-po-report-detail'
    print_url = 'api-po-report-print'


class SalesOrderReportTest(ReportTest):
    """Unit test class for the SalesOrderReport model"""
    model = report_models.SalesOrderReport

    list_url = 'api-so-report-list'
    detail_url = 'api-so-report-detail'
    print_url = 'api-so-report-print'
