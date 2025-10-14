"""Serializers used in various InvenTree apps."""

import os
from collections import OrderedDict
from copy import deepcopy
from decimal import Decimal
from typing import Optional

from django.conf import settings
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from djmoney.contrib.django_rest_framework.fields import MoneyField
from djmoney.money import Money
from djmoney.utils import MONEY_CLASSES, get_currency_field_name
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.fields import empty
from rest_framework.mixins import ListModelMixin
from rest_framework.serializers import DecimalField
from rest_framework.utils import model_meta
from taggit.serializers import TaggitSerializer

import common.models as common_models
import InvenTree.ready
from common.currency import currency_code_default, currency_code_mappings
from InvenTree.fields import InvenTreeRestURLField, InvenTreeURLField
from InvenTree.helpers import str2bool


# region path filtering
class OptFilter:
    """Filter for serializer or field."""

    is_filterable = None
    is_filterable_vals = {}

    def __init__(self, *args, **kwargs):
        """Initialize the serializer."""
        if self.is_filterable is None:  # Materialize parameters for later usage
            self.is_filterable = kwargs.pop('is_filterable', None)
            self.is_filterable_vals = kwargs.pop('is_filterable_vals', {})
        super().__init__(*args, **kwargs)


class PathScopedMixin:
    """Mixin to disable a serializer field based on kwargs passed to the view."""

    _was_filtered = False

    def __init__(self, *args, **kwargs):
        """Initialization routine for the serializer."""
        self.gather_filters(kwargs)
        super().__init__(*args, **kwargs)
        self.do_filtering(*args, **kwargs)

    def gather_filters(self, kwargs):
        """Gather filterable fields."""
        if getattr(self, '_was_filtered', False) or not hasattr(self, 'fields'):
            return kwargs
        self._was_filtered = True

        # Actually gather the filterable fields
        fields = self.fields.items()
        self.filter_targets = {
            k: {'serializer': a, **getattr(a, 'is_filterable_vals', {})}
            for k, a in fields
            if getattr(a, 'is_filterable', None)
        }

        # Remove filter args from kwargs to avoid issues with super().__init__
        poped_kwargs = {}  # store popped kwargs as a arg might be reused for multiple fields
        tgs_vals = {}
        for k, v in self.filter_targets.items():
            pop_ref = v['name'] or k
            val = kwargs.pop(pop_ref, poped_kwargs.get(pop_ref))
            if val:
                poped_kwargs[pop_ref] = val
            tgs_vals[k] = str2bool(val) if isinstance(val, str) else val
        self.filter_target_values = tgs_vals

        if len(self.filter_targets) == 0:
            raise Exception(
                'INVE-W999: No filter targets found in fields, remove `PathScopedMixin`'
            )

        return kwargs

    def do_filtering(self, *args, **kwargs):
        """Do the actual filtering."""
        if not hasattr(self, 'filter_target_values'):
            return

        # Throw out fields which are not requested
        for k, v in self.filter_target_values.items():
            value = v if v is not None else self.filter_targets[k]['default']
            if value is not True:
                self.fields.pop(k, None)


# Decorator for marking serialzier fields that can be filtered out
def can_filter(func, default=False, name: Optional[str] = None):
    """Decorator for marking serializer fields as filterable."""
    # Ensure this function can be actually filteres
    if not issubclass(func.__class__, OptFilter):
        raise TypeError(
            'INVE-W999: `can_filter` can only be applied to serializers that contain `OptFilter` mixin!'
        )

    # Mark the function as filterable
    func._kwargs['is_filterable'] = True
    func._kwargs['is_filterable_vals'] = {
        'default': default,
        'name': name if name else func.field_name,
    }
    return func


class FilterableListSerializer(OptFilter, PathScopedMixin, serializers.ListSerializer):
    """Custom ListSerializer which allows filtering of fields."""


class CfListField(OptFilter, serializers.ListField):
    """Custom ListField which allows filtering."""


class CfSerializerMethodField(OptFilter, serializers.SerializerMethodField):
    """Custom SerializerMethodField which allows filtering."""


class CfDateTimeField(OptFilter, serializers.DateTimeField):
    """Custom DateTimeField which allows filtering."""


class CfFloatField(OptFilter, serializers.FloatField):
    """Custom FloatField which allows filtering."""


class CfCharField(OptFilter, serializers.CharField):
    """Custom CharField which allows filtering."""


class CfIntegerField(OptFilter, serializers.IntegerField):
    """Custom IntegerField which allows filtering."""


# endregion


class EmptySerializer(serializers.Serializer):
    """Empty serializer for use in testing."""


