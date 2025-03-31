"""Schema processing functions for cleaning up generated schema."""

from typing import Optional

from drf_spectacular.openapi import AutoSchema
from drf_spectacular.plumbing import ComponentRegistry
from drf_spectacular.utils import _SchemaType


class ExtendedAutoSchema(AutoSchema):
    """Extend drf-spectacular to allow customizing the schema to match the actual API behavior."""

    def is_bulk_delete(self) -> bool:
        """Check the class of the current view for the BulkDeleteMixin."""
        return 'BulkDeleteMixin' in [c.__name__ for c in type(self.view).__mro__]

    def get_operation_id(self) -> str:
        """Custom path handling overrides, falling back to default behavior."""
        result_id = super().get_operation_id()

        # rename bulk deletes to deconflict with single delete operation_id
        if self.method == 'DELETE' and self.is_bulk_delete():
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
        if self.method == 'DELETE' and self.is_bulk_delete():
            original_method = self.method
            self.method = 'PUT'
            request_body = self._get_request_body()
            request_body['required'] = True
            operation['requestBody'] = request_body
            self.method = original_method

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
