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
            from .models import StockLocationLabel
            assert bool(StockLocationLabel is not None)
        except AppRegistryNotReady:  # pragma: no cover
            # Database might not yet be ready
            warnings.warn('Database was not ready for creating labels')
            return

        self.create_stock_item_labels()
        self.create_stock_location_labels()
        self.create_part_labels()

    def create_stock_item_labels(self):
        """Create database entries for the default StockItemLabel templates, if they do not already exist."""
        from .models import StockItemLabel

        src_dir = Path(__file__).parent.joinpath(
            'templates',
            'label',
            'stockitem',
        )

        dst_dir = settings.MEDIA_ROOT.joinpath(
            'label',
            'inventree',
            'stockitem',
        )

        if not dst_dir.exists():
            logger.info(f"Creating required directory: '{dst_dir}'")
            dst_dir.mkdir(exist_ok=True)

        labels = [
            {
                'file': 'qr.html',
                'name': 'QR Code',
                'description': 'Simple QR code label',
                'width': 24,
                'height': 24,
            },
        ]

        for label in labels:

            filename = os.path.join(
                'label',
                'inventree',
                'stockitem',
                label['file'],
            )

            # Check if the file exists in the media directory
            src_file = src_dir.joinpath(label['file'])
            dst_file = settings.MEDIA_ROOT.joinpath(filename)

            to_copy = False

            if dst_file.exists():
                # File already exists - let's see if it is the "same",
                # or if we need to overwrite it with a newer copy!

                if hashFile(dst_file) != hashFile(src_file):  # pragma: no cover
                    logger.info(f"Hash differs for '{filename}'")
                    to_copy = True

            else:
                logger.info(f"Label template '{filename}' is not present")
                to_copy = True

            if to_copy:
                logger.info(f"Copying label template '{dst_file}'")
                shutil.copyfile(src_file, dst_file)

            # Check if a label matching the template already exists
            if StockItemLabel.objects.filter(label=filename).exists():
                continue  # pragma: no cover

            logger.info(f"Creating entry for StockItemLabel '{label['name']}'")

            StockItemLabel.objects.create(
                name=label['name'],
                description=label['description'],
                label=filename,
                filters='',
                enabled=True,
                width=label['width'],
                height=label['height'],
            )

    def create_stock_location_labels(self):
        """Create database entries for the default StockItemLocation templates, if they do not already exist."""
        from .models import StockLocationLabel

        src_dir = Path(__file__).parent.joinpath(
            'templates',
            'label',
            'stocklocation',
        )

        dst_dir = settings.MEDIA_ROOT.joinpath(
            'label',
            'inventree',
            'stocklocation',
        )

        if dst_dir.exists():
            logger.info(f"Creating required directory: '{dst_dir}'")
            dst_dir.mkdir(exist_ok=True)

        labels = [
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

        for label in labels:

            filename = os.path.join(
                'label',
                'inventree',
                'stocklocation',
                label['file'],
            )

            # Check if the file exists in the media directory
            src_file = src_dir.joinpath(label['file'])
            dst_file = settings.MEDIA_ROOT.joinpath(filename)

            to_copy = False

            if dst_file.exists():
                # File already exists - let's see if it is the "same",
                # or if we need to overwrite it with a newer copy!

                if hashFile(dst_file) != hashFile(src_file):  # pragma: no cover
                    logger.info(f"Hash differs for '{filename}'")
                    to_copy = True

            else:
                logger.info(f"Label template '{filename}' is not present")
                to_copy = True

            if to_copy:
                logger.info(f"Copying label template '{dst_file}'")
                shutil.copyfile(src_file, dst_file)

            # Check if a label matching the template already exists
            if StockLocationLabel.objects.filter(label=filename).exists():
                continue  # pragma: no cover

            logger.info(f"Creating entry for StockLocationLabel '{label['name']}'")

            StockLocationLabel.objects.create(
                name=label['name'],
                description=label['description'],
                label=filename,
                filters='',
                enabled=True,
                width=label['width'],
                height=label['height'],
            )

    def create_part_labels(self):
        """Create database entries for the default PartLabel templates, if they do not already exist."""
        from .models import PartLabel

        src_dir = Path(__file__).parent.joinpath(
            'templates',
            'label',
            'part',
        )

        dst_dir = settings.MEDIA_ROOT.joinpath(
            'label',
            'inventree',
            'part',
        )

        if not dst_dir.exists():
            logger.info(f"Creating required directory: '{dst_dir}'")
            dst_dir.mkdir(exist_ok=True)

        labels = [
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

        for label in labels:

            filename = os.path.join(
                'label',
                'inventree',
                'part',
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
                shutil.copyfile(src_file, dst_file)

            # Check if a label matching the template already exists
            if PartLabel.objects.filter(label=filename).exists():
                continue  # pragma: no cover

            logger.info(f"Creating entry for PartLabel '{label['name']}'")

            PartLabel.objects.create(
                name=label['name'],
                description=label['description'],
                label=filename,
                filters='',
                enabled=True,
                width=label['width'],
                height=label['height'],
            )
