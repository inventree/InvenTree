"""Serializers used in various InvenTree apps."""

import os
from collections import OrderedDict
from copy import deepcopy
from decimal import Decimal

from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

import tablib
from djmoney.contrib.django_rest_framework.fields import MoneyField
from djmoney.money import Money
from djmoney.utils import MONEY_CLASSES, get_currency_field_name
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.fields import empty
from rest_framework.serializers import DecimalField
from rest_framework.utils import model_meta
from taggit.serializers import TaggitSerializer

import common.models as common_models
from common.settings import currency_code_default, currency_code_mappings
from InvenTree.fields import InvenTreeRestURLField, InvenTreeURLField


class EmptySerializer(serializers.Serializer):
    """Empty serializer for use in testing."""


class InvenTreeMoneySerializer(MoneyField):
    """Custom serializer for 'MoneyField', which ensures that passed values are numerically valid.

    Ref: https://github.com/django-money/django-money/blob/master/djmoney/contrib/django_rest_framework/fields.py
    """

    def __init__(self, *args, **kwargs):
        """Override default values."""
        kwargs['max_digits'] = kwargs.get('max_digits', 19)
        self.decimal_places = kwargs['decimal_places'] = kwargs.get('decimal_places', 6)
        kwargs['required'] = kwargs.get('required', False)

        super().__init__(*args, **kwargs)

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

        return amount


class InvenTreeCurrencySerializer(serializers.ChoiceField):
    """Custom serializers for selecting currency option."""

    def __init__(self, *args, **kwargs):
        """Initialize the currency serializer."""
        choices = currency_code_mappings()

        allow_blank = kwargs.get('allow_blank', False) or kwargs.get(
            'allow_null', False
        )

        if allow_blank:
            choices = [('', '---------')] + choices

        kwargs['choices'] = choices

        if 'default' not in kwargs and 'required' not in kwargs:
            kwargs['default'] = '' if allow_blank else currency_code_default

        if 'label' not in kwargs:
            kwargs['label'] = _('Currency')

        if 'help_text' not in kwargs:
            kwargs['help_text'] = _('Select currency from available options')

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


class InvenTreeModelSerializer(serializers.ModelSerializer):
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
                data = exc.message_dict
            elif hasattr(exc, 'message'):
                data = {'non_field_errors': str(exc.message)}
            else:
                data = {'non_field_errors': str(exc)}

            # Change '__all__' key (django style) to 'non_field_errors' (DRF style)
            if '__all__' in data:
                data['non_field_errors'] = data['__all__']
                del data['__all__']

            raise ValidationError(data)

        return data


class InvenTreeTaggitSerializer(TaggitSerializer):
    """Updated from https://github.com/glemmaPaul/django-taggit-serializer."""

    def update(self, instance, validated_data):
        """Overridden update method to re-add the tagmanager."""
        to_be_tagged, validated_data = self._pop_tags(validated_data)

        tag_object = super().update(instance, validated_data)

        for key in to_be_tagged.keys():
            # re-add the tagmanager
            new_tagobject = tag_object.__class__.objects.get(id=tag_object.id)
            setattr(tag_object, key, getattr(new_tagobject, key))

        return self._save_tags(tag_object, to_be_tagged)


class InvenTreeTagModelSerializer(InvenTreeTaggitSerializer, InvenTreeModelSerializer):
    """Combination of InvenTreeTaggitSerializer and InvenTreeModelSerializer."""

    pass


class UserSerializer(InvenTreeModelSerializer):
    """Serializer for a User."""

    class Meta:
        """Metaclass defines serializer fields."""

        model = User
        fields = ['pk', 'username', 'first_name', 'last_name', 'email']

        read_only_fields = ['username']


class ExendedUserSerializer(UserSerializer):
    """Serializer for a User with a bit more info."""

    from users.serializers import GroupSerializer

    groups = GroupSerializer(read_only=True, many=True)

    class Meta(UserSerializer.Meta):
        """Metaclass defines serializer fields."""

        fields = UserSerializer.Meta.fields + [
            'groups',
            'is_staff',
            'is_superuser',
            'is_active',
        ]

        read_only_fields = UserSerializer.Meta.read_only_fields + ['groups']

    def validate(self, attrs):
        """Expanded validation for changing user role."""
        # Check if is_staff or is_superuser is in attrs
        role_change = 'is_staff' in attrs or 'is_superuser' in attrs
        request_user = self.context['request'].user

        if role_change:
            if request_user.is_superuser:
                # Superusers can change any role
                pass
            elif request_user.is_staff and 'is_superuser' not in attrs:
                # Staff can change any role except is_superuser
                pass
            else:
                raise PermissionDenied(
                    _('You do not have permission to change this user role.')
                )
        return super().validate(attrs)


