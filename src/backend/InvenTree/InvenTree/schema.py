"""Schema processing functions for cleaning up generated schema."""


def postprocess_bulk_delete(result, generator, request, public):
    """Add a request body to bulk DELETE endpoints.

    drf-spectacular doesn't support a body on DELETE endpoints because the semantics are not well-defined and OpenAPI
    recommends against it. This allows us to generate a schema that follows existing behavior.
    """
    request_schema = {'schema': {'$ref': '#/components/schemas/BulkDeleteRequest'}}
    request_body = {
        'content': {
            'application/json': request_schema,
            'application/x-www-form-urlencoded': request_schema,
            'multipart/form-data': request_schema,
        },
        'required': True,
    }

    # Update relevant operations to reference the bulk delete schema
    target_operation_suffix = '_destroy'
    paths = result.get('paths', {})
    for path, operations in paths.items():
        # Anything ending in a path parameter is not a bulk operation
        if path.endswith('/{id}/'):
            continue

        delete_operation = operations.get('delete', {})
        operation_id = delete_operation.get('operationId', '')
        if operation_id.endswith(target_operation_suffix):
            # change id to deconflict with single destroy operations
            delete_operation['operationId'] = operation_id.replace(
                target_operation_suffix, '_bulk_destroy'
            )
            delete_operation['requestBody'] = request_body

    # Add BulkDeleteRequest to schemas: because drf-spectacular strips requests from delete operations there's no way
    # to attach a serializer to generate this automatically
    schema_def = {
        'type': 'object',
        'description': 'Parameters for selecting items to bulk delete.',
        'properties': {
            'items': {
                'type': 'array',
                'items': {'type': 'integer'},
                'description': 'A list of primary key values',
            },
            'filters': {
                'type': 'object',
                'additionalProperties': {'type': 'string'},
                'description': 'A dictionary of filter values.',
            },
        },
    }
    result.get('components').get('schemas')['BulkDeleteRequest'] = schema_def

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
