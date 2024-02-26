"""label app specification."""

import hashlib
import logging
import os
import shutil
import warnings
from pathlib import Path

from django.apps import AppConfig
from django.conf import settings
from django.core.exceptions import AppRegistryNotReady
from django.core.files.storage import default_storage
from django.db.utils import IntegrityError, OperationalError, ProgrammingError

from maintenance_mode.core import maintenance_mode_on, set_maintenance_mode

import InvenTree.helpers
import InvenTree.ready
from InvenTree.config import ensure_dir
from InvenTree.files import MEDIA_STORAGE_DIR, TEMPLATES_DIR

logger = logging.getLogger('inventree')


class LabelConfig(AppConfig):
    """App configuration class for the 'label' app."""

    name = 'label'

    def ready(self):
        """This function is called whenever the label app is loaded."""
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
                self.create_labels()  # pragma: no cover
            except (
                AppRegistryNotReady,
                IntegrityError,
                OperationalError,
                ProgrammingError,
            ):
                # Database might not yet be ready
                warnings.warn(
                    'Database was not ready for creating labels', stacklevel=2
                )

        set_maintenance_mode(False)

    def create_labels(self):
        """Create all default templates."""
        # Test if models are ready
        import label.models

        assert bool(label.models.StockLocationLabel is not None)

        # Create the categories
        self.create_labels_category(
            label.models.StockItemLabel,
            'stockitem',
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

        self.create_labels_category(
            label.models.StockLocationLabel,
            'stocklocation',
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

        self.create_labels_category(
            label.models.PartLabel,
            'part',
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

        self.create_labels_category(
            label.models.BuildLineLabel,
            'buildline',
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

    def create_labels_category(self, model, ref_name, labels):
        """Create folder and database entries for the default templates, if they do not already exist."""
        # Create root dir for templates
        src_dir = TEMPLATES_DIR.joinpath('label', 'templates', 'label', ref_name)
        dst_dir = MEDIA_STORAGE_DIR.joinpath('label', 'inventree', ref_name)
        ensure_dir(dst_dir, default_storage)

        # Create labels
        for label in labels:
            self.create_template_label(model, src_dir, ref_name, label)

    def create_template_label(self, model, src_dir, ref_name, label):
        """Ensure a label template is in place."""
        filename = os.path.join('label', 'inventree', ref_name, label['file'])

        src_file = src_dir.joinpath(label['file'])
        dst_file = MEDIA_STORAGE_DIR.joinpath(filename)

        to_copy = False

        if dst_file.exists():
            # File already exists - let's see if it is the "same"

            if InvenTree.helpers.hash_file(dst_file) != InvenTree.helpers.hash_file(
                src_file
            ):  # pragma: no cover
                logger.info("Hash differs for '%s'", filename)
                to_copy = True

        else:
            logger.info("Label template '%s' is not present", filename)
            to_copy = True

        if to_copy:
            logger.info("Copying label template '%s'", dst_file)
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

        # Check if a label matching the template already exists
        try:
            if model.objects.filter(label=filename).exists():
                return  # pragma: no cover
        except Exception:
            logger.exception(
                "Failed to query label for '%s' - you should run 'invoke update' first!",
                filename,
            )

        logger.info("Creating entry for %s '%s'", model, label['name'])

        try:
            model.objects.create(
                name=label['name'],
                description=label['description'],
                label=filename,
                filters='',
                enabled=True,
                width=label['width'],
                height=label['height'],
            )
        except Exception:
            logger.warning("Failed to create label '%s'", label['name'])
