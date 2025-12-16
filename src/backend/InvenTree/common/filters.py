"""Custom API filters for InvenTree."""

import re

from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db.models import (
    Case,
    CharField,
    Exists,
    FloatField,
    Model,
    OuterRef,
    Q,
    Subquery,
    Value,
    When,
)
from django.db.models.query import QuerySet
from django.utils.translation import gettext_lazy as _

import InvenTree.conversion
import InvenTree.helpers
import InvenTree.serializers


def determine_content_type(content_type: str | int | None) -> ContentType | None:
    """Determine a ContentType instance from a string or integer input.

    Arguments:
        content_type: The content type to resolve (name or ID).

    Returns:
        ContentType instance if found, else None.
    """
    if content_type is None:
        return None

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

    return ct


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

    ct = determine_content_type(content_type)

    if ct is None:
        raise ValidationError(f'Invalid content type: {content_type}')

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
        - <x> is the ID of the ParameterTemplate.
        - <value> is the value to filter against.

    Typically these filters would be provided against via an API request.
    """
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


def order_by_parameter(
    queryset: QuerySet, model_type: Model, ordering: str | None
) -> QuerySet:
    """Order the provided queryset by a parameter value.

    Arguments:
        queryset: The initial queryset to order.
        model_type: The model type of the items in the queryset.
        ordering: The ordering string provided by the user.

    Returns:
        Ordered queryset.

    Used to order returned parts based on their parameter values.

    To order based on parameter value, supply an ordering string like:
    - parameter_<x>
    - -parameter_<x>

    where:
        - <x> is the ID of the ParameterTemplate.
        - A leading '-' indicates descending order.
    """
    import common.models

    if not ordering:
        # No ordering provided - return the original queryset
        return queryset

    result = re.match(r'^-?parameter_(\d+)$', ordering)

    if not result:
        # Ordering does not match the expected pattern - return the original queryset
        return queryset

    template_id = result.group(1)
    ascending = not ordering.startswith('-')

    template_exists_filter = common.models.Parameter.objects.filter(
        template__id=template_id,
        model_type=ContentType.objects.get_for_model(model_type),
        model_id=OuterRef('id'),
    )

    queryset = queryset.annotate(parameter_exists=Exists(template_exists_filter))

    # Annotate the queryset with the parameter value for the provided template
    queryset = queryset.annotate(
        parameter_value=Case(
            When(
                parameter_exists=True,
                then=Subquery(
                    template_exists_filter.values('data')[:1], output_field=CharField()
                ),
            ),
            default=Value('', output_field=CharField()),
        ),
        parameter_value_numeric=Case(
            When(
                parameter_exists=True,
                then=Subquery(
                    template_exists_filter.values('data_numeric')[:1],
                    output_field=FloatField(),
                ),
            ),
            default=Value(0, output_field=FloatField()),
        ),
    )

    prefix = '' if ascending else '-'

    return queryset.order_by(
        '-parameter_exists',
        f'{prefix}parameter_value_numeric',
        f'{prefix}parameter_value',
    )


def enable_project_code_filter(default: bool = True):
    """Add an optional 'project_code_detail' field to an API serializer.

    Arguments:
        filter_name: The name of the filter field.
        default: If True, enable the filter by default.

    If applied, this field will automatically prefetch the 'project_code' relationship.
    """
    from common.serializers import ProjectCodeSerializer

    return InvenTree.serializers.enable_filter(
        ProjectCodeSerializer(
            source='project_code', many=False, read_only=True, allow_null=True
        ),
        default,
        filter_name='project_code_detail',
        prefetch_fields=['project_code'],
    )


def enable_project_label_filter(default: bool = True):
    """Add an optional 'project_code_label' field to an API serializer.

    Arguments:
        filter_name: The name of the filter field.
        default: If True, enable the filter by default.

    If applied, this field will automatically prefetch the 'project_code' relationship.
    """
    return InvenTree.serializers.enable_filter(
        InvenTree.serializers.FilterableCharField(
            source='project_code.code',
            read_only=True,
            label=_('Project Code Label'),
            allow_null=True,
        ),
        default,
        filter_name='project_code_detail',
        prefetch_fields=['project_code'],
    )


def enable_parameters_filter():
    """Add an optional 'parameters' field to an API serializer.

    Arguments:
        source: The source field for the serializer.
        filter_name: The name of the filter field.
        default: If True, enable the filter by default.

    If applied, this field will automatically annotate the queryset with parameter data.
    """
    from common.serializers import ParameterSerializer

    return InvenTree.serializers.enable_filter(
        ParameterSerializer(many=True, read_only=True, allow_null=True),
        False,
        filter_name='parameters',
        prefetch_fields=[
            'parameters_list',
            'parameters_list__model_type',
            'parameters_list__updated_by',
            'parameters_list__template',
        ],
    )


def enable_tags_filter(default: bool = False):
    """Add an optional 'tags' field to an API serializer.

    Arguments:
        default: If True, enable the filter by default.

    If applied, this field will automatically prefetch the 'tags' relationship.
    """
    from InvenTree.serializers import FilterableTagListField

    return InvenTree.serializers.enable_filter(
        FilterableTagListField(required=False),
        default,
        filter_name='tags',
        prefetch_fields=['tags', 'tagged_items', 'tagged_items__tag'],
    )