class InvenTreeMoneySerializer(OptFilter, MoneyField):
    """Custom serializer for 'MoneyField', which ensures that passed values are numerically valid.

    Ref: https://github.com/django-money/django-money/blob/master/djmoney/contrib/django_rest_framework/fields.py
    """

    def __init__(self, *args, **kwargs):
        """Override default values."""
        kwargs['max_digits'] = kwargs.get('max_digits', 19)
        self.decimal_places = kwargs['decimal_places'] = kwargs.get('decimal_places', 6)
        kwargs['required'] = kwargs.get('required', False)

        super().__init__(*args, **kwargs)

    def to_representation(self, obj):
        """Convert the Money object to a decimal value for representation."""
        val = super().to_representation(obj)

        return float(val)

    def get_value(self, data):
        """Test that the returned amount is a valid Decimal."""
        amount = super(DecimalField, self).get_value(data)

        # Convert an empty string to None
        if len(str(amount).strip()) == 0:
            amount = None

        try:
            if amount is not None and amount is not empty:
                # Convert to a Decimal instance, and round to maximum allowed decimal places
                amount = Decimal(amount)
                amount = round(amount, self.decimal_places)
        except Exception:
            raise ValidationError({self.field_name: [_('Must be a valid number')]})

        currency = data.get(
            get_currency_field_name(self.field_name), self.default_currency
        )

        if (
            currency
            and amount is not None
            and not isinstance(amount, MONEY_CLASSES)
            and amount is not empty
        ):
            return Money(amount, currency)

        try:
            fp_amount = float(amount)
            return fp_amount
        except Exception:
            return amount


@extend_schema_field(serializers.CharField())
class InvenTreeCurrencySerializer(serializers.ChoiceField):
    """Custom serializers for selecting currency option."""

    def __init__(self, *args, **kwargs):
        """Initialize the currency serializer."""
        choices = currency_code_mappings()

        allow_blank = kwargs.get('allow_blank', False) or kwargs.get(
            'allow_null', False
        )

        if allow_blank:
            choices = [('', '---------'), *choices]

        kwargs['choices'] = choices

        if 'default' not in kwargs and 'required' not in kwargs:
            kwargs['default'] = '' if allow_blank else currency_code_default

        if 'label' not in kwargs:
            kwargs['label'] = _('Currency')

        if 'help_text' not in kwargs:
            kwargs['help_text'] = _('Select currency from available options')

        if InvenTree.ready.isGeneratingSchema():
            kwargs['help_text'] = (
                kwargs['help_text']
                + '\n\n'
                + '\n'.join(f'* `{value}` - {label}' for value, label in choices)
                + "\n\nOther valid currencies may be found in the 'CURRENCY_CODES' global setting."
            )

        super().__init__(*args, **kwargs)


class DependentField(serializers.Field):
    """A dependent field can be used to dynamically return child fields based on the value of other fields."""

    child = None

    def __init__(self, *args, depends_on, field_serializer, **kwargs):
        """A dependent field can be used to dynamically return child fields based on the value of other fields.

        Example:
        This example adds two fields. If the client selects integer, an integer field will be shown, but if he
        selects char, an char field will be shown. For any other value, nothing will be shown.

        class TestSerializer(serializers.Serializer):
            select_type = serializers.ChoiceField(choices=[
                ("integer", "Integer"),
                ("char", "Char"),
            ])
            my_field = DependentField(depends_on=["select_type"], field_serializer="get_my_field")

            def get_my_field(self, fields):
                if fields["select_type"] == "integer":
                    return serializers.IntegerField()
                if fields["select_type"] == "char":
                    return serializers.CharField()
        """
        super().__init__(*args, **kwargs)

        self.depends_on = depends_on
        self.field_serializer = field_serializer

    def get_child(self, raise_exception=False):
        """This method tries to extract the child based on the provided data in the request by the client."""
        data = deepcopy(self.context['request'].data)

        def visit_parent(node):
            """Recursively extract the data for the parent field/serializer in reverse."""
            nonlocal data

            if node.parent:
                visit_parent(node.parent)

            # only do for composite fields and stop right before the current field
            if hasattr(node, 'child') and node is not self and isinstance(data, dict):
                data = data.get(node.field_name, None)

        visit_parent(self)

        # ensure that data is a dictionary and that a parent exists
        if not isinstance(data, dict) or self.parent is None:
            return

        # check if the request data contains the dependent fields, otherwise skip getting the child
        for f in self.depends_on:
            if data.get(f, None) is None:
                if (
                    self.parent
                    and (v := getattr(self.parent.fields[f], 'default', None))
                    is not None
                ):
                    data[f] = v
                else:
                    return

        # partially validate the data for options requests that set raise_exception while calling .get_child(...)
        if raise_exception:
            validation_data = {k: v for k, v in data.items() if k in self.depends_on}
            serializer = self.parent.__class__(
                context=self.context, data=validation_data, partial=True
            )
            serializer.is_valid(raise_exception=raise_exception)

        # try to get the field serializer
        field_serializer = getattr(self.parent, self.field_serializer)
        child = field_serializer(data)

        if not child:
            return

        self.child = child
        self.child.bind(field_name='', parent=self)

    def to_internal_value(self, data):
        """This method tries to convert the data to an internal representation based on the defined to_internal_value method on the child."""
        self.get_child()
        if self.child:
            return self.child.to_internal_value(data)

        return None

    def to_representation(self, value):
        """This method tries to convert the data to representation based on the defined to_representation method on the child."""
        self.get_child()
        if self.child:
            return self.child.to_representation(value)

        return None


