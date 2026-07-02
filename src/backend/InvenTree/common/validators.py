"""Validation helpers for common models."""

import re

from django.core.exceptions import SuspiciousFileOperation, ValidationError
from django.core.files.storage import default_storage
from django.utils import translation
from django.utils.translation import gettext_lazy as _

import common.icons
from common.settings import get_global_setting


def note_model_types():
    """Return a list of valid note model choices."""
    import InvenTree.models

    return list(
        InvenTree.helpers_model.getModelsWithMixin(InvenTree.models.InvenTreeNoteMixin)
    )


def note_model_options():
    """Return a list of options for models which support notes."""
    return [
        (model.__name__.lower(), model._meta.verbose_name)
        for model in note_model_types()
    ]


def parameter_model_types():
    """Return a list of valid parameter model choices."""
    import InvenTree.models

    return list(
        InvenTree.helpers_model.getModelsWithMixin(
            InvenTree.models.InvenTreeParameterMixin
        )
    )


def parameter_model_options():
    """Return a list of options for models which support parameters."""
    return [
        (model.__name__.lower(), model._meta.verbose_name)
        for model in parameter_model_types()
    ]


def parameter_template_model_options():
    """Return a list of options for models which support parameter templates."""
    options = [
        (model.__name__.lower(), model._meta.verbose_name)
        for model in parameter_model_types()
    ]

    return [(None, _('All models')), *options]


def attachment_model_types():
    """Return a list of valid attachment model choices."""
    import InvenTree.models

    return list(
        InvenTree.helpers_model.getModelsWithMixin(
            InvenTree.models.InvenTreeAttachmentMixin
        )
    )


def attachment_model_options():
    """Return a list of options for models which support attachments."""
    return [
        (model.__name__.lower(), model._meta.verbose_name)
        for model in attachment_model_types()
    ]


def attachment_model_class_from_label(label: str):
    """Return the model class for the given label."""
    if not label:
        raise ValidationError(_('No attachment model type provided'))

    for model in attachment_model_types():
        if model.__name__.lower() == label.lower():
            return model

    raise ValidationError(_('Invalid attachment model type') + f": '{label}'")


def validate_attachment_model_type(value):
    """Ensure that the provided attachment model is valid."""
    model_names = [el[0] for el in attachment_model_options()]
    if value not in model_names:
        raise ValidationError('Model type does not support attachments')


def validate_attachment_file(attachment):
    """Ensure that the provided attachment file is valid."""
    max_size = get_global_setting('INVENTREE_UPLOAD_MAX_SIZE', create=False)

    if attachment.size > (max_size * 1024 * 1024):
        raise ValidationError(
            _(f'File size exceeds maximum upload limit of {max_size} MB')
        )

    try:
        default_storage.generate_filename(attachment.name)
    except SuspiciousFileOperation:  # pragma: no cover
        raise ValidationError(_('Invalid file name'))


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


def validate_icon(name: str | None):
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


def validate_locale(value: str):
    """Validate that the provided value is a valid locale string."""
    from babel import Locale
    from babel.core import UnknownLocaleError

    if not value:
        return

    try:
        Locale.parse(translation.to_locale(value))
    except (UnknownLocaleError, ValueError) as e:
        raise ValidationError(f"Invalid locale value: '{value}' - {e}")
