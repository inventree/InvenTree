import os
import shutil
import logging

from django.apps import AppConfig
from django.conf import settings


logger = logging.getLogger(__name__)


class LabelConfig(AppConfig):
    name = 'label'

    def ready(self):
        """
        This function is called whenever the label app is loaded
        """

        self.create_stock_item_labels()
        self.create_stock_location_labels()

    def create_stock_item_labels(self):
        """
        Create database entries for the default StockItemLabel templates,
        if they do not already exist
        """

        try:
            from .models import StockItemLabel
        except:
            # Database might not by ready yet
            return

        src_dir = os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            'templates',
            'stockitem',
        )

        dst_dir = os.path.join(
            settings.MEDIA_ROOT,
            'label',
            'inventree',
            'stockitem',
        )

        if not os.path.exists(dst_dir):
            logger.info(f"Creating missing directory: '{dst_dir}'")
            os.makedirs(dst_dir, exist_ok=True)

        labels = [
            {
                'file': 'qr.html',
                'name': 'QR Code',
                'description': 'Simple QR code label',
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
            src_file = os.path.join(src_dir, label['file'])
            dst_file = os.path.join(settings.MEDIA_ROOT, filename)

            if not os.path.exists(dst_file):
                logger.info(f"Copying label template '{dst_file}'")
                shutil.copyfile(src_file, dst_file)

            try:
                # Check if a label matching the template already exists
                if StockItemLabel.objects.filter(label=filename).exists():
                    continue

                logger.info(f"Creating entry for StockItemLabel '{label['name']}'")

                StockItemLabel.objects.create(
                    name=label['name'],
                    description=label['description'],
                    label=filename,
                    filters='',
                    enabled=True
                )
            except:
                pass

    def create_stock_location_labels(self):
        """
        Create database entries for the default StockItemLocation templates,
        if they do not already exist
        """

        try:
            from .models import StockLocationLabel
        except:
            # Database might not yet be ready
            return
        
        src_dir = os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            'templates',
            'stocklocation',
        )

        dst_dir = os.path.join(
            settings.MEDIA_ROOT,
            'label',
            'inventree',
            'stocklocation',
        )

        if not os.path.exists(dst_dir):
            logger.info(f"Creating missing directory: '{dst_dir}'")
            os.makedirs(dst_dir, exist_ok=True)

        labels = [
            {
                'file': 'qr.html',
                'name': 'QR Code',
                'description': 'Simple QR code label',
            },
            {
                'file': 'qr_and_text.html',
                'name': 'QR and text',
                'description': 'Label with QR code and name of location',
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
            src_file = os.path.join(src_dir, label['file'])
            dst_file = os.path.join(settings.MEDIA_ROOT, filename)

            if not os.path.exists(dst_file):
                logger.info(f"Copying label template '{dst_file}'")
                shutil.copyfile(src_file, dst_file)

            try:
                # Check if a label matching the template already exists
                if StockLocationLabel.objects.filter(label=filename).exists():
                    continue

                logger.info(f"Creating entry for StockLocationLabel '{label['name']}'")

                StockLocationLabel.objects.create(
                    name=label['name'],
                    description=label['description'],
                    label=filename,
                    filters='',
                    enabled=True
                )
            except:
                pass
