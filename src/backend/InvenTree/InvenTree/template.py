"""Custom template loader for InvenTree."""

import os

from django.conf import settings
from django.core.files.storage import default_storage
from django.template import Origin, TemplateDoesNotExist
from django.template.loaders.base import Loader as BaseLoader
from django.template.loaders.cached import Loader as CachedLoader


class InvenTreeStorageTemplateLoader(BaseLoader):
    """Custom template loader that loads templates from Django's default storage backend (e.g. S3, SFTP)."""

    def get_storage_candidates(self, template_name: str) -> list[str]:
        """Generate candidate storage paths for a given template name."""
        clean = str(template_name).replace('\\', '/')

        # If path starts with MEDIA_ROOT, strip it
        media_root_str = str(settings.MEDIA_ROOT).replace('\\', '/').rstrip('/')
        if clean.startswith(media_root_str):
            clean = clean[len(media_root_str) :].lstrip('/')

        clean = clean.lstrip('/')
        candidates = [clean]

        # Handle storage location prefix (e.g. S3 / SFTP location)
        location = getattr(default_storage, 'location', '') or ''
        location = str(location).replace('\\', '/').strip('/')
        if location:
            if clean.startswith(f'{location}/'):
                candidates.append(clean[len(location) + 1 :])
            else:
                candidates.append(f'{location}/{clean}')

        # Handle report subdirectory prefix
        if not clean.startswith('report/'):
            candidates.append(f'report/{clean}')

        return candidates

    def get_template_sources(self, template_name):
        """Yield Origin objects for templates found in default storage."""
        for candidate in self.get_storage_candidates(template_name):
            try:
                if default_storage.exists(candidate):
                    yield Origin(
                        name=candidate, template_name=template_name, loader=self
                    )
                    return
            except Exception:
                continue

    def get_contents(self, origin):
        """Return template contents from default storage."""
        try:
            with default_storage.open(origin.name, 'r') as fp:
                content = fp.read()
                if isinstance(content, bytes):
                    content = content.decode('utf-8')
                return content
        except Exception as exc:
            raise TemplateDoesNotExist(origin) from exc


class InvenTreeTemplateLoader(CachedLoader):
    """Custom template loader which bypasses cache for PDF export."""

    def get_template(self, template_name, skip=None):
        """Return a template object for the given template name.

        Any custom report or label templates will be forced to reload (without cache).
        This ensures that generated PDF reports / labels are always up-to-date.
        """
        # List of template patterns to skip cache for
        skip_cache_dirs = [
            os.path.abspath(os.path.join(settings.MEDIA_ROOT, 'report')),
            os.path.abspath(os.path.join(settings.MEDIA_ROOT, 'label')),
            'report/',
            'label/',
            'snippets/',
        ]

        # Initially load the template using the cached loader
        template = CachedLoader.get_template(self, template_name, skip)

        template_path = str(template.name)

        # If the template matches any of the skip patterns, reload it without cache
        if any(template_path.startswith(d) for d in skip_cache_dirs):
            template = BaseLoader.get_template(self, template_name, skip)

        return template
