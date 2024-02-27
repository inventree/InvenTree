"""Config options for the label app."""

import logging
import os

from django.apps import AppConfig
from django.core.files.storage import default_storage

import InvenTree.helpers
from generic.templating.apps import TemplatingMixin
from InvenTree.files import MEDIA_STORAGE_DIR, TEMPLATES_DIR

logger = logging.getLogger('inventree')
ref = 'label'
db_ref = 'label'


class LabelConfig(TemplatingMixin, AppConfig):
    """Configuration class for the "label" app."""

    name = ref

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

    def get_src_dir(self, ref, ref_name):
        """Get the source directory."""
        return TEMPLATES_DIR.joinpath(ref, 'templates', ref, ref_name)

    def get_new_obj_data(self, data, filename):
        """Get the data for a new template db object."""
        return {
            'name': data['name'],
            'description': data['description'],
            'label': filename,
            'filters': '',
            'enabled': True,
            'width': data['width'],
            'height': data['height'],
        }
