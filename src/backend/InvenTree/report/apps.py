"""Config options for the report app."""

import logging
import os
from pathlib import Path

from django.apps import AppConfig
from django.core.exceptions import AppRegistryNotReady
from django.core.files.base import ContentFile
from django.db.utils import IntegrityError, OperationalError, ProgrammingError

from maintenance_mode.core import maintenance_mode_on, set_maintenance_mode

import InvenTree.ready

logger = logging.getLogger('inventree')


class ReportConfig(AppConfig):
    """Configuration class for the "report" app."""

    name = 'report'

    def ready(self):
        """This function is called whenever the app is loaded."""
        # Configure logging for PDF generation (disable "info" messages)
        logging.getLogger('fontTools').setLevel(logging.WARNING)
        logging.getLogger('weasyprint').setLevel(logging.WARNING)

        super().ready()

        # skip loading if plugin registry is not loaded or we run in a background thread
        if (
            not InvenTree.ready.isPluginRegistryLoaded()
            or not InvenTree.ready.isInMainThread()
        ):
            return

        if not InvenTree.ready.canAppAccessDatabase(allow_test=False):
            return  # pragma: no cover

        with maintenance_mode_on():
            try:
                self.create_default_labels()
                self.create_default_reports()
            except (
                AppRegistryNotReady,
                IntegrityError,
                OperationalError,
                ProgrammingError,
            ):
                logger.warning(
                    'Database not ready for creating default report templates'
                )

        set_maintenance_mode(False)

    def create_default_labels(self):
        """Create default label templates."""
        # Test if models are ready
        try:
            import report.models
        except Exception:  # pragma: no cover
            # Database is not ready yet
            return

        assert bool(report.models.LabelTemplate is not None)

        label_templates = [
            {
                'file': 'part_label.html',
                'name': 'InvenTree Part Label',
                'description': 'Sample part label',
                'model_type': 'part',
            },
            {
                'file': 'part_label_code128.html',
                'name': 'InvenTree Part Label (Code128)',
                'description': 'Sample part label with Code128 barcode',
                'model_type': 'part',
            },
            {
                'file': 'stockitem_qr.html',
                'name': 'InvenTree Stock Item Label (QR)',
                'description': 'Sample stock item label with QR code',
                'model_type': 'stockitem',
            },
            {
                'file': 'stocklocation_qr_and_text.html',
                'name': 'InvenTree Stock Location Label (QR + Text)',
                'description': 'Sample stock item label with QR code and text',
                'model_type': 'stocklocation',
            },
            {
                'file': 'stocklocation_qr.html',
                'name': 'InvenTree Stock Location Label (QR)',
                'description': 'Sample stock location label with QR code',
                'model_type': 'stocklocation',
            },
            {
                'file': 'buildline_label.html',
                'name': 'InvenTree Build Line Label',
                'description': 'Sample build line label',
                'model_type': 'buildline',
            },
        ]

        for template in label_templates:
            # Ignore matching templates which are already in the database
            if report.models.LabelTemplate.objects.filter(
                name=template['name']
            ).exists():
                continue

            filename = template.pop('file')

            template_file = Path(__file__).parent.joinpath(
                'templates', 'label', filename
            )

            if not template_file.exists():
                logger.warning("Missing template file: '%s'", template['name'])
                continue

            # Read the existing template file
            data = template_file.open('r').read()

            try:
                # Create a new entry
                report.models.LabelTemplate.objects.create(
                    **template, template=ContentFile(data, os.path.basename(filename))
                )
                logger.info("Creating new label template: '%s'", template['name'])
            except Exception:
                pass

    def create_default_reports(self):
        """Create default report templates."""
        # Test if models are ready
        try:
            import report.models
        except Exception:  # pragma: no cover
            # Database is not ready yet
            return

        assert bool(report.models.ReportTemplate is not None)

        # Construct a set of default ReportTemplate instances
        report_templates = [
            {
                'file': 'inventree_bill_of_materials_report.html',
                'name': 'InvenTree Bill of Materials',
                'description': 'Sample bill of materials report',
                'model_type': 'part',
            },
            {
                'file': 'inventree_build_order_report.html',
                'name': 'InvenTree Build Order',
                'description': 'Sample build order report',
                'model_type': 'build',
            },
            {
                'file': 'inventree_purchase_order_report.html',
                'name': 'InvenTree Purchase Order',
                'description': 'Sample purchase order report',
                'model_type': 'purchaseorder',
                'filename_pattern': 'PurchaseOrder-{{ reference }}.pdf',
            },
            {
                'file': 'inventree_sales_order_report.html',
                'name': 'InvenTree Sales Order',
                'description': 'Sample sales order report',
                'model_type': 'salesorder',
                'filename_pattern': 'SalesOrder-{{ reference }}.pdf',
            },
            {
                'file': 'inventree_sales_order_shipment_report.html',
                'name': 'InvenTree Sales Order Shipment',
                'description': 'Sample sales order shipment report',
                'model_type': 'salesordershipment',
                'filename_pattern': 'SalesOrderShipment-{{ reference }}.pdf',
            },
            {
                'file': 'inventree_return_order_report.html',
                'name': 'InvenTree Return Order',
                'description': 'Sample return order report',
                'model_type': 'returnorder',
                'filename_pattern': 'ReturnOrder-{{ reference }}.pdf',
            },
            {
                'file': 'inventree_test_report.html',
                'name': 'InvenTree Test Report',
                'description': 'Sample stock item test report',
                'model_type': 'stockitem',
            },
            {
                'file': 'inventree_stock_location_report.html',
                'name': 'InvenTree Stock Location Report',
                'description': 'Sample stock location report',
                'model_type': 'stocklocation',
            },
        ]

        for template in report_templates:
            # Ignore matching templates which are already in the database
            if report.models.ReportTemplate.objects.filter(
                name=template['name']
            ).exists():
                continue

            filename = template.pop('file')

            template_file = Path(__file__).parent.joinpath(
                'templates', 'report', filename
            )

            if not template_file.exists():
                logger.warning("Missing template file: '%s'", template['name'])
                continue

            # Read the existing template file
            data = template_file.open('r').read()

            # Create a new entry
            try:
                report.models.ReportTemplate.objects.create(
                    **template, template=ContentFile(data, os.path.basename(filename))
                )
                logger.info("Created new report template: '%s'", template['name'])
            except Exception:
                pass
