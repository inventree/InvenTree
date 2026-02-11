"""Extended schema generator."""

from pathlib import Path
from typing import TypeVar

from django.conf import settings

import structlog
import yaml
from drf_spectacular.management.commands import spectacular

T = TypeVar('T')
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


def sub_component_name(name: T) -> T | str:
    """Clean up component references."""
    if not isinstance(name, str):
        return name
    s = name.split('/')
    if len(s) == 4 and s[1] == 'components':
        s[3] = prep_name(s[3])
    return '/'.join(s)


def clean_params(params):
    """Clean refs of unwanted parameters.

    We don't use them in our API, we only support allauths browser APIs endpoints.
    """
    return [p for p in params if p['$ref'] not in dja_clean_params]


class Command(spectacular.Command):
    """Overwritten command to include django-allauth schemas."""

    def proccess_refs(self, value):
        """Prepend ref names."""
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
        for p_name, p_spec in spec['paths'].items():
            # strip path name
            p_name = (
                p_name
                .removeprefix(dja_path_prefix)
                .removeprefix('/_allauth/browser/v1/')
                .removeprefix('/_allauth/app/v1/')
            )

            # fix refs
            for m_name, m_spec in p_spec.items():
                if m_spec.get('operationId', None) is None:
                    m_spec['operationId'] = (
                        f'{dja_ref_prefix}_{p_name.replace("/", "_")}_{m_name}'
                    )
                # update all refs
                for key, value in m_spec.items():
                    if key in ['parameters', 'responses', 'requestBody']:
                        m_spec[key] = self.proccess_refs(value)

                # patch out unwanted  parameters - we don't use it
                if params := m_spec.get('parameters', None):
                    m_spec['parameters'] = clean_params(params)

            # prefix path name
            paths[f'/api/auth/v1/{p_name}'] = p_spec
        settings.SPECTACULAR_SETTINGS['APPEND_PATHS'] = paths

        components = {}
        # Reformat components
        for c_name, c_spec in spec['components'].items():
            new_component = {}
            for sc_name, sc_spec in c_spec.items():
                new_component[prep_name(sc_name)] = self.proccess_refs(sc_spec)
            components[c_name] = new_component

        # Remove unused parameters
        for p in dja_clean_params:
            components['parameters'].pop(p.replace('#/components/parameters/', ''))

        settings.SPECTACULAR_SETTINGS['APPEND_COMPONENTS'] = components

        super().handle(*args, **kwargs)

        return 'done'
