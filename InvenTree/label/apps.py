"""Config options for the label app."""

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
ref = 'label'


class LabelConfig(AppConfig):
    """Configuration class for the "label" app."""

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
            import label.models
        except Exception:  # pragma: no cover
            # Database is not ready yet
            return
        assert bool(label.models.StockLocationLabel is not None)

        # Create the categories
        self.create_template_dir(
            label.models.StockItemLabel,
            [
                {
                    'file': 'qr.html',
                    'name': 'QR Code',
                    'description': 'Simple QR code label',
                    'width': 24,
                    'height': 24,
                }
            ],
        )

        self.create_template_dir(
            label.models.StockLocationLabel,
            [
                {
                    'file': 'qr.html',
                    'name': 'QR Code',
                    'description': 'Simple QR code label',
                    'width': 24,
                    'height': 24,
                },
                {
                    'file': 'qr_and_text.html',
                    'name': 'QR and text',
                    'description': 'Label with QR code and name of location',
                    'width': 50,
                    'height': 24,
                },
            ],
        )

        self.create_template_dir(
            label.models.PartLabel,
            [
                {
                    'file': 'part_label.html',
                    'name': 'Part Label',
                    'description': 'Simple part label',
                    'width': 70,
                    'height': 24,
                },
                {
                    'file': 'part_label_code128.html',
                    'name': 'Barcode Part Label',
                    'description': 'Simple part label with Code128 barcode',
                    'width': 70,
                    'height': 24,
                },
            ],
        )

        self.create_template_dir(
            label.models.BuildLineLabel,
            [
                {
                    'file': 'buildline_label.html',
                    'name': 'Build Line Label',
                    'description': 'Example build line label',
                    'width': 125,
                    'height': 48,
                }
            ],
        )

    def create_template_dir(self, model, data):
        """Create folder and database entries for the default templates, if they do not already exist."""
        ref_name = model.getSubdir()

        # Create root dir for templates
        src_dir = TEMPLATES_DIR.joinpath(ref, 'templates', ref, ref_name)
        dst_dir = MEDIA_STORAGE_DIR.joinpath(ref, 'inventree', ref_name)
        ensure_dir(dst_dir, default_storage)

        # Copy each template across (if required)
        for entry in data:
            self.create_template_file(model, src_dir, entry, ref_name)

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
            if model.objects.filter(label=filename).exists():
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
                label=filename,
                filters='',
                enabled=True,
                width=data['width'],
                height=data['height'],
            )
        except Exception:
            logger.warning("Failed to create %s '%s'", ref, data['name'])