class UserCreateSerializer(ExendedUserSerializer):
    """Serializer for creating a new User."""

    def validate(self, attrs):
        """Expanded valiadation for auth."""
        # Check that the user trying to create a new user is a superuser
        if not self.context['request'].user.is_superuser:
            raise serializers.ValidationError(_('Only superusers can create new users'))

        # Generate a random password
        password = User.objects.make_random_password(length=14)
        attrs.update({'password': password})
        return super().validate(attrs)

    def create(self, validated_data):
        """Send an e email to the user after creation."""
        from InvenTree.helpers_model import get_base_url

        base_url = get_base_url()

        instance = super().create(validated_data)

        # Make sure the user cannot login until they have set a password
        instance.set_unusable_password()

        message = (
            _('Your account has been created.')
            + '\n\n'
            + _('Please use the password reset function to login')
        )

        if base_url:
            message += f'\n\nURL: {base_url}'

        # Send the user an onboarding email (from current site)
        instance.email_user(subject=_('Welcome to InvenTree'), message=message)

        return instance


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


class InvenTreeAttachmentSerializer(InvenTreeModelSerializer):
    """Special case of an InvenTreeModelSerializer, which handles an "attachment" model.

    The only real addition here is that we support "renaming" of the attachment file.
    """

    @staticmethod
    def attachment_fields(extra_fields=None):
        """Default set of fields for an attachment serializer."""
        fields = [
            'pk',
            'attachment',
            'filename',
            'link',
            'comment',
            'upload_date',
            'user',
            'user_detail',
        ]

        if extra_fields:
            fields += extra_fields

        return fields

    user_detail = UserSerializer(source='user', read_only=True, many=False)

    attachment = InvenTreeAttachmentSerializerField(required=False, allow_null=False)

    # The 'filename' field must be present in the serializer
    filename = serializers.CharField(
        label=_('Filename'), required=False, source='basename', allow_blank=False
    )

    upload_date = serializers.DateField(read_only=True)


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


class DataFileUploadSerializer(serializers.Serializer):
    """Generic serializer for uploading a data file, and extracting a dataset.

    - Validates uploaded file
    - Extracts column names
    - Extracts data rows
    """

    # Implementing class should register a target model (database model) to be used for import
    TARGET_MODEL = None

    class Meta:
        """Metaclass options."""

        fields = ['data_file']

    data_file = serializers.FileField(
        label=_('Data File'),
        help_text=_('Select data file for upload'),
        required=True,
        allow_empty_file=False,
    )

    def validate_data_file(self, data_file):
        """Perform validation checks on the uploaded data file."""
        self.filename = data_file.name

        name, ext = os.path.splitext(data_file.name)

        # Remove the leading . from the extension
        ext = ext[1:]

        accepted_file_types = ['xls', 'xlsx', 'csv', 'tsv', 'xml']

        if ext not in accepted_file_types:
            raise serializers.ValidationError(_('Unsupported file type'))

        # Impose a 50MB limit on uploaded BOM files
        max_upload_file_size = 50 * 1024 * 1024

        if data_file.size > max_upload_file_size:
            raise serializers.ValidationError(_('File is too large'))

        # Read file data into memory (bytes object)
        try:
            data = data_file.read()
        except Exception as e:
            raise serializers.ValidationError(str(e))

        if ext in ['csv', 'tsv', 'xml']:
            try:
                data = data.decode()
            except Exception as e:
                raise serializers.ValidationError(str(e))

        # Convert to a tablib dataset (we expect headers)
        try:
            self.dataset = tablib.Dataset().load(data, ext, headers=True)
        except Exception as e:
            raise serializers.ValidationError(str(e))

        if len(self.dataset.headers) == 0:
            raise serializers.ValidationError(_('No columns found in file'))

        if len(self.dataset) == 0:
            raise serializers.ValidationError(_('No data rows found in file'))

        return data_file

    def match_column(self, column_name, field_names, exact=False):
        """Attempt to match a column name (from the file) to a field (defined in the model).

        Order of matching is:
        - Direct match
        - Case insensitive match
        - Fuzzy match
        """
        if not column_name:
            return None

        column_name = str(column_name).strip()

        column_name_lower = column_name.lower()

        if column_name in field_names:
            return column_name

        for field_name in field_names:
            if field_name.lower() == column_name_lower:
                return field_name

        if exact:
            # Finished available 'exact' matches
            return None

        # TODO: Fuzzy pattern matching for column names

        # No matches found
        return None

    def extract_data(self):
        """Returns dataset extracted from the file."""
        # Provide a dict of available import fields for the model
        model_fields = {}

        # Keep track of columns we have already extracted
        matched_columns = set()

        if self.TARGET_MODEL:
            try:
                model_fields = self.TARGET_MODEL.get_import_fields()
            except Exception:
                pass

        # Extract a list of valid model field names
        model_field_names = list(model_fields.keys())

        # Provide a dict of available columns from the dataset
        file_columns = {}

        for header in self.dataset.headers:
            column = {}

            # Attempt to "match" file columns to model fields
            match = self.match_column(header, model_field_names, exact=True)

            if match is not None and match not in matched_columns:
                matched_columns.add(match)
                column['value'] = match
            else:
                column['value'] = None

            file_columns[header] = column

        return {
            'file_fields': file_columns,
            'model_fields': model_fields,
            'rows': [row.values() for row in self.dataset.dict],
            'filename': self.filename,
        }

    def save(self):
        """Empty overwrite for save."""
        ...


