"""Serializers used in various InvenTree apps."""

import os
from collections import OrderedDict
from copy import deepcopy
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import models
from django.db.models import QuerySet
from django.utils.translation import gettext_lazy as _

from djmoney.contrib.django_rest_framework.fields import MoneyField
from djmoney.money import Money
from djmoney.utils import MONEY_CLASSES, get_currency_field_name
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.fields import empty
from rest_framework.mixins import ListModelMixin
from rest_framework.serializers import DecimalField, Serializer
from rest_framework.utils import model_meta
from taggit.serializers import TaggitSerializer, TagListSerializerField

import common.models as common_models
import InvenTree.ready
from common.currency import currency_code_default, currency_code_mappings
from InvenTree.fields import InvenTreeRestURLField, InvenTreeURLField
from InvenTree.helpers import str2bool
from InvenTree.helpers_model import getModelsWithMixin

from .setting.storages import StorageBackends


# region path filtering
class FilterableSerializerField:
    """Mixin to mark serializer as filterable.

    This needs to be used in conjunction with OptionalField(s) on the serializer field!
    """

    is_filterable = None
    is_filterable_vals = {}

    # Options for automatic queryset prefetching
    prefetch_fields: Optional[list[str]] = None

    def __init__(self, *args, **kwargs):
        """Initialize the serializer."""
        self.is_filterable = kwargs.pop('is_filterable', None)
        self.is_filterable_vals = kwargs.pop('is_filterable_vals', {})
        self.prefetch_fields = kwargs.pop('prefetch_fields', None)

        super().__init__(*args, **kwargs)


@dataclass
class OptionalField:
    """DataClass used to optionally enable a serializer field.

    This is used in conjunction with the `FilterableSerializerMixin` to allow
    dynamic inclusion or exclusion of serializer fields at runtime.
    """

    serializer_class: Serializer
    serializer_kwargs: Optional[dict] = None
    default_include: bool = False
    filter_name: Optional[str] = None
    filter_by_query: bool = True
    prefetch_fields: Optional[list[str]] = None


