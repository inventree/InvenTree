"""Check if there are any pending database migrations, and run them."""

from pathlib import Path

from django.conf import settings

import structlog
import yaml
from drf_spectacular.management.commands import spectacular

logger = structlog.get_logger('inventree')


def prep_name(ref):
    """Prepend allauth to all ref names."""
    return f'allauth.{ref}'


class Command(spectacular.Command):
    """Overwritten command to include allauth schemas."""

    def proccess_refs(self, value):
        """Prepend ref names."""

        def sub_component_name(name: str) -> str:
            s = name.split('/')
            if len(s) == 4 and s[1] == 'components':
                s[3] = prep_name(s[3])
            return '/'.join(s)

        if isinstance(value, list):
            return [{k: sub_component_name(v) for k, v in val.items()} for val in value]
        elif isinstance(value, dict):
            return {
                k: sub_component_name(v)
                if isinstance(v, str)
                else self.proccess_refs(v)
                for k, v in value.items()
            }

    def handle(self, *args, **kwargs):
        """Extended schema generation that patches in allauth schemas."""
        from allauth.headless.spec.internal import schema

        # paths
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
                # update parameters, resresponses, etc.
                for key, value in method_spec.items():
                    if key in ['parameters', 'responses', 'requestBody']:
                        method_spec[key] = self.proccess_refs(value)

        settings.SPECTACULAR_SETTINGS['APPEND_PATHS'] = spec_paths

        # components
        components = spec['components']
        # Prepend all component names with 'allauth.'
        for component_name, component in components.items():
            new_component = {}
            for sub_component_name, sub_component in component.items():
                new_component[prep_name(sub_component_name)] = sub_component
            components[component_name] = new_component
        settings.SPECTACULAR_SETTINGS['APPEND_COMPONENTS'] = components

        super().handle(*args, **kwargs)