class BareInvenTreeModelSerializer(serializers.ModelSerializer):
    """Inherits the standard Django ModelSerializer class, but also ensures that the underlying model class data are checked on validation. Without Filtering support."""

    # Switch out URLField mapping
    serializer_field_mapping = {
        **serializers.ModelSerializer.serializer_field_mapping,
        models.URLField: InvenTreeRestURLField,
        InvenTreeURLField: InvenTreeRestURLField,
    }

    def __init__(self, instance=None, data=empty, **kwargs):
        """Custom __init__ routine to ensure that *default* values (as specified in the ORM) are used by the DRF serializers, *if* the values are not provided by the user."""
        # If instance is None, we are creating a new instance
        if instance is None and data is not empty:
            if data is None:
                data = OrderedDict()
            else:
                new_data = OrderedDict()
                new_data.update(data)

                data = new_data

            # Add missing fields which have default values
            ModelClass = self.Meta.model

            fields = model_meta.get_field_info(ModelClass)

            for field_name, field in fields.fields.items():
                """
                Update the field IF (and ONLY IF):

                - The field has a specified default value
                - The field does not already have a value set
                """
                if field.has_default() and field_name not in data:
                    value = field.default

                    # Account for callable functions
                    if callable(value):
                        try:
                            value = value()
                        except Exception:
                            continue

                    data[field_name] = value

        super().__init__(instance, data, **kwargs)

    def get_initial(self):
        """Construct initial data for the serializer.

        Use the 'default' values specified by the django model definition
        """
        initials = super().get_initial().copy()

        # Are we creating a new instance?
        if self.instance is None:
            ModelClass = self.Meta.model

            fields = model_meta.get_field_info(ModelClass)

            for field_name, field in fields.fields.items():
                if field.has_default() and field_name not in initials:
                    value = field.default

                    # Account for callable functions
                    if callable(value):
                        try:
                            value = value()
                        except Exception:
                            continue

                    initials[field_name] = value

        return initials

    def skip_create_fields(self):
        """Return a list of 'fields' which should be skipped for model creation.

        This is used to 'bypass' a shortcoming of the DRF framework,
        which does not allow us to have writeable serializer fields which do not exist on the model.

        Default implementation returns an empty list
        """
        return []

    def save(self, **kwargs):
        """Catch any django ValidationError thrown at the moment `save` is called, and re-throw as a DRF ValidationError."""
        try:
            super().save(**kwargs)
        except (ValidationError, DjangoValidationError) as exc:
            raise ValidationError(detail=serializers.as_serializer_error(exc))

        return self.instance

    def create(self, validated_data):
        """Custom create method which supports field adjustment."""
        initial_data = validated_data.copy()

        # Remove any fields which do not exist on the model
        for field in self.skip_create_fields():
            initial_data.pop(field, None)

        return super().create(initial_data)

    def update(self, instance, validated_data):
        """Catch any django ValidationError, and re-throw as a DRF ValidationError."""
        try:
            instance = super().update(instance, validated_data)
        except (ValidationError, DjangoValidationError) as exc:
            raise ValidationError(detail=serializers.as_serializer_error(exc))

        return instance

    def run_validation(self, data=empty):
        """Perform serializer validation.

        In addition to running validators on the serializer fields,
        this class ensures that the underlying model is also validated.
        """
        # Run any native validation checks first (may raise a ValidationError)
        data = super().run_validation(data)

        if not hasattr(self, 'instance') or self.instance is None:
            # No instance exists (we are creating a new one)

            initial_data = data.copy()

            for field in self.skip_create_fields():
                # Remove any fields we do not wish to provide to the model
                initial_data.pop(field, None)

            # Create a (RAM only) instance for extra testing
            instance = self.Meta.model(**initial_data)
        else:
            # Instance already exists (we are updating!)
            instance = self.instance

            # Update instance fields
            for attr, value in data.items():
                try:
                    setattr(instance, attr, value)
                except (ValidationError, DjangoValidationError) as exc:
                    raise ValidationError(detail=serializers.as_serializer_error(exc))

        # Run a 'full_clean' on the model.
        # Note that by default, DRF does *not* perform full model validation!
        try:
            instance.full_clean()
        except (ValidationError, DjangoValidationError) as exc:
            if hasattr(exc, 'message_dict'):
                data = {**exc.message_dict}
            elif hasattr(exc, 'message'):
                data = {'non_field_errors': [str(exc.message)]}
            else:
                data = {'non_field_errors': [str(exc)]}

            # Change '__all__' key (django style) to 'non_field_errors' (DRF style)
            if hasattr(data, '__all__'):
                data['non_field_errors'] = data.pop('__all__')

            raise ValidationError(data)

        return data


