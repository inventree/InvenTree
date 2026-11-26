"""Validators for part app."""

import re

from django.core.exceptions import FieldDoesNotExist, ValidationError
from django.utils.translation import gettext_lazy as _

from jinja2.sandbox import SandboxedEnvironment


def validate_ipn_regex(value):
    """Validate that the PART_IPN_REGEX setting is a valid regular expression.

    An empty value is allowed (and disables IPN pattern matching).
    """
    pattern = str(value or '').strip()

    if not pattern:
        return

    try:
        re.compile(pattern)
    except re.error as exc:
        raise ValidationError({
            'value': _('Invalid regular expression: {error}').format(error=exc)
        })


def validate_part_name_format(value):
    """Validate part name format.

    Make sure that each template container has a field of Part Model
    """
    # Make sure that the field_name exists in Part model
    from part.models import Part

    jinja_template_regex = re.compile(r'{{.*?}}')
    field_name_regex = re.compile(r'(?<=part\.)[A-z]+')

    for jinja_template in jinja_template_regex.findall(str(value)):
        # make sure at least one and only one field is present inside the parser
        field_names = field_name_regex.findall(jinja_template)
        if len(field_names) < 1:
            raise ValidationError({
                'value': 'At least one field must be present inside a jinja template container i.e {{}}'
            })

        for field_name in field_names:
            try:
                Part._meta.get_field(field_name)
            except FieldDoesNotExist:
                raise ValidationError({
                    'value': f'{field_name} does not exist in Part Model'
                })

    # Attempt to render the template with a dummy Part instance
    # Use pk=1 to ensure conditional checks like {% if part.pk %} are evaluated
    p = Part(pk=1, name='test part', description='some test part')

    try:
        SandboxedEnvironment().from_string(value).render({'part': p})
    except Exception as exc:
        raise ValidationError({'value': str(exc)})

    return True
