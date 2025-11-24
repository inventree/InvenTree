"""Custom API filters for InvenTree."""


def filter_content_type(
    queryset, field_name: str, content_type: str | int | None, allow_null: bool = True
):
    """Filter a queryset by content type.

    Arguments:
        queryset: The queryset to filter.
        field_name: The name of the content type field within the current model context.
        content_type: The content type to filter by (name or ID).
        allow_null: If True, include entries with null content type.

    Returns:
        Filtered queryset.
    """
    if content_type is None:
        return queryset

    from django.contrib.contenttypes.models import ContentType
    from django.db.models import Q

    ct = None

    # First, try to resolve the content type via a PK value
    try:
        content_type_id = int(content_type)
        ct = ContentType.objects.get_for_id(content_type_id)
    except (ValueError, ContentType.DoesNotExist):
        ct = None

    if len(content_type.split('.')) == 2:
        # Next, try to resolve the content type via app_label.model_name
        try:
            app_label, model = content_type.split('.')
            ct = ContentType.objects.get(app_label=app_label, model=model)
        except ContentType.DoesNotExist:
            ct = None

    else:
        # Next, try to resolve the content type via a model name
        ct = ContentType.objects.filter(model__iexact=content_type).first()

    if ct is None:
        raise ValueError(f'Invalid content type: {content_type}')

    q = Q(**{f'{field_name}': ct})

    if allow_null:
        q |= Q(**{f'{field_name}__isnull': True})

    return queryset.filter(q)
