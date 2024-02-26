"""Config options for the report app."""

import logging
import os
import warnings

from django.apps import AppConfig
from django.core.exceptions import AppRegistryNotReady
from django.core.files.storage import default_storage
from django.db.utils import IntegrityError, OperationalError, ProgrammingError

from maintenance_mode.core import maintenance_mode_on, set_maintenance_mode

import InvenTree.helpers
from generic.templating.apps import TemplatingMixin
from InvenTree.files import MEDIA_STORAGE_DIR, TEMPLATES_DIR

logger = logging.getLogger('inventree')
ref = 'report'
db_ref = 'template'


class ReportConfig(TemplatingMixin, AppConfig):
    """Configuration class for the "report" app."""

    name = ref

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
                    f'Database was not ready for creating {ref}s', stacklevel=2
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

    def create_template_file(self, model, src_dir, data, ref_name):
        """Ensure a label template is in place."""
        # Destination filename
        filename = os.path.join(ref, 'inventree', ref_name, data['file'])

        src_file = src_dir.joinpath(data['file'])
        dst_file = MEDIA_STORAGE_DIR.joinpath(filename)

        do_copy = False

        if not dst_file.exists():
            logger.info("%s template '%s' is not present", ref, filename)
            do_copy = True
        else:
            # Check if the file contents are different
            src_hash = InvenTree.helpers.hash_file(src_file)
            dst_hash = InvenTree.helpers.hash_file(dst_file)

            if src_hash != dst_hash:
                logger.info("Hash differs for '%s'", filename)
                do_copy = True

        if do_copy:
            logger.info("Copying %s template '%s'", ref, dst_file)
            # Ensure destination dir exists
            try:
                dst_file.parent.mkdir(parents=True, exist_ok=True)
            except FileExistsError:
                pass

            # Copy file
            try:
                default_storage.save(filename, src_file.open('rb'))
            except FileExistsError:
                pass

        # Check if a file matching the template already exists
        try:
            if model.objects.filter(**{db_ref: filename}).exists():
                return  # pragma: no cover
        except Exception:
            logger.exception(
                "Failed to query %s for '%s' - you should run 'invoke update' first!",
                ref,
                filename,
            )

        logger.info("Creating entry for %s '%s'", model, data.get('name'))

        try:
            model.objects.create(
                name=data['name'],
                description=data['description'],
                template=filename,
                enabled=True,
            )
        except Exception:
            logger.warning("Failed to create %s '%s'", ref, data['name'])
