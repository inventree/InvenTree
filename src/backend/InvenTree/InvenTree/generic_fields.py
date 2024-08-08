"""Custom model/serializer fields for InvenTree models that support custom states."""

from typing import Any, Iterable

from django.db import models
from django.utils.encoding import force_str
from django.utils.translation import gettext_lazy as _

from rest_framework import serializers


class CustomChoiceField(serializers.ChoiceField):
    """Custom Choice Field."""

    def __init__(self, choices: Iterable, **kwargs):
        """Initialize the field."""
        choice_mdl = kwargs.pop('choice_mdl', None)
        choice_field = kwargs.pop('choice_field', None)
        is_custom = kwargs.pop('is_custom', False)
        kwargs.pop('max_value', None)
        kwargs.pop('min_value', None)
        super().__init__(choices, **kwargs)
        self.choice_mdl = choice_mdl
        self.choice_field = choice_field
        self.is_is_custom = is_custom

    def get_logical_value(self, value):
        """Get the state model for the selected value."""
        from common.models import InvenTreeCustomUserStateModel

        return InvenTreeCustomUserStateModel.objects.get(
            key=value, model__model=self.choice_mdl._meta.model_name
        )

    def to_internal_value(self, data):
        """Map the choice (that might be a custom one) back to the logical value."""
        try:
            return super().to_internal_value(data)
        except serializers.ValidationError:
            from common.models import InvenTreeCustomUserStateModel

            try:
                logical = self.get_logical_value(data)
                if self.is_is_custom:
                    return logical.key
                return logical.logical_key
            except InvenTreeCustomUserStateModel.DoesNotExist:
                raise serializers.ValidationError('Invalid choice')

    def get_field_info(self, field, field_info):
        """Return the field information for the given item."""
        from common.models import InvenTreeCustomUserStateModel

        # Static choices
        choices = [
            {
                'value': choice_value,
                'display_name': force_str(choice_name, strings_only=True),
            }
            for choice_value, choice_name in field.choices.items()
        ]
        # Dynamic choices from InvenTreeCustomUserStateModel
        objs = InvenTreeCustomUserStateModel.objects.filter(
            model__model=field.choice_mdl._meta.model_name
        )
        dyn_choices = [
            {'value': choice.key, 'display_name': choice.label} for choice in objs.all()
        ]

        if dyn_choices:
            all_choices = choices + dyn_choices
            field_info['choices'] = sorted(all_choices, key=lambda kv: kv['value'])
        else:
            field_info['choices'] = choices
        return field_info


class InvenTreeCustomStatusExtraModelField(models.PositiveIntegerField):
    """Cusotm field used to detect custom extenteded fields."""


class InvenTreeCustomStatusModelField(models.PositiveIntegerField):
    """Custom model field for extendable status codes.

    Adds a secondary _custom_key field to the model which can be used to store additional status information.
    """

    def deconstruct(self):
        """Deconstruct the field for migrations."""
        name, path, args, kwargs = super().deconstruct()

        return name, path, args, kwargs

    def contribute_to_class(self, cls, name):
        """Add the _custom_key field to the model."""
        cls._meta.supports_custom_status = True

        if not hasattr(self, '_custom_key_field'):
            self.add_field(cls, name)

        super().contribute_to_class(cls, name)

    def clean(self, value: Any, model_instance: Any) -> Any:
        """Ensure that the value is not an empty string."""
        if value == '':
            value = None
        return super().clean(value, model_instance)

    def add_field(self, cls, name):
        """Adds custom_key_field to the model class to save additional status information."""
        custom_key_field = InvenTreeCustomStatusExtraModelField(
            default=None,
            verbose_name=_('Custom status key'),
            help_text=_('Additional status information for this item'),
            blank=True,
            null=True,
        )
        cls.add_to_class(f'{name}_custom_key', custom_key_field)
        self._custom_key_field = custom_key_field


class ExtraCustomChoiceField(CustomChoiceField):
    """Custom Choice Field that returns value of status if empty."""

    def to_representation(self, value):
        """Return the value of the status if it is empty."""
        return super().to_representation(value) or value