class FilterableSerializerMixin:
    """Mixin that enables filtering of marked fields on a serializer.

    Use the `OptionalField` helper class to mark serializer fields as filterable.
    This introduces overhead during initialization, so only use this mixin when necessary.
    """

    fields_to_remove: set = None
    optional_fields: set = None
    filter_on_query: bool = True

    def __init__(self, *args, **kwargs):
        """Initialization routine for the serializer. This gathers and applies filters through kwargs."""
        # add list_serializer_class to meta if not present - reduces duplication
        if not isinstance(self, FilterableListSerializer) and (
            not hasattr(self.Meta, 'list_serializer_class')
        ):
            self.Meta.list_serializer_class = FilterableListSerializer

        # Extract some useful context information for later use
        context = kwargs.get('context', {})
        self.request = context.get('request', None) or getattr(self, 'request', None)
        self.request_query_params = (
            dict(getattr(self.request, 'query_params', {})) if self.request else {}
        )

        # Determine if this is a top-level serializer
        top_level_serializer = context.get('top_level_serializer', None)

        self.is_top_level = (
            top_level_serializer is None
            or top_level_serializer == self.__class__.__name__
        )

        if top_level_serializer is None:
            context['top_level_serializer'] = self.__class__.__name__
            kwargs['context'] = context

        self.gather_optional_fields(kwargs)

        super().__init__(*args, **kwargs)

        # Ensure any fields we are *not* using are removed
        if len(self.fields_to_remove) > 0:
            for field_name in self.fields_to_remove:
                self.fields.pop(field_name, None)

    def is_exporting(self) -> bool:
        """Determine if we are exporting data."""
        return getattr(self, '_exporting_data', False)

    def is_field_included(
        self, field_name: str, field: OptionalField, kwargs: dict
    ) -> bool:
        """Determine at runtime whether an OptionalField should be included.

        Arguments:
            field_name: Name of the field
            field: The OptionalField instance
            kwargs: The kwargs provided to the serializer instance

        Returns:
            True if the field should be included, False otherwise.

        Order of operations:

        - If we are generating the schema, always include the field
        - If this is a write request (POST, PUT, PATCH) and we are not exporting, always include the field
        - If this is a top-level serializer, check the request query parameters for the filter name
        - Check the kwargs provided to the serializer instance
        - Finally, fall back to the default_include value for the field itself
        """
        field_ref = field.filter_name or field_name

        # First, check kwargs provided to the serializer instance
        # We also pop the value to avoid issues with nested serializers
        value = kwargs.pop(field_ref, None)

        # We do not want to pop fields while generating the schema
        if InvenTree.ready.isGeneratingSchema():
            return True

        write_request = False

        field_kwargs = field.serializer_kwargs or {}

        # Skip filtering for a write request - all fields should be present for data creation
        if method := getattr(self.request, 'method', None):
            if (
                self.is_top_level
                and str(method).lower() in ['post', 'put', 'patch']
                and not self.is_exporting()
            ):
                write_request = True

        if write_request:
            # Ignore read_only fields for write requests
            return field_kwargs.get('read_only', False) is not True
        else:
            # Ignore write_only fields for read requests
            if field_kwargs.get('write_only', False):
                return False

        # For a top-level serializer, check request query parameters
        if (
            self.is_top_level
            and self.request
            and self.filter_on_query
            and field.filter_by_query
        ):
            param_value = self.request.query_params.get(field_ref, None)

            if param_value is not None:
                # Convert from list to single value if needed
                if type(param_value) == list and len(param_value) == 1:
                    param_value = param_value[0]

                value = str2bool(param_value)

        if value is None:
            value = field.default_include

        return value

    def gather_optional_fields(self, kwargs):
        """Determine which optional fields will be included on this serializer.

        Note that there may be instances of OptionalField in the field set,
        which need to either be instantiated or removed.
        """
        self.prefetch_list = set()
        self.fields_to_remove = set()
        self.optional_fields = set()

        # Walk upwards through the class hierarchy
        seen_vars = set()

        for base in self.__class__.__mro__:
            for field_name, field in vars(base).items():
                if field_name in seen_vars:
                    continue

                seen_vars.add(field_name)

                if field and isinstance(field, OptionalField):
                    if self.is_field_included(field_name, field, kwargs):
                        self.optional_fields.add(field_name)
                        # Add prefetch information
                        if field.prefetch_fields:
                            for pf in field.prefetch_fields:
                                self.prefetch_list.add(pf)
                    else:
                        self.fields_to_remove.add(field_name)

    def get_field_names(self, declared_fields, info):
        """Remove unused fields before returning field names."""
        field_names = super().get_field_names(declared_fields, info)

        # Add any optional fields which are included
        for field_name in self.optional_fields:
            if field_name not in field_names:
                field_names.append(field_name)

        # Remove any fields which are marked for removal
        for field_name in self.fields_to_remove:
            if field_name in field_names:
                field_names.remove(field_name)

        return field_names

    def build_optional_field(self, field_name: str):
        """Build an optional field, based on the provided field name."""
        field = getattr(self, field_name, None)

        if field and isinstance(field, OptionalField):
            return field.serializer_class, field.serializer_kwargs or {}

    def build_relational_field(self, field_name, relation_info):
        """Handle a special case where an OptionalField shadows a model relation."""
        if field_name in self.optional_fields:
            if field := self.build_optional_field(field_name):
                return field

        return super().build_relational_field(field_name, relation_info)

    def build_property_field(self, field_name, model_class):
        """Handle a special case where an OptionalField shadows a model property."""
        if field_name in self.optional_fields:
            if field := self.build_optional_field(field_name):
                return field

        return super().build_property_field(field_name, model_class)

    def build_unknown_field(self, field_name, model_class):
        """Perform lazy initialization of OptionalFields.

        The DRF framework calls this method when it encounters a field which is not yet initialized.
        """
        if field := self.build_optional_field(field_name):
            return field

        return super().build_unknown_field(field_name, model_class)

    def prefetch_queryset(self, queryset: QuerySet) -> QuerySet:
        """Apply any prefetching to the queryset based on the optionally included fields.

        Args:
            queryset: The original queryset.

        Returns:
            The modified queryset with prefetching applied.
        """
        # If we are inside an OPTIONS request, DO NOT PREFETCH
        if request := getattr(self, 'request', None):
            if method := getattr(request, 'method', None):
                if str(method).lower() == 'options':
                    return queryset

            if getattr(request, '_metadata_requested', False):
                return queryset

        if self.prefetch_list and len(self.prefetch_list) > 0:
            queryset = queryset.prefetch_related(*list(self.prefetch_list))

        return queryset


# special serializers which allow filtering
class FilterableListSerializer(
    FilterableSerializerField, FilterableSerializerMixin, serializers.ListSerializer
):
    """Custom ListSerializer which allows filtering of fields."""


# special serializer fields which allow filtering
class FilterableListField(FilterableSerializerField, serializers.ListField):
    """Custom ListField which allows filtering."""


class FilterableSerializerMethodField(
    FilterableSerializerField, serializers.SerializerMethodField
):
    """Custom SerializerMethodField which allows filtering."""


class FilterableDateTimeField(FilterableSerializerField, serializers.DateTimeField):
    """Custom DateTimeField which allows filtering."""


class FilterableFloatField(FilterableSerializerField, serializers.FloatField):
    """Custom FloatField which allows filtering."""


class FilterableCharField(FilterableSerializerField, serializers.CharField):
    """Custom CharField which allows filtering."""


class FilterableIntegerField(FilterableSerializerField, serializers.IntegerField):
    """Custom IntegerField which allows filtering."""


class FilterableTagListField(FilterableSerializerField, TagListSerializerField):
    """Custom TagListSerializerField which allows filtering."""

    class Meta:
        """Empty Meta class."""


# endregion


class EmptySerializer(serializers.Serializer):
    """Empty serializer for use in testing."""


