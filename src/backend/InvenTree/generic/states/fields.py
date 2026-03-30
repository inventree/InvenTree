"""Custom model/serializer fields for InvenTree models that support custom states."""

from collections.abc import Iterable
from typing import Any, Optional

from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.utils.encoding import force_str
from django.utils.translation import gettext_lazy as _

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers
from rest_framework.fields import ChoiceField

import InvenTree.ready

from .custom import get_logical_value


class CustomChoiceField(serializers.ChoiceField):
    """Custom Choice Field.

    This is not intended to be used directly.
    """

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
        self.is_custom = is_custom

    def to_internal_value(self, data):
        """Map the choice (that might be a custom one) back to the logical value."""
        try:
            return super().to_internal_value(data)
        except serializers.ValidationError:
            try:
                logical = get_logical_value(data, self.choice_mdl._meta.model_name)
                if self.is_custom:
                    return logical.key
                return logical.logical_key
            except (ObjectDoesNotExist, Exception):
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


@extend_schema_field(OpenApiTypes.INT)
class ExtraCustomChoiceField(CustomChoiceField):
    """Custom Choice Field that returns value of status if empty.

    This is not intended to be used directly.
    """

    def to_representation(self, value):
        """Return the value of the status if it is empty."""
        return super().to_representation(value) or value


class InvenTreeCustomStatusModelField(models.PositiveIntegerField):
    """Custom model field for extendable status codes.

    Adds a secondary *_custom_key field to the model which can be used to store additional status information.
    Models using this model field must also include the InvenTreeCustomStatusSerializerMixin in all serializers that create or update the value.
    """

    def __init__(self, *args, **kwargs):
        """Initialize the field."""
        from generic.states.validators import CustomStatusCodeValidator

        self.status_class = kwargs.pop('status_class', None)

        validators = kwargs.pop('validators', None) or []

        if self.status_class:
            validators.append(CustomStatusCodeValidator(status_class=self.status_class))

        kwargs['validators'] = validators
        super().__init__(*args, **kwargs)

    def deconstruct(self):
        """Deconstruct the field for migrations."""
        name, path, args, kwargs = super().deconstruct()

        return name, path, args, kwargs

    def contribute_to_class(self, cls, name):
        """Add the _custom_key field to the model."""
        cls._meta.supports_custom_status = True

        if not hasattr(self, '_custom_key_field') and not hasattr(
            cls, f'{name}_custom_key'
        ):
            self.add_field(cls, name)

        super().contribute_to_class(cls, name)

    def clean(self, value: Any, model_instance: Any) -> Any:
        """Ensure that the value is not an empty string."""
        if value == '':
            value = None

        return super().clean(value, model_instance)

    def add_field(self, cls, name):
        """Adds custom_key_field to the model class to save additional status information."""
        from generic.states.validators import CustomStatusCodeValidator

        validators = []

        if self.status_class:
            validators.append(CustomStatusCodeValidator(status_class=self.status_class))

        help_text = _('Additional status information for this item')
        if InvenTree.ready.isGeneratingSchema() and self.status_class:
            help_text = (
                help_text
                + '\n\n'
                + '\n'.join(
                    f'* `{value}` - {label}'
                    for value, label in self.status_class.items(custom=True)
                )
                + "\n\nAdditional custom status keys may be retrieved from the corresponding 'status_retrieve' call."
            )

        custom_key_field = ExtraInvenTreeCustomStatusModelField(
            default=None,
            verbose_name=_('Custom status key'),
            help_text=help_text,
            validators=validators,
            blank=True,
            null=True,
        )

        cls.add_to_class(f'{name}_custom_key', custom_key_field)
        self._custom_key_field = custom_key_field


class ExtraInvenTreeCustomStatusModelField(models.PositiveIntegerField):
    """Custom field used to detect custom extenteded fields.

    This is not intended to be used directly, if you want to support custom states in your model use InvenTreeCustomStatusModelField.
    """

    def __init__(self, *args, **kwargs):
        """Initialize the field."""
        super().__init__(*args, **kwargs)


