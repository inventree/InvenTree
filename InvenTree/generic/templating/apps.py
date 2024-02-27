"""Shared templating code."""

import logging
import os
import warnings

from django.core.exceptions import AppRegistryNotReady
from django.core.files.storage import default_storage
from django.db.utils import IntegrityError, OperationalError, ProgrammingError

from maintenance_mode.core import maintenance_mode_on, set_maintenance_mode

import InvenTree.helpers
from InvenTree.config import ensure_dir
from InvenTree.files import MEDIA_STORAGE_DIR

logger = logging.getLogger('inventree')


class TemplatingMixin:
    """Mixin that contains shared templating code."""

    def create_defaults(self):
        """Function that creates all default templates for the app."""
        raise NotImplementedError('create_defaults must be implemented')

    def get_src_dir(self, ref, ref_name):
        """Get the source directory for the default templates."""
        raise NotImplementedError('get_src_dir must be implemented')

    def get_new_obj_data(self, data, filename):
        """Get the data for a new template db object."""
        raise NotImplementedError('get_new_obj_data must be implemented')

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
            model.objects.create(**self.get_new_obj_data(data, filename))
        except Exception:
            logger.warning("Failed to create %s '%s'", ref, data['name'])
