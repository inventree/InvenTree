"""Config options for the 'report' app."""

import logging
import os
import warnings

from django.apps import AppConfig
from django.core.exceptions import AppRegistryNotReady
from django.core.files.storage import default_storage
from django.db.utils import IntegrityError, OperationalError, ProgrammingError

from maintenance_mode.core import maintenance_mode_on, set_maintenance_mode

import InvenTree.helpers
from InvenTree.config import ensure_dir
from InvenTree.files import MEDIA_STORAGE_DIR, TEMPLATES_DIR

logger = logging.getLogger('inventree')


class ReportConfig(AppConfig):
    """Configuration class for the 'report' app."""

    name = 'report'

    def ready(self):
        """This function is called whenever the app is loaded."""
        import InvenTree.ready

        # skip loading if plugin registry is not loaded or we run in a background thread
        if (
            not InvenTree.ready.isPluginRegistryLoaded()
            or not InvenTree.ready.isInMainThread()
        ):
            return

        if not InvenTree.ready.canAppAccessDatabase(allow_test=False):
            return  # pragma: no cover

        # Configure logging for PDF generation (disable "info" messages)
        logging.getLogger('fontTools').setLevel(logging.WARNING)
        logging.getLogger('weasyprint').setLevel(logging.WARNING)

        with maintenance_mode_on():
            try:
                self.create_defaults()
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

        set_maintenance_mode(False)

    def create_defaults(self):
        """Create all default templates."""
        # Test if models are ready
        try:
            import report.models
        except Exception:  # pragma: no cover
            # Database is not ready yet
            return
        assert bool(report.models.TestReport is not None)

        # Create the categories
        self.create_default_reports(
            report.models.TestReport,
            [
                {
                    'file': 'inventree_test_report.html',
                    'name': 'InvenTree Test Report',
                    'description': 'Stock item test report',
                }
            ],
        )

        self.create_default_reports(
            report.models.BuildReport,
            [
                {
                    'file': 'inventree_build_order.html',
                    'name': 'InvenTree Build Order',
                    'description': 'Build Order job sheet',
                }
            ],
        )

        self.create_default_reports(
            report.models.BillOfMaterialsReport,
            [
                {
                    'file': 'inventree_bill_of_materials_report.html',
                    'name': 'Bill of Materials',
                    'description': 'Bill of Materials report',
                }
            ],
        )

        self.create_default_reports(
            report.models.PurchaseOrderReport,
            [
                {
                    'file': 'inventree_po_report.html',
                    'name': 'InvenTree Purchase Order',
                    'description': 'Purchase Order example report',
                }
            ],
        )

        self.create_default_reports(
            report.models.SalesOrderReport,
            [
                {
                    'file': 'inventree_so_report.html',
                    'name': 'InvenTree Sales Order',
                    'description': 'Sales Order example report',
                }
            ],
        )

        self.create_default_reports(
            report.models.ReturnOrderReport,
            [
                {
                    'file': 'inventree_return_order_report.html',
                    'name': 'InvenTree Return Order',
                    'description': 'Return Order example report',
                }
            ],
        )

        self.create_default_reports(
            report.models.StockLocationReport,
            [
                {
                    'file': 'inventree_slr_report.html',
                    'name': 'InvenTree Stock Location',
                    'description': 'Stock Location example report',
                }
            ],
        )

    def create_default_reports(self, model, reports):
        """Copy default report files across to the media directory."""
        # Source directory for report templates
        src_dir = TEMPLATES_DIR.joinpath('report', 'templates', 'report')

        # Destination directory
        dst_dir = MEDIA_STORAGE_DIR.joinpath('report', 'inventree', model.getSubdir())
        ensure_dir(dst_dir, default_storage)

        # Copy each report template across (if required)
        for report in reports:
            # Destination filename
            filename = os.path.join(
                'report', 'inventree', model.getSubdir(), report['file']
            )

            src_file = src_dir.joinpath(report['file'])
            dst_file = MEDIA_STORAGE_DIR.joinpath(filename)

            do_copy = False

            if not dst_file.exists():
                logger.info("Report template '%s' is not present", filename)
                do_copy = True
            else:
                # Check if the file contents are different
                src_hash = InvenTree.helpers.hash_file(src_file)
                dst_hash = InvenTree.helpers.hash_file(dst_file)

                if src_hash != dst_hash:
                    logger.info("Hash differs for '%s'", filename)
                    do_copy = True

            if do_copy:
                logger.info("Copying test report template '%s'", dst_file)
                try:
                    default_storage.save(filename, src_file.open('rb'))
                except FileExistsError:
                    pass

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
