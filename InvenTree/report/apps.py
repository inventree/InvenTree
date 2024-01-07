"""Config options for the 'report' app"""

import logging
import os
import shutil
import warnings
from pathlib import Path

from django.apps import AppConfig
from django.conf import settings
from django.core.exceptions import AppRegistryNotReady
from django.db.utils import IntegrityError, OperationalError, ProgrammingError

logger = logging.getLogger("inventree")


class ReportConfig(AppConfig):
    """Configuration class for the 'report' app"""

    name = 'report'

    def ready(self):
        """This function is called whenever the report app is loaded."""
        from InvenTree.ready import (
            canAppAccessDatabase,
            isImportingData,
            isInMainThread,
            isPluginRegistryLoaded,
        )

        # skip loading if plugin registry is not loaded or we run in a background thread
        if not isPluginRegistryLoaded() or not isInMainThread():
            return

        # Configure logging for PDF generation (disable "info" messages)
        logging.getLogger('fontTools').setLevel(logging.WARNING)
        logging.getLogger('weasyprint').setLevel(logging.WARNING)

        # Create entries for default report templates
        if canAppAccessDatabase(allow_test=False) and not isImportingData():
            try:
                self.create_default_test_reports()
                self.create_default_build_reports()
                self.create_default_bill_of_materials_reports()
                self.create_default_purchase_order_reports()
                self.create_default_sales_order_reports()
                self.create_default_return_order_reports()
                self.create_default_stock_location_reports()
            except (
                AppRegistryNotReady,
                IntegrityError,
                OperationalError,
                ProgrammingError,
            ):
                # Database might not yet be ready
                warnings.warn(
                    'Database was not ready for creating reports', stacklevel=2
                )

    def create_default_reports(self, model, reports):
        """Copy default report files across to the media directory."""
        # Source directory for report templates
        src_dir = Path(__file__).parent.joinpath('templates', 'report')

        # Destination directory
        dst_dir = settings.MEDIA_ROOT.joinpath('report', 'inventree', model.getSubdir())

        if not dst_dir.exists():
            logger.info("Creating missing directory: '%s'", dst_dir)
            dst_dir.mkdir(parents=True, exist_ok=True)

        # Copy each report template across (if required)
        for report in reports:
            # Destination filename
            filename = os.path.join(
                'report', 'inventree', model.getSubdir(), report['file']
            )

            src_file = src_dir.joinpath(report['file'])
            dst_file = settings.MEDIA_ROOT.joinpath(filename)

            if not dst_file.exists():
                logger.info("Copying test report template '%s'", dst_file)
                shutil.copyfile(src_file, dst_file)

            try:
                # Check if a report matching the template already exists
                if model.objects.filter(template=filename).exists():
                    continue

                logger.info("Creating new TestReport for '%s'", report.get('name'))

                model.objects.create(
                    name=report['name'],
                    description=report['description'],
                    template=filename,
                    enabled=True,
                )

            except Exception:
                pass

    def create_default_test_reports(self):
        """Create database entries for the default TestReport templates, if they do not already exist."""
        try:
            from .models import TestReport
        except Exception:  # pragma: no cover
            # Database is not ready yet
            return

        # List of test reports to copy across
        reports = [
            {
                'file': 'inventree_test_report.html',
                'name': 'InvenTree Test Report',
                'description': 'Stock item test report',
            }
        ]

        self.create_default_reports(TestReport, reports)

    def create_default_bill_of_materials_reports(self):
        """Create database entries for the default Bill of Material templates (if they do not already exist)"""
        try:
            from .models import BillOfMaterialsReport
        except Exception:  # pragma: no cover
            # Database is not ready yet
            return

        # List of Build reports to copy across
        reports = [
            {
                'file': 'inventree_bill_of_materials_report.html',
                'name': 'Bill of Materials',
                'description': 'Bill of Materials report',
            }
        ]

        self.create_default_reports(BillOfMaterialsReport, reports)

    def create_default_build_reports(self):
        """Create database entries for the default BuildReport templates (if they do not already exist)"""
        try:
            from .models import BuildReport
        except Exception:  # pragma: no cover
            # Database is not ready yet
            return

        # List of Build reports to copy across
        reports = [
            {
                'file': 'inventree_build_order.html',
                'name': 'InvenTree Build Order',
                'description': 'Build Order job sheet',
            }
        ]

        self.create_default_reports(BuildReport, reports)

    def create_default_purchase_order_reports(self):
        """Create database entries for the default SalesOrderReport templates (if they do not already exist)"""
        try:
            from .models import PurchaseOrderReport
        except Exception:  # pragma: no cover
            # Database is not ready yet
            return

        # List of Build reports to copy across
        reports = [
            {
                'file': 'inventree_po_report.html',
                'name': 'InvenTree Purchase Order',
                'description': 'Purchase Order example report',
            }
        ]

        self.create_default_reports(PurchaseOrderReport, reports)

    def create_default_sales_order_reports(self):
        """Create database entries for the default Sales Order report templates (if they do not already exist)"""
        try:
            from .models import SalesOrderReport
        except Exception:  # pragma: no cover
            # Database is not ready yet
            return

        # List of Build reports to copy across
        reports = [
            {
                'file': 'inventree_so_report.html',
                'name': 'InvenTree Sales Order',
                'description': 'Sales Order example report',
            }
        ]

        self.create_default_reports(SalesOrderReport, reports)

    def create_default_return_order_reports(self):
        """Create database entries for the default ReturnOrderReport templates"""
        try:
            from report.models import ReturnOrderReport
        except Exception:  # pragma: no cover
            # Database not yet ready
            return

        # List of templates to copy across
        reports = [
            {
                'file': 'inventree_return_order_report.html',
                'name': 'InvenTree Return Order',
                'description': 'Return Order example report',
            }
        ]

        self.create_default_reports(ReturnOrderReport, reports)

    def create_default_stock_location_reports(self):
        """Create database entries for the default StockLocationReport templates"""
        try:
            from report.models import StockLocationReport
        except Exception:  # pragma: no cover
            # Database not yet ready
            return

        # List of templates to copy across
        reports = [
            {
                'file': 'inventree_slr_report.html',
                'name': 'InvenTree Stock Location',
                'description': 'Stock Location example report',
            }
        ]

        self.create_default_reports(StockLocationReport, reports)
