"""label app specification"""

import hashlib
import logging
import os
import shutil
import warnings
from pathlib import Path

from django.apps import AppConfig
from django.conf import settings
from django.core.exceptions import AppRegistryNotReady

from InvenTree.ready import canAppAccessDatabase

logger = logging.getLogger("inventree")


def hashFile(filename):
    """Calculate the MD5 hash of a file."""
    md5 = hashlib.md5()

    with open(filename, 'rb') as f:
        data = f.read()
        md5.update(data)

    return md5.hexdigest()


class LabelConfig(AppConfig):
    """App configuration class for the 'label' app"""

    name = 'label'

    def ready(self):
        """This function is called whenever the label app is loaded."""
        if canAppAccessDatabase():
            self.create_labels()  # pragma: no cover

    def create_labels(self):
        """Create all default templates."""
        # Test if models are ready
        try:
            from .models import PartLabel, StockItemLabel, StockLocationLabel
            assert bool(StockLocationLabel is not None)
        except AppRegistryNotReady:  # pragma: no cover
            # Database might not yet be ready
            warnings.warn('Database was not ready for creating labels')
            return

        # Create the categories
        self.create_labels_category(
            StockItemLabel,
            'stockitem',
            [
                {
                    'file': 'qr.html',
                    'name': 'QR Code',
                    'description': 'Simple QR code label',
                    'width': 24,
                    'height': 24,
                },
            ],
        )
        self.create_labels_category(
            StockLocationLabel,
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
                }
            ]
        )
        self.create_labels_category(
            PartLabel,
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
            ]
        )

    def create_labels_category(self, model, ref_name, labels):
        """Create folder and database entries for the default templates, if they do not already exist."""
        # Create root dir for templates
        src_dir = Path(__file__).parent.joinpath(
            'templates',
            'label',
            ref_name,
        )

        dst_dir = settings.MEDIA_ROOT.joinpath(
            'label',
            'inventree',
            ref_name,
        )

        if not dst_dir.exists():
            logger.info(f"Creating required directory: '{dst_dir}'")
            dst_dir.mkdir(parents=True, exist_ok=True)

        # Create lables
        for label in labels:
            self.create_template_label(model, src_dir, ref_name, label)

    def create_template_label(self, model, src_dir, ref_name, label):
        """Ensure a label template is in place."""
        filename = os.path.join(
            'label',
            'inventree',
            ref_name,
            label['file']
        )

        src_file = src_dir.joinpath(label['file'])
        dst_file = settings.MEDIA_ROOT.joinpath(filename)

        to_copy = False

        if dst_file.exists():
            # File already exists - let's see if it is the "same"

            if hashFile(dst_file) != hashFile(src_file):  # pragma: no cover
                logger.info(f"Hash differs for '{filename}'")
                to_copy = True

        else:
            logger.info(f"Label template '{filename}' is not present")
            to_copy = True

        if to_copy:
            logger.info(f"Copying label template '{dst_file}'")
            # Ensure destionation dir exists
            dst_file.parent.mkdir(parents=True, exist_ok=True)

            # Copy file
            shutil.copyfile(src_file, dst_file)

        # Check if a label matching the template already exists
        if model.objects.filter(label=filename).exists():
            return  # pragma: no cover

        logger.info(f"Creating entry for {model} '{label['name']}'")

        model.objects.create(
            name=label['name'],
            description=label['description'],
            label=filename,
            filters='',
            enabled=True,
            width=label['width'],
            height=label['height'],
        )
        return
