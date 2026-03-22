"""Schema processing functions for cleaning up generated schema."""

from itertools import chain
from typing import Any, Optional

from django.conf import settings

from drf_spectacular.contrib.django_oauth_toolkit import DjangoOAuthToolkitScheme
from drf_spectacular.drainage import warn
from drf_spectacular.openapi import AutoSchema
from drf_spectacular.plumbing import ComponentRegistry
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiParameter,
    _SchemaType,
    extend_schema,
    extend_schema_view,
)
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

        parameters = operation.get('parameters', [])

        # If pagination limit is not set (default state) then all results will return unpaginated. This doesn't match
        # what the schema defines to be the expected result. This forces limit to be present, producing the expected
        # type.
        pagination_class = getattr(self.view, 'pagination_class', None)
        if pagination_class and pagination_class == LimitOffsetPagination:
            for parameter in parameters:
                if parameter['name'] == 'limit':
                    parameter['required'] = True

        # Add valid order selections to the ordering field description.
        ordering_fields = getattr(self.view, 'ordering_fields', None)
        if ordering_fields is not None:
            for parameter in parameters:
                if parameter['name'] == 'ordering':
                    schema_order = []
                    for field in ordering_fields:
                        schema_order.append(field)
                        schema_order.append('-' + field)
                    parameter['schema']['enum'] = schema_order

        # Add valid search fields to the search description.
        search_fields = getattr(self.view, 'search_fields', None)

        if search_fields is not None:
            # Ensure consistent ordering of search fields
            search_fields = sorted(search_fields)
            for parameter in parameters:
                if parameter['name'] == 'search':
                    parameter['description'] = (
                        f'{parameter["description"]} Searched fields: {", ".join(search_fields)}.'
                    )

        # Change return to array type, simply annotating this return type attempts to paginate, which doesn't work for
        # a create method and removing the pagination also affects the list method
        if self.method == 'POST' and type(self.view).__name__ == 'StockList':
            schema = operation['responses']['201']['content']['application/json'][
                'schema'
            ]
            schema['type'] = 'array'
            schema['items'] = {'$ref': schema['$ref']}
            del schema['$ref']

        # Add vendor extensions for custom behavior
        operation.update(self.get_inventree_extensions())

        return operation

    def get_inventree_extensions(self):
        """Add InvenTree specific extensions to the schema."""
        from rest_framework.generics import RetrieveAPIView
        from rest_framework.mixins import RetrieveModelMixin, UpdateModelMixin

        from data_exporter.mixins import DataExportViewMixin
        from InvenTree.api import BulkOperationMixin
        from InvenTree.mixins import CleanMixin

        lvl = settings.SCHEMA_VENDOREXTENSION_LEVEL
        """Level of detail for InvenTree extensions."""

        if lvl == 0:
            return {}

        mro = self.view.__class__.__mro__

        data = {}
        if lvl >= 1:
            data['x-inventree-meta'] = {
                'version': '1.0',
                'is_detail': any(
                    a in mro
                    for a in [RetrieveModelMixin, UpdateModelMixin, RetrieveAPIView]
                ),
                'is_bulk': BulkOperationMixin in mro,
                'is_cleaned': CleanMixin in mro,
                'is_filtered': hasattr(self.view, 'output_options'),
                'is_exported': DataExportViewMixin in mro,
            }
        if lvl >= 2:
            data['x-inventree-components'] = [str(a) for a in mro]
            try:
                qs = self.view.get_queryset()
                qs = qs.model if qs is not None and hasattr(qs, 'model') else None
            except Exception:
                qs = None

            data['x-inventree-model'] = {
                'scope': 'core',
                'model': str(qs.__name__) if qs else None,
                'app': str(qs._meta.app_label) if qs else None,
            }

        return data


def postprocess_schema_enums(result, generator, **kwargs):
    """Override call to drf-spectacular's enum postprocessor to filter out specific warnings."""
    from drf_spectacular import drainage

    # Monkey-patch the warn function temporarily
    original_warn = drainage.warn

    def custom_warn(msg: str, delayed: Any = None) -> None:
        """Custom patch to ignore some drf-spectacular warnings.

        - Some warnings are unavoidable due to the way that InvenTree implements generic relationships (via ContentType).
        - The cleanest way to handle this appears to be to override the 'warn' function from drf-spectacular.

        Ref: https://github.com/inventree/InvenTree/pull/10699
        """
        ignore_patterns = [
            'enum naming encountered a non-optimally resolvable collision for fields named "model_type"'
        ]

        if any(pattern in msg for pattern in ignore_patterns):
            return

        original_warn(msg, delayed)

    # Replace the warn function with our custom version
    drainage.warn = custom_warn

    import drf_spectacular.hooks

    result = drf_spectacular.hooks.postprocess_schema_enums(result, generator, **kwargs)

    # Restore the original warn function
    drainage.warn = original_warn

    return result


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

    # Raise error if the paths missing scopes are not specifically excluded from oauth2
    wrong_url = [
        path for path in no_oauth2_wa if path not in settings.OAUTH2_CHECK_EXCLUDED
    ]
    if len(wrong_url) > 0:
        warn(
            f'Found {len(wrong_url)} paths without oauth2 that are not excluded:\n{", ".join(wrong_url)}. '
            '\n\nPlease check the schema and add oauth2 scopes where necessary.'
        )

    return result


def schema_for_view_output_options(view_class):
    """A class decorator that automatically generates schema parameters for a view.

    It works by introspecting the `output_options` attribute on the view itself.
    This decorator reads the `output_options` attribute from the view class,
    extracts the `OPTIONS` list from it, and creates an OpenApiParameter for each option.
    """
    output_config_class = view_class.output_options

    parameters = []
    for option in output_config_class.OPTIONS:
        param = OpenApiParameter(
            name=option.flag,
            type=OpenApiTypes.BOOL,
            location=OpenApiParameter.QUERY,
            description=option.description,
            default=option.default,
        )
        parameters.append(param)

    extended_view = extend_schema_view(get=extend_schema(parameters=parameters))(
        view_class
    )
    return extended_view
