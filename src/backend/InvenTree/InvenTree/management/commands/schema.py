"""Check if there are any pending database migrations, and run them."""

from pathlib import Path

from django.conf import settings

import structlog
import yaml
from drf_spectacular.management.commands import spectacular

logger = structlog.get_logger('inventree')


dja_path_prefix = '/_allauth/{client}/v1/'
dja_ref_prefix = 'allauth'
dja_clean_params = [
    '#/components/parameters/allauth.SessionToken',
    '#/components/parameters/allauth.Client',
]


def prep_name(ref):
    """Prepend django-allauth to all ref names."""
    return f'{dja_ref_prefix}.{ref}'


def clean_params(params):
    """Clean refs of unwanted parameters.

    We don't use them in our API, we only support allauths browser APIs endpoints.
    """
    return [p for p in params if p['$ref'] not in dja_clean_params]


class Command(spectacular.Command):
    """Overwritten command to include django-allauth schemas."""

    def proccess_refs(self, value):
        """Prepend ref names."""

        def sub_component_name(name: str) -> str:
            if not isinstance(name, str):
                return name
            s = name.split('/')
            if len(s) == 4 and s[1] == 'components':
                s[3] = prep_name(s[3])
            return '/'.join(s)

        if isinstance(value, str):
            return sub_component_name(value)
        elif isinstance(value, list):
            return [self.proccess_refs(v) for v in value]
        elif isinstance(value, dict):
            return {k: self.proccess_refs(v) for k, v in value.items()}
        return value

    def handle(self, *args, **kwargs):
        """Extended schema generation that patches in django-allauth schemas."""
        from allauth.headless.spec.internal import schema

        # gather paths
        org_path = Path(schema.__file__).parent.parent / 'doc/openapi.yaml'
        with open(org_path, 'rb') as f:
            spec = yaml.safe_load(f)

        paths = {}
        # Reformat paths
        for path_name, path_spec in spec['paths'].items():
            # strip path name
            path_name = path_name.removeprefix(dja_path_prefix)

            # fix refs
            for method_name, method_spec in path_spec.items():
                if method_spec.get('operationId', None) is None:
                    method_spec['operationId'] = (
                        f'{dja_ref_prefix}_{path_name.replace("/", "_")}_{method_name}'
                    )
                # update all refs
                for key, value in method_spec.items():
                    if key in ['parameters', 'responses', 'requestBody']:
                        method_spec[key] = self.proccess_refs(value)

                # patch out unwanted  parameters - we don't use it
                if params := method_spec.get('parameters', None):
                    method_spec['parameters'] = clean_params(params)

            # prefix path name
            paths[f'/api/auth/v1/{path_name}'] = path_spec
        settings.SPECTACULAR_SETTINGS['APPEND_PATHS'] = paths

        components = {}
        # Reformat components
        for component_name, component_spec in spec['components'].items():
            new_component = {}
            for subcomponent_name, subcomponent_spec in component_spec.items():
                new_component[prep_name(subcomponent_name)] = self.proccess_refs(
                    subcomponent_spec
                )
            components[component_name] = new_component
        settings.SPECTACULAR_SETTINGS['APPEND_COMPONENTS'] = components

        super().handle(*args, **kwargs)
