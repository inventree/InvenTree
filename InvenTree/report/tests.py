# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.urls import reverse

from InvenTree.api_tester import InvenTreeAPITestCase

import report.models as report_models


class ReportTest(InvenTreeAPITestCase):

    fixtures = [
        'category',
        'part',
        'company',
        'location',
        'supplier_part',
        'stock',
        'stock_tests',
    ]

    model = None
    list_url = None
    detail_url = None
    print_url = None

    def setUp(self):
        super().setUp()

    def test_list_endpoint(self):
        """
        Test that the LIST endpoint works for each report
        """

        if self.list_url:
            url = reverse(self.list_url)

            print("URL:", url)
            response = self.get(url)
            self.assertEqual(response.status_code, 200)
            print("Response:")
            print(response)
            print(response.data)


class TestReportTest(ReportTest):

    model = report_models.TestReport

    list_url = 'api-stockitem-testreport-list'
    detail_url = 'api-stockitem-testreport-detail'
    print_url = 'api-stockitem-testreport-print'


class BuildReportTest(ReportTest):

    model = report_models.BuildReport

    list_url = 'api-build-report-list'
    detail_url = 'api-build-report-detail'
    print_url = 'api-build-report-print'


class BOMReportTest(ReportTest):

    model = report_models.BillOfMaterialsReport

    list_url = 'api-bom-report-list'
    detail_url = 'api-bom-report-detail'
    print_url = 'api-bom-report-print'


class POReportTest(ReportTest):

    model = report_models.PurchaseOrderReport

    list_url = 'api-po-report-list'
    detail_url = 'api-po-report-detail'
    print_url = 'api-po-report-print'

class SOReportTest(ReportTest):

    model = report_models.SalesOrderReport

    list_url = 'api-so-report-list'
    detail_url = 'api-so-report-detail'
    print_url = 'api-so-report-print'