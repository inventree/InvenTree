"""Custom API filters for InvenTree."""

import re

from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.db.models.query import QuerySet

import InvenTree.conversion
import InvenTree.helpers


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


"""A list of valid operators for filtering part parameters."""
PARAMETER_FILTER_OPERATORS: list[str] = ['gt', 'gte', 'lt', 'lte', 'ne', 'icontains']


def filter_parameters_by_value(
    queryset: QuerySet, template_id: int, value: str, func: str = ''
) -> QuerySet:
    """Filter the Parameter model based on the provided template and value.

    Arguments:
        queryset: The initial QuerySet to filter.
        template_id: The parameter template ID to filter by.
        value: The value to filter against.
        func: The filtering function to apply (e.g. 'gt', 'lt', etc).

    Returns:
        A list of Parameter instances which match the given criteria.

    Notes:
    - Parts which do not have a value for the given parameter are excluded.
    """
    from common.models import ParameterTemplate

    # Ensure that the provided function is valid
    if func and func not in PARAMETER_FILTER_OPERATORS:
        raise ValueError(f'Invalid parameter filter function: {func}')

    # Ensure that the template exists
    try:
        template = ParameterTemplate.objects.get(pk=template_id)
    except ParameterTemplate.DoesNotExist:
        raise ValueError(f'Invalid parameter template ID: {template_id}')

    # Construct a "numeric" value for the filter
    try:
        value_numeric = float(value)
    except (ValueError, TypeError):
        value_numeric = None

    if template.checkbox:
        # Account for 'boolean' parameter values
        bool_value = InvenTree.helpers.str2bool(value)
        value_numeric = 1 if bool_value else 0
        value = str(bool_value)

        # Boolean filtering is limited to exact matches
        func = ''

    elif value_numeric is None and template.units:
        # Convert the raw value to the units of the template parameter
        try:
            value_numeric = InvenTree.conversion.convert_physical_value(
                value, template.units
            )
        except Exception:
            # The value cannot be converted - return an empty queryset
            return queryset.none()

    # Special handling for the "not equal" operator
    if func == 'ne':
        invert = True
        func = ''
    else:
        invert = False

    # Some filters are only applicable to string values
    text_only = any([func in ['icontains'], value_numeric is None])

    # Ensure the function starts with a double underscore
    if func and not func.startswith('__'):
        func = f'__{func}'

    # Query for 'numeric' value - this has priority over 'string' value
    data_numeric = {
        'parameters_list__template': template,
        'parameters_list__data_numeric__isnull': False,
        f'parameters_list__data_numeric{func}': value_numeric,
    }

    query_numeric = Q(**data_numeric)

    # Query for 'string' value
    data_text = {
        'parameters_list__template': template,
        f'parameters_list__data{func}': str(value),
    }

    if not text_only:
        data_text['parameters_list__data_numeric__isnull'] = True

    query_text = Q(**data_text)

    # Combine the queries based on whether we are filtering by text or numeric value
    q = query_text if text_only else query_text | query_numeric

    # queryset = Parameter.objects.prefetch_related('template').all()

    # Special handling for the '__ne' (not equal) operator
    # In this case, we want the *opposite* of the above queries
    if invert:
        return queryset.exclude(q).distinct()
    else:
        return queryset.filter(q).distinct()


def filter_parametric_data(queryset: QuerySet, parameters: dict[str, str]) -> QuerySet:
    """Filter the provided queryset by parametric data.

    Arguments:
        queryset: The initial queryset to filter.
        parameters: A dictionary of parameter filters to apply.

    Returns:
        Filtered queryset.

    Used to filter returned parts based on their parameter values.

    To filter based on parameter value, supply query parameters like:
    - parameter_<x>=<value>
    - parameter_<x>_gt=<value>
    - parameter_<x>_lte=<value>

    where:
        - <x> is the ID of the PartParameterTemplate.
        - <value> is the value to filter against.

    Typically these filters would be provided against via an API request.
    """
    queryset = queryset.prefetch_related('parameters_list', 'parameters_list__template')

    # Allowed lookup operations for parameter values
    operators = '|'.join(PARAMETER_FILTER_OPERATORS)

    regex_pattern = rf'^parameter_(\d+)(_({operators}))?$'

    for param, value in parameters.items():
        result = re.match(regex_pattern, param)
        if not result:
            continue

        template_id = result.group(1)
        operator = result.group(3) or ''

        queryset = filter_parameters_by_value(
            queryset, template_id, value, func=operator
        )

    return queryset
