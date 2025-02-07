"""Check if there are any pending database migrations, and run them."""

from pathlib import Path

from django.conf import settings

import structlog
import yaml
from drf_spectacular.management.commands import spectacular

logger = structlog.get_logger('inventree')


class Command(spectacular.Command):
    """Overwritten command to include allauth schemas."""

    def handle(self, *args, **kwargs):
        """Extended schema generation that patches in allauth schemas."""
        from allauth.headless.spec.internal import schema

        path = Path(schema.__file__).parent.parent / 'doc/openapi.yaml'
        with open(path, 'rb') as f:
            spec = yaml.safe_load(f)
        spec_paths = spec['paths']
        # add 'operationId' to each path
        for path, path_spec in spec_paths.items():
            for method, method_spec in path_spec.items():
                operation_id = method_spec.get('operationId', None)
                if operation_id is None:
                    method_spec['operationId'] = f'{method}{path}'

        settings.SPECTACULAR_SETTINGS['APPEND_PATHS'] = spec_paths

        super().handle(*args, **kwargs)
