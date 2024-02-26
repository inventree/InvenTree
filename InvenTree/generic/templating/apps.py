"""ABC."""

from django.core.files.storage import default_storage

from InvenTree.config import ensure_dir
from InvenTree.files import MEDIA_STORAGE_DIR


class TemplatingMixin:
    """ABC."""

    def create_template_dir(self, model, data):
        """Create folder and database entries for the default templates, if they do not already exist."""
        ref_name = model.getSubdir()

        # Create root dir for templates
        src_dir = self.get_src_dir(ref, ref_name)
        dst_dir = MEDIA_STORAGE_DIR.joinpath(ref, 'inventree', ref_name)
        ensure_dir(dst_dir, default_storage)

        # Copy each template across (if required)
        for entry in data:
            self.create_template_file(model, src_dir, entry, ref_name)
