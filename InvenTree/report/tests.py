"""Unit testing for the various report models"""

import os
import shutil

from django.conf import settings
from django.core.cache import cache
from django.http.response import StreamingHttpResponse
from django.urls import reverse

import report.models as report_models
from build.models import Build
from common.models import InvenTreeSetting, InvenTreeUserSetting
from InvenTree.api_tester import InvenTreeAPITestCase
from stock.models import StockItem, StockItemAttachment


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
        src_dir = os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            'templates',
            'report'
        )

        template_dir = os.path.join(
            'report',
            'inventree',
            self.model.getSubdir(),
        )

        dst_dir = os.path.join(
            settings.MEDIA_ROOT,
            template_dir
        )

        if not os.path.exists(dst_dir):  # pragma: no cover
            os.makedirs(dst_dir, exist_ok=True)

        src_file = os.path.join(src_dir, filename)
        dst_file = os.path.join(dst_dir, filename)

        if not os.path.exists(dst_file):  # pragma: no cover
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
