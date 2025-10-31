"""Validation helpers for common models."""

import re
from typing import Union

from django.core.exceptions import ValidationError
from django.db.models import Model
from django.utils.translation import gettext_lazy as _

import common.icons
from common.settings import get_global_setting


def get_mixin_models(mixin_class: type[Model]):
    """Return a list of Django model classes that inherit from the given mixin.

    This function lazily imports the helper to avoid circular imports.

    Args:
        mixin_class: The mixin class to search for.

    Returns:
        A list of Django model classes that subclass the provided mixin.
    """
    # Lazy import to prevent circular dependency issues
    import InvenTree.helpers_model

    return list(InvenTree.helpers_model.getModelsWithMixin(mixin_class))


def get_model_options_for_mixin(mixin_class: type[Model]):
    """Build choice options for all models that inherit from a given mixin.

    Each option is a tuple of:
    - key: the lowercase model class name (e.g. 'part', 'stockitem')
    - label: the model's verbose name for display

    Args:
        mixin_class: The mixin class used to filter models.

    Returns:
        A list of (key, label) tuples suitable for form field choices.
    """
    options = []
    for model in get_mixin_models(mixin_class):
        key = model.__name__.lower()
        label = str(model._meta.verbose_name)
        options.append((key, label))
    return options


def attachment_model_options():
    """Return a list of valid attachment model choices."""
    import InvenTree.models

    return get_model_options_for_mixin(InvenTree.models.InvenTreeAttachmentMixin)


def resolve_model_from_label(label: str, mixin_class: type[Model]):
    """Resolve a model class by a case-insensitive label among models inheriting a mixin.

    Args:
        label: The identifier string to match (typically the model class name in lowercase).
        mixin_class: The mixin class that candidate models must inherit from.

    Returns:
        The Django model class that matches the provided label.
    """
    if not label:
        raise ValidationError(_('No attachment model type provided'))

    label_lc = label.lower()

    for model in get_mixin_models(mixin_class):
        if model.__name__.lower() == label_lc:
            return model

    raise ValidationError(_('Invalid attachment model type') + f": '{label}'")


def validate_attachment_model_type(value):
    """Ensure that the provided attachment model is valid."""
    import InvenTree.models

    model_names = [
        el[0]
        for el in get_model_options_for_mixin(InvenTree.models.InvenTreeAttachmentMixin)
    ]
    if value not in model_names:
        raise ValidationError('Model type does not support attachments')


def validate_notes_model_type(value):
    """Ensure that the provided model type is valid.

    The provided value must map to a model which implements the 'InvenTreeNotesMixin'.
    """
    import InvenTree.helpers_model
    import InvenTree.models

    if not value:
        # Empty values are allowed
        return

    model_types = list(
        InvenTree.helpers_model.getModelsWithMixin(InvenTree.models.InvenTreeNotesMixin)
    )

    model_names = [model.__name__.lower() for model in model_types]

    if value.lower() not in model_names:
        raise ValidationError(f"Invalid model type '{value}'")


def limit_image_content_types():
    """Limit the content types for image uploads to those supported by InvenTreeImageMixin."""
    import InvenTree.models

    allowed_models = [
        m[0] for m in get_model_options_for_mixin(InvenTree.models.InvenTreeImageMixin)
    ]

    return {'model__in': allowed_models}


def validate_decimal_places_min(value):
    """Validator for PRICING_DECIMAL_PLACES_MIN setting."""
    try:
        value = int(value)
        places_max = int(get_global_setting('PRICING_DECIMAL_PLACES', create=False))
    except Exception:
        return

    if value > places_max:
        raise ValidationError(_('Minimum places cannot be greater than maximum places'))


def validate_decimal_places_max(value):
    """Validator for PRICING_DECIMAL_PLACES_MAX setting."""
    try:
        value = int(value)
        places_min = int(get_global_setting('PRICING_DECIMAL_PLACES_MIN', create=False))
    except Exception:
        return

    if value < places_min:
        raise ValidationError(_('Maximum places cannot be less than minimum places'))


def validate_email_domains(setting):
    """Validate the email domains setting."""
    if not setting.value:
        return

    domains = setting.value.split(',')
    for domain in domains:
        if not domain:
            raise ValidationError(_('An empty domain is not allowed.'))
        if not re.match(r'^@[a-zA-Z0-9\.\-_]+$', domain):
            raise ValidationError(_(f'Invalid domain name: {domain}'))


def validate_icon(name: Union[str, None]):
    """Validate the provided icon name, and ignore if empty."""
    if name == '' or name is None:
        return

    common.icons.validate_icon(name)


def validate_uppercase(value: str):
    """Ensure that the provided value is uppercase."""
    value = str(value)

    if value != value.upper():
        raise ValidationError(_('Value must be uppercase'))


def validate_variable_string(value: str):
    """The passed value must be a valid variable identifier string."""
    if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', value):
        raise ValidationError(_('Value must be a valid variable identifier'))