class DataFileExtractSerializer(serializers.Serializer):
    """Generic serializer for extracting data from an imported dataset.

    - User provides an array of matched headers
    - User provides an array of raw data rows
    """

    # Implementing class should register a target model (database model) to be used for import
    TARGET_MODEL = None

    class Meta:
        """Metaclass options."""

        fields = ['columns', 'rows']

    # Mapping of columns
    columns = serializers.ListField(child=serializers.CharField(allow_blank=True))

    rows = serializers.ListField(
        child=serializers.ListField(
            child=serializers.CharField(allow_blank=True, allow_null=True)
        )
    )

    def validate(self, data):
        """Clean data."""
        data = super().validate(data)

        self.columns = data.get('columns', [])
        self.rows = data.get('rows', [])

        if len(self.rows) == 0:
            raise serializers.ValidationError(_('No data rows provided'))

        if len(self.columns) == 0:
            raise serializers.ValidationError(_('No data columns supplied'))

        self.validate_extracted_columns()

        return data

    @property
    def data(self):
        """Returns current data."""
        if self.TARGET_MODEL:
            try:
                model_fields = self.TARGET_MODEL.get_import_fields()
            except Exception:
                model_fields = {}

        rows = []

        for row in self.rows:
            """Optionally pre-process each row, before sending back to the client."""

            processed_row = self.process_row(self.row_to_dict(row))

            if processed_row:
                rows.append({'original': row, 'data': processed_row})

        return {'fields': model_fields, 'columns': self.columns, 'rows': rows}

    def process_row(self, row):
        """Process a 'row' of data, which is a mapped column:value dict.

        Returns either a mapped column:value dict, or None.

        If the function returns None, the column is ignored!
        """
        # Default implementation simply returns the original row data
        return row

    def row_to_dict(self, row):
        """Convert a "row" to a named data dict."""
        row_dict = {'errors': {}}

        for idx, value in enumerate(row):
            if idx < len(self.columns):
                col = self.columns[idx]

                if col:
                    row_dict[col] = value

        return row_dict

    def validate_extracted_columns(self):
        """Perform custom validation of header mapping."""
        if self.TARGET_MODEL:
            try:
                model_fields = self.TARGET_MODEL.get_import_fields()
            except Exception:
                model_fields = {}

        cols_seen = set()

        for name, field in model_fields.items():
            required = field.get('required', False)

            # Check for missing required columns
            if required:
                if name not in self.columns:
                    raise serializers.ValidationError(
                        _(f"Missing required column: '{name}'")
                    )

        for col in self.columns:
            if not col:
                continue

            # Check for duplicated columns
            if col in cols_seen:
                raise serializers.ValidationError(_(f"Duplicate column: '{col}'"))

            cols_seen.add(col)

    def save(self):
        """No "save" action for this serializer."""
        pass


class RemoteImageMixin(metaclass=serializers.SerializerMetaclass):
    """Mixin class which allows downloading an 'image' from a remote URL.

    Adds the optional, write-only `remote_image` field to the serializer
    """

    def skip_create_fields(self):
        """Ensure the 'remote_image' field is skipped when creating a new instance."""
        return ['remote_image']

    remote_image = serializers.URLField(
        required=False,
        allow_blank=False,
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
        except Exception as exc:
            self.remote_image_file = None
            raise ValidationError(str(exc))

        return url
