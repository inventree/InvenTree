"""Shared templating code."""

import warnings

from django.core.exceptions import AppRegistryNotReady
from django.core.files.storage import default_storage
from django.db.utils import IntegrityError, OperationalError, ProgrammingError

from maintenance_mode.core import maintenance_mode_on, set_maintenance_mode

from InvenTree.config import ensure_dir
from InvenTree.files import MEDIA_STORAGE_DIR


class TemplatingMixin:
    """Mixin that contains shared templating code."""

    def create_defaults(self):
        """Function that creates all default templates for the app."""
        raise NotImplementedError('create_defaults must be implemented')

    def get_src_dir(self, ref, ref_name):
        """Get the source directory for the default templates."""
        raise NotImplementedError('get_src_dir must be implemented')

    # Standardized code
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
