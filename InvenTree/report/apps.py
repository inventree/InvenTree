"""Config options for the report app."""

import logging

from django.apps import AppConfig

from generic.templating.apps import TemplatingMixin
from InvenTree.files import TEMPLATES_DIR

logger = logging.getLogger('inventree')
ref = 'report'
db_ref = 'template'


class ReportConfig(TemplatingMixin, AppConfig):
    """Configuration class for the "report" app."""

    name = ref

    def ready(self):
        """This function is called whenever the app is loaded."""
        # Configure logging for PDF generation (disable "info" messages)
        logging.getLogger('fontTools').setLevel(logging.WARNING)
        logging.getLogger('weasyprint').setLevel(logging.WARNING)

        super().ready()

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
        self.create_template_dir(
            report.models.TestReport,
            [
                {
                    'file': 'inventree_test_report.html',
                    'name': 'InvenTree Test Report',
                    'description': 'Stock item test report',
                }
            ],
        )

        self.create_template_dir(
            report.models.BuildReport,
            [
                {
                    'file': 'inventree_build_order.html',
                    'name': 'InvenTree Build Order',
                    'description': 'Build Order job sheet',
                }
            ],
        )

        self.create_template_dir(
            report.models.BillOfMaterialsReport,
            [
                {
                    'file': 'inventree_bill_of_materials_report.html',
                    'name': 'Bill of Materials',
                    'description': 'Bill of Materials report',
                }
            ],
        )

        self.create_template_dir(
            report.models.PurchaseOrderReport,
            [
                {
                    'file': 'inventree_po_report.html',
                    'name': 'InvenTree Purchase Order',
                    'description': 'Purchase Order example report',
                }
            ],
        )

        self.create_template_dir(
            report.models.SalesOrderReport,
            [
                {
                    'file': 'inventree_so_report.html',
                    'name': 'InvenTree Sales Order',
                    'description': 'Sales Order example report',
                }
            ],
        )

        self.create_template_dir(
            report.models.ReturnOrderReport,
            [
                {
                    'file': 'inventree_return_order_report.html',
                    'name': 'InvenTree Return Order',
                    'description': 'Return Order example report',
                }
            ],
        )

        self.create_template_dir(
            report.models.StockLocationReport,
            [
                {
                    'file': 'inventree_slr_report.html',
                    'name': 'InvenTree Stock Location',
                    'description': 'Stock Location example report',
                }
            ],
        )

    def get_src_dir(self, ref, ref_name):
        """Get the source directory."""
        return TEMPLATES_DIR.joinpath(ref, 'templates', ref)

    def get_new_obj_data(self, data, filename):
        """Get the data for a new template db object."""
        return {
            'name': data['name'],
            'description': data['description'],
            'template': filename,
            'enabled': True,
        }