class InvenTreeCustomStatusSerializerMixin:
    """Mixin to ensure custom status fields are set.

    This mixin must be used to ensure that custom status fields are set correctly when updating a model.
    """

    _custom_fields: Optional[list] = None
    _custom_fields_leader: Optional[list] = None
    _custom_fields_follower: Optional[list] = None
    _is_gathering = False

    def update(self, instance, validated_data):
        """Ensure the custom field is updated if the leader was changed."""
        self.gather_custom_fields()
        # Mirror values from leader to follower
        for field in self._custom_fields_leader:
            follower_field_name = f'{field}_custom_key'
            if (
                field in self.initial_data
                and self.instance
                and self.initial_data[field]
                != getattr(self.instance, follower_field_name, None)
            ):
                setattr(self.instance, follower_field_name, self.initial_data[field])

        # Mirror values from follower to leader
        for field in self._custom_fields_follower:
            leader_field_name = field.replace('_custom_key', '')
            if field in validated_data and leader_field_name not in self.initial_data:
                try:
                    reference = get_logical_value(
                        validated_data[field],
                        self.fields[field].choice_mdl._meta.model_name,
                    )
                    validated_data[leader_field_name] = reference.logical_key
                except (ObjectDoesNotExist, Exception):
                    if validated_data[field] in self.fields[leader_field_name].choices:
                        validated_data[leader_field_name] = validated_data[field]
                    else:
                        raise serializers.ValidationError('Invalid choice')
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        """Ensure custom state fields are not served empty."""
        data = super().to_representation(instance)
        for field in self.gather_custom_fields():
            if data[field] is None:
                data[field] = data[
                    field.replace('_custom_key', '')
                ]  # Use "normal" status field instead
        return data

    def gather_custom_fields(self):
        """Gather all custom fields on the serializer."""
        if self._custom_fields_follower:
            self._is_gathering = False
            return self._custom_fields_follower

        if self._is_gathering:
            self._custom_fields = {}
        else:
            self._is_gathering = True
            # Gather fields
            self._custom_fields = {
                k: v.is_custom
                for k, v in self.fields.items()
                if isinstance(v, CustomChoiceField)
            }

        # Separate fields for easier/cheaper access
        self._custom_fields_follower = [k for k, v in self._custom_fields.items() if v]
        self._custom_fields_leader = [
            k for k, v in self._custom_fields.items() if not v
        ]

        return self._custom_fields_follower

    def build_standard_field(self, field_name, model_field):
        """Use custom field for custom status model.

        This is required because of DRF overwriting all fields with choice sets.
        """
        field_cls, field_kwargs = super().build_standard_field(field_name, model_field)
        if issubclass(field_cls, ChoiceField) and isinstance(
            model_field, InvenTreeCustomStatusModelField
        ):
            field_cls = CustomChoiceField
            field_kwargs['choice_mdl'] = model_field.model
            field_kwargs['choice_field'] = model_field.name
        elif isinstance(model_field, ExtraInvenTreeCustomStatusModelField):
            field_cls = ExtraCustomChoiceField
            field_kwargs['choice_mdl'] = model_field.model
            field_kwargs['choice_field'] = model_field.name
            field_kwargs['is_custom'] = True

            # Inherit choices from leader
            self.gather_custom_fields()
            if field_name in self._custom_fields:
                leader_field_name = field_name.replace('_custom_key', '')
                leader_field = self.fields[leader_field_name]
                if hasattr(leader_field, 'choices'):
                    field_kwargs['choices'] = list(leader_field.choices.items())
                elif hasattr(model_field.model, leader_field_name):
                    leader_model_field = getattr(
                        model_field.model, leader_field_name
                    ).field
                    if hasattr(leader_model_field, 'choices'):
                        field_kwargs['choices'] = leader_model_field.choices

                if getattr(leader_field, 'read_only', False) is True:
                    field_kwargs['read_only'] = True

            if 'choices' not in field_kwargs:
                field_kwargs['choices'] = []

        return field_cls, field_kwargs
