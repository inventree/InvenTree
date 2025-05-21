"""Schema processing functions for cleaning up generated schema."""

from itertools import chain
from typing import Optional

from drf_spectacular.contrib.django_oauth_toolkit import DjangoOAuthToolkitScheme
from drf_spectacular.drainage import warn
from drf_spectacular.openapi import AutoSchema
from drf_spectacular.plumbing import ComponentRegistry
from drf_spectacular.utils import _SchemaType
from rest_framework.pagination import LimitOffsetPagination

from InvenTree.permissions import OASTokenMixin
from users.oauth2_scopes import oauth2_scopes


class ExtendedOAuth2Scheme(DjangoOAuthToolkitScheme):
    """Extend drf-spectacular to allow customizing the schema to match the actual API behavior."""

    target_class = 'users.authentication.ExtendedOAuth2Authentication'

    def get_security_requirement(self, auto_schema):
        """Get the security requirement for the current view."""
        ret = super().get_security_requirement(auto_schema)
        if ret:
            return ret

        # If no security requirement is found, try if the view uses our OASTokenMixin
        for permission in auto_schema.view.get_permissions():
            if isinstance(permission, OASTokenMixin):
                alt_scopes = permission.get_required_alternate_scopes(
                    auto_schema.view.request, auto_schema.view
                )
                alt_scopes = alt_scopes.get(auto_schema.method, [])
                return [{self.name: group} for group in alt_scopes]


class ExtendedAutoSchema(AutoSchema):
    """Extend drf-spectacular to allow customizing the schema to match the actual API behavior."""

    def is_bulk_action(self, ref: str) -> bool:
        """Check the class of the current view for the bulk mixins."""
        return ref in [c.__name__ for c in type(self.view).__mro__]

    def get_operation_id(self) -> str:
        """Custom path handling overrides, falling back to default behavior."""
        result_id = super().get_operation_id()

        # rename bulk actions to deconflict with single action operation_id
        if (self.method == 'DELETE' and self.is_bulk_action('BulkDeleteMixin')) or (
            (self.method == 'PUT' or self.method == 'PATCH')
            and self.is_bulk_action('BulkUpdateMixin')
        ):
            action = self.method_mapping[self.method.lower()]
            result_id = result_id.replace(action, 'bulk_' + action)

        return result_id

    def get_operation(
        self,
        path: str,
        path_regex: str,
        path_prefix: str,
        method: str,
        registry: ComponentRegistry,
    ) -> Optional[_SchemaType]:
        """Custom operation handling, falling back to default behavior."""
        operation = super().get_operation(
            path, path_regex, path_prefix, method, registry
        )
        if operation is None:
            return None

        # drf-spectacular doesn't support a body on DELETE endpoints because the semantics are not well-defined and
        # OpenAPI recommends against it. This allows us to generate a schema that follows existing behavior.
        if self.method == 'DELETE' and self.is_bulk_action('BulkDeleteMixin'):
            original_method = self.method
            self.method = 'PUT'
            request_body = self._get_request_body()
            request_body['required'] = True
            operation['requestBody'] = request_body
            self.method = original_method

        # If pagination limit is not set (default state) then all results will return unpaginated. This doesn't match
        # what the schema defines to be the expected result. This forces limit to be present, producing the expected
        # type.
        pagination_class = getattr(self.view, 'pagination_class', None)
        if pagination_class and pagination_class == LimitOffsetPagination:
            parameters = operation.get('parameters', [])
            for parameter in parameters:
                if parameter['name'] == 'limit':
                    parameter['required'] = True

        return operation


def postprocess_required_nullable(result, generator, request, public):
    """Un-require nullable fields.

    Read-only values are all marked as required by spectacular, but InvenTree doesn't always include them in the
    response. This removes them from the required list to allow responses lacking read-only nullable fields to validate
    against the schema.
    """
    # Process schema section
    schemas = result.get('components', {}).get('schemas', {})
    for schema in schemas.values():
        required_fields = schema.get('required', [])
        properties = schema.get('properties', {})

        # copy list to allow removing from it while iterating
        for field in list(required_fields):
            field_dict = properties.get(field, {})
            if field_dict.get('readOnly') and field_dict.get('nullable'):
                required_fields.remove(field)
        if 'required' in schema and len(required_fields) == 0:
            schema.pop('required')

    return result


def postprocess_print_stats(result, generator, request, public):
    """Prints statistics against schema."""
    rlt_dict = {}
    for path in result['paths']:
        for method in result['paths'][path]:
            sec = result['paths'][path][method].get('security', [])
            scopes = list(filter(None, (item.get('oauth2') for item in sec)))
            rlt_dict[f'{path}:{method}'] = {
                'method': method,
                'oauth': list(chain(*scopes)),
                'sec': sec is None,
            }

    # Get paths without oauth2
    no_oauth2 = [
        path for path, details in rlt_dict.items() if not any(details['oauth'])
    ]
    no_oauth2_wa = [path for path in no_oauth2 if not path.startswith('/api/auth/v1/')]
    # Get paths without security
    no_security = [path for path, details in rlt_dict.items() if details['sec']]
    # Get path counts per scope
    scopes = {}
    for path, details in rlt_dict.items():
        if details['oauth']:
            for scope in details['oauth']:
                if scope not in scopes:
                    scopes[scope] = []
                scopes[scope].append(path)
    # Sort scopes by keys
    scopes = dict(sorted(scopes.items()))

    # Print statistics
    print('\nSchema statistics:')
    print(f'Paths without oauth2:                   {len(no_oauth2)}')
    print(f'Paths without oauth2 (without allauth): {len(no_oauth2_wa)}')
    print(f'Paths without security:                 {len(no_security)}\n')
    print('Scope stats:')
    for scope, paths in scopes.items():
        print(f'  {scope}: {len(paths)}')
    print()

    # Check for unknown scopes
    for scope, paths in scopes.items():
        if scope not in oauth2_scopes:
            warn(f'unknown scope `{scope}` in {len(paths)} paths')

    return result
