"""Schema processing functions for cleaning up generated schema."""


def postprocess_conditionally_removed(result, generator, request, public):
    """Un-require conditionally-removed objects.

    Read-only values are all marked as required but some are conditionally removed depending on the view and therefore must not be required.
    """
    # Alpha-sorted list of the fields that are conditionally removed within serializers
    conditionally_removed = [
        'availability_updated',
        'available',
        'build_detail',
        'category_detail',
        'category_path',
        'create_child_builds',
        'customer_detail',
        'default_location_detail',
        'item_detail',
        'location_detail',
        'location_path',
        'manufacturer_detail',
        'manufacturer_part_detail',
        'notes',
        'on_order',
        'order_detail',
        'parameters',
        'part_detail',
        'path',
        'permissions',
        'pretty_name',
        'pricing_max',
        'pricing_max_total',
        'pricing_min',
        'pricing_min_total',
        'pricing_updated',
        'stock_item_detail',
        'sub_part_detail',
        'substitutes',
        'supplier_detail',
        'supplier_part_detail',
        'tags',
        'template_detail',
        'tests',
        'user_detail',
    ]

    # Process schema section
    schemas = result.get('components', {}).get('schemas', {})
    for schema in schemas.values():
        required_fields = schema.get('required', [])
        for to_remove in conditionally_removed:
            if to_remove in required_fields:
                required_fields.remove(to_remove)
        if 'required' in schema and len(required_fields) == 0:
            schema.pop('required')

    return result