class TreePathSerializer(serializers.Serializer):
    """Serializer field for representing a tree path."""

    class Meta:
        """Metaclass options."""

        fields = [
            'pk',
            'name',
            # Any fields after this point are optional, and can be included via extra_fields
            'icon',
        ]

    def __init__(self, *args, extra_fields: Optional[list[str]] = None, **kwargs):
        """Initialize the TreePathSerializer."""
        super().__init__(*args, **kwargs)

        allowed_fields = ['pk', 'name', *(extra_fields or [])]

        for field in list(self.fields.keys()):
            if field not in allowed_fields:
                self.fields.pop(field, None)

    pk = serializers.IntegerField(read_only=True)
    name = serializers.CharField(read_only=True)
    icon = serializers.CharField(required=False, read_only=True)


class InvenTreeMoneySerializer(FilterableSerializerField, MoneyField):
    """Custom serializer for 'MoneyField', which ensures that passed values are numerically valid.

    Ref: https://github.com/django-money/django-money/blob/master/djmoney/contrib/django_rest_framework/fields.py
    This field allows filtering.
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


class InvenTreeModelSerializer(FilterableSerializerField, serializers.ModelSerializer):
    """Inherits the standard Django ModelSerializer class, but also ensures that the underlying model class data are checked on validation."""

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

        if settings.STORAGE_TARGET == StorageBackends.S3:
            return str(value.url)
        return os.path.join(str(settings.MEDIA_URL), str(value))


class InvenTreeImageSerializerField(serializers.ImageField):
    """Custom image serializer.

    On upload, validate that the file is a valid image file
    """

    def to_representation(self, value):
        """To json-serializable type."""
        if not value:
            return None

        if settings.STORAGE_TARGET == StorageBackends.S3:
            return str(value.url)
        return os.path.join(str(settings.MEDIA_URL), str(value))


class InvenTreeDecimalField(serializers.FloatField):
    """Custom serializer for decimal fields.

    Solves the following issues:
    - The normal DRF DecimalField renders values with trailing zeros
    - Using a FloatField can result in rounding issues: https://code.djangoproject.com/ticket/30290
    """

    def to_internal_value(self, data):
        """Convert to python type."""
        if data in [None, '']:
            if self.allow_null:
                return None
            raise serializers.ValidationError(_('This field may not be null.'))

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


class ContentTypeField(serializers.ChoiceField):
    """Serializer field which represents a ContentType as 'app_label.model_name'.

    This field converts a ContentType instance to a string representation in the format 'app_label.model_name' during serialization, and vice versa during deserialization.

    Additionally, a "mixin_class" can be supplied to the field, which will restrict the valid content types to only those models which inherit from the specified mixin.
    """

    mixin_class = None

    def __init__(self, *args, mixin_class=None, **kwargs):
        """Initialize the ContentTypeField.

        Args:
            mixin_class: Optional mixin class to restrict valid content types.
        """
        from InvenTree.cache import get_cached_content_types

        self.mixin_class = mixin_class

        # Override the 'choices' field, to limit to the appropriate models
        if self.mixin_class is not None:
            models = getModelsWithMixin(self.mixin_class)

            kwargs['choices'] = [
                (
                    f'{model._meta.app_label}.{model._meta.model_name}',
                    model._meta.verbose_name,
                )
                for model in models
            ]
        else:
            content_types = get_cached_content_types()

            kwargs['choices'] = [
                (f'{ct.app_label}.{ct.model}', str(ct)) for ct in content_types
            ]

        if kwargs.get('allow_null') or kwargs.get('allow_blank'):
            kwargs['choices'] = [('', '---------'), *kwargs['choices']]

        super().__init__(*args, **kwargs)

    def to_representation(self, value):
        """Convert ContentType instance to string representation."""
        return f'{value.app_label}.{value.model}'

    def to_internal_value(self, data):
        """Convert string representation back to ContentType instance."""
        content_type = None

        if data in ['', None]:
            return None

        # First, try to resolve the content type via direct pk value
        try:
            content_type_id = int(data)
            content_type = ContentType.objects.get_for_id(content_type_id)
        except (ValueError, ContentType.DoesNotExist):
            content_type = None

        try:
            if len(data.split('.')) == 2:
                app_label, model = data.split('.')
                content_types = ContentType.objects.filter(
                    app_label=app_label, model=model
                )

                if content_types.count() == 1:
                    # Try exact match first
                    content_type = content_types.first()
            else:
                # Try lookup just on model name
                content_types = ContentType.objects.filter(model=data)
                if content_types.exists() and content_types.count() == 1:
                    content_type = content_types.first()

        except Exception:
            raise ValidationError(_('Invalid content type format'))

        if content_type is None:
            raise ValidationError(_('Content type not found'))

        if self.mixin_class is not None:
            model_class = content_type.model_class()
            if not issubclass(model_class, self.mixin_class):
                raise ValidationError(
                    _('Content type does not match required mixin class')
                )

        return content_type
