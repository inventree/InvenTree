"""Custom template loader for InvenTree"""

import os

from django.conf import settings
from django.template.loaders.base import Loader as BaseLoader
from django.template.loaders.cached import Loader as CachedLoader


class InvenTreeTemplateLoader(CachedLoader):
    """Custom template loader which bypasses cache for PDF export"""

    def get_template(self, template_name, skip=None):
        """Return a template object for the given template name.

        Any custom report or label templates will be forced to reload (without cache).
        This ensures that generated PDF reports / labels are always up-to-date.
        """
        # List of template patterns to skip cache for
        skip_cache_dirs = [
            os.path.abspath(os.path.join(settings.MEDIA_ROOT, 'report')),
            os.path.abspath(os.path.join(settings.MEDIA_ROOT, 'label')),
            'snippets/',
        ]

        # Initially load the template using the cached loader
        template = CachedLoader.get_template(self, template_name, skip)

        template_path = str(template.name)

        # If the template matches any of the skip patterns, reload it without cache
        if any(template_path.startswith(d) for d in skip_cache_dirs):
            template = BaseLoader.get_template(self, template_name, skip)

        return template