class InvenTreeModelSerializer(OptFilter, BareInvenTreeModelSerializer):
    """Inherits the standard Django ModelSerializer class, but also ensures that the underlying model class data are checked on validation."""


class InvenTreeTaggitSerializer(TaggitSerializer):
    """Updated from https://github.com/glemmaPaul/django-taggit-serializer."""

    def update(self, instance, validated_data):
        """Overridden update method to re-add the tagmanager."""
        to_be_tagged, validated_data = self._pop_tags(validated_data)

        tag_object = super().update(instance, validated_data)

        for key in to_be_tagged:
            # re-add the tagmanager
            new_tagobject = tag_object.__class__.objects.get(id=tag_object.id)
            setattr(tag_object, key, getattr(new_tagobject, key))

        return self._save_tags(tag_object, to_be_tagged)


class InvenTreeTagModelSerializer(InvenTreeTaggitSerializer, InvenTreeModelSerializer):
    """Combination of InvenTreeTaggitSerializer and InvenTreeModelSerializer."""


class InvenTreeAttachmentSerializerField(serializers.FileField):
    """Override the DRF native FileField serializer, to remove the leading server path.

    For example, the FileField might supply something like:

    http://127.0.0.1:8000/media/foo/bar.jpg

    Whereas we wish to return:

    /media/foo/bar.jpg

    If the server process is serving the data at 127.0.0.1,
    but a proxy service (e.g. nginx) is then providing DNS lookup to the outside world,
    then an attachment which prefixes the "address" of the internal server
    will not be accessible from the outside world.
    """

    def to_representation(self, value):
        """To json-serializable type."""
        if not value:
            return None

        return os.path.join(str(settings.MEDIA_URL), str(value))


class InvenTreeImageSerializerField(serializers.ImageField):
    """Custom image serializer.

    On upload, validate that the file is a valid image file
    """

    def to_representation(self, value):
        """To json-serializable type."""
        if not value:
            return None

        return os.path.join(str(settings.MEDIA_URL), str(value))


class InvenTreeDecimalField(serializers.FloatField):
    """Custom serializer for decimal fields.

    Solves the following issues:
    - The normal DRF DecimalField renders values with trailing zeros
    - Using a FloatField can result in rounding issues: https://code.djangoproject.com/ticket/30290
    """

    def to_internal_value(self, data):
        """Convert to python type."""
        # Convert the value to a string, and then a decimal
        try:
            return Decimal(str(data))
        except Exception:
            raise serializers.ValidationError(_('Invalid value'))


class NotesFieldMixin:
    """Serializer mixin for handling 'notes' fields.

    The 'notes' field will be hidden in a LIST serializer,
    but available in a DETAIL serializer.
    """

    def __init__(self, *args, **kwargs):
        """Remove 'notes' field from list views."""
        super().__init__(*args, **kwargs)

        if hasattr(self, 'context'):
            if view := self.context.get('view', None):
                if (
                    issubclass(view.__class__, ListModelMixin)
                    and not InvenTree.ready.isGeneratingSchema()
                ):
                    self.fields.pop('notes', None)


class RemoteImageMixin(metaclass=serializers.SerializerMetaclass):
    """Mixin class which allows downloading an 'image' from a remote URL.

    Adds the optional, write-only `remote_image` field to the serializer
    """

    def skip_create_fields(self):
        """Ensure the 'remote_image' field is skipped when creating a new instance."""
        return ['remote_image']

    remote_image = serializers.URLField(
        required=False,
        allow_blank=True,
        write_only=True,
        label=_('Remote Image'),
        help_text=_('URL of remote image file'),
    )

    def validate_remote_image(self, url):
        """Perform custom validation for the remote image URL.

        - Attempt to download the image and store it against this object instance
        - Catches and re-throws any errors
        """
        from InvenTree.helpers_model import download_image_from_url

        if not url:
            return

        if not common_models.InvenTreeSetting.get_setting(
            'INVENTREE_DOWNLOAD_FROM_URL'
        ):
            raise ValidationError(
                _('Downloading images from remote URL is not enabled')
            )

        try:
            self.remote_image_file = download_image_from_url(url)
        except Exception:
            self.remote_image_file = None
            raise ValidationError(_('Failed to download image from remote URL'))

        return url
