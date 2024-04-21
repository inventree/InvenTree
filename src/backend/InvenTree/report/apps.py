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

    def create_default_reports(self):
        """Create all default templates."""
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
                'file': 'inventree_build_order_base.html',
                'name': 'InvenTree Build Order',
                'description': 'Sample build order report',
                'model_type': 'build',
            },
            {
                'file': 'inventree_po_report_base.html',
                'name': 'InvenTree Purchase Order',
                'description': 'Sample purchase order report',
                'model_type': 'purchaseorder',
            },
            {
                'file': 'inventree_so_report_base.html',
                'name': 'InvenTree Sales Order',
                'description': 'Sample sales order report',
                'model_type': 'salesorder',
            },
            {
                'file': 'inventree_return_order_report_base.html',
                'name': 'InvenTree Return Order',
                'description': 'Sample return order report',
                'model_type': 'returnorder',
            },
            {
                'file': 'inventree_test_report_base.html',
                'name': 'InvenTree Test Report',
                'description': 'Sample stock item test report',
                'model_type': 'stockitem',
            },
            {
                'file': 'inventree_slr_report.html',
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

            template_file = Path(__file__).parent.joinpath(
                'templates', 'report', template['file']
            )

            if not template_file.exists():
                logger.warning("Missing template file: '%s'", template['name'])
                continue

            # Read the existing template file
            data = template_file.open('r').read()

            logger.info("Creating new report template: '%s'", template['name'])

            # Create a new entry
            report.models.ReportTemplate.objects.create(
                name=template['name'],
                description=template['description'],
                model_type=template['model_type'],
                template=ContentFile(data, os.path.basename(template['file'])),
            )
