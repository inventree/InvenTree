"""Serializers used in various InvenTree apps."""

import os
from collections import OrderedDict
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
from rest_framework.exceptions import ValidationError
from rest_framework.fields import empty
from rest_framework.serializers import DecimalField
from rest_framework.utils import model_meta

from .models import extract_int


class InvenTreeMoneySerializer(MoneyField):
    """Custom serializer for 'MoneyField', which ensures that passed values are numerically valid.

    Ref: https://github.com/django-money/django-money/blob/master/djmoney/contrib/django_rest_framework/fields.py
    """

    def __init__(self, *args, **kwargs):
        """Overrite default values."""
        kwargs["max_digits"] = kwargs.get("max_digits", 19)
        kwargs["decimal_places"] = kwargs.get("decimal_places", 4)
        kwargs["required"] = kwargs.get("required", False)

        super().__init__(*args, **kwargs)

    def get_value(self, data):
        """Test that the returned amount is a valid Decimal."""
        amount = super(DecimalField, self).get_value(data)

        # Convert an empty string to None
        if len(str(amount).strip()) == 0:
            amount = None

        try:
            if amount is not None and amount is not empty:
                amount = Decimal(amount)
        except Exception:
            raise ValidationError({
                self.field_name: [_("Must be a valid number")],
            })

        currency = data.get(get_currency_field_name(self.field_name), self.default_currency)

        if currency and amount is not None and not isinstance(amount, MONEY_CLASSES) and amount is not empty:
            return Money(amount, currency)

        return amount


class InvenTreeModelSerializer(serializers.ModelSerializer):
    """Inherits the standard Django ModelSerializer class, but also ensures that the underlying model class data are checked on validation."""

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

    def save(self, **kwargs):
        """Catch any django ValidationError thrown at the moment `save` is called, and re-throw as a DRF ValidationError."""
        try:
            super().save(**kwargs)
        except (ValidationError, DjangoValidationError) as exc:
            raise ValidationError(detail=serializers.as_serializer_error(exc))

        return self.instance

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

        # Now ensure the underlying model is correct

        if not hasattr(self, 'instance') or self.instance is None:
            # No instance exists (we are creating a new one)
            instance = self.Meta.model(**data)
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

            data = exc.message_dict

            # Change '__all__' key (django style) to 'non_field_errors' (DRF style)
            if '__all__' in data:
                data['non_field_errors'] = data['__all__']
                del data['__all__']

            raise ValidationError(data)

        return data


class UserSerializer(InvenTreeModelSerializer):
    """Serializer for a User."""

    class Meta:
        """Metaclass defines serializer fields."""
        model = User
        fields = [
            'pk',
            'username',
            'first_name',
            'last_name',
            'email'
        ]


class ReferenceIndexingSerializerMixin():
    """This serializer mixin ensures the the reference is not to big / small for the BigIntegerField."""

    def validate_reference(self, value):
        """Ensures the reference is not to big / small for the BigIntegerField."""
        if extract_int(value) > models.BigIntegerField.MAX_BIGINT:
            raise serializers.ValidationError('reference is to to big')
        return value


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

    user_detail = UserSerializer(source='user', read_only=True, many=False)

    attachment = InvenTreeAttachmentSerializerField(
        required=False,
        allow_null=False,
    )

    # The 'filename' field must be present in the serializer
    filename = serializers.CharField(
        label=_('Filename'),
        required=False,
        source='basename',
        allow_blank=False,
    )


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
            raise serializers.ValidationError(_("Invalid value"))


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

        fields = [
            'data_file',
        ]

    data_file = serializers.FileField(
        label=_("Data File"),
        help_text=_("Select data file for upload"),
        required=True,
        allow_empty_file=False,
    )

    def validate_data_file(self, data_file):
        """Perform validation checks on the uploaded data file."""
        self.filename = data_file.name

        name, ext = os.path.splitext(data_file.name)

        # Remove the leading . from the extension
        ext = ext[1:]

        accepted_file_types = [
            'xls', 'xlsx',
            'csv', 'tsv',
            'xml',
        ]

        if ext not in accepted_file_types:
            raise serializers.ValidationError(_("Unsupported file type"))

        # Impose a 50MB limit on uploaded BOM files
        max_upload_file_size = 50 * 1024 * 1024

        if data_file.size > max_upload_file_size:
            raise serializers.ValidationError(_("File is too large"))

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
            raise serializers.ValidationError(_("No columns found in file"))

        if len(self.dataset) == 0:
            raise serializers.ValidationError(_("No data rows found in file"))

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
        model_field_names = [key for key in model_fields.keys()]

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

        fields = [
            'columns',
            'rows',
        ]

    # Mapping of columns
    columns = serializers.ListField(
        child=serializers.CharField(
            allow_blank=True,
        ),
    )

    rows = serializers.ListField(
        child=serializers.ListField(
            child=serializers.CharField(
                allow_blank=True,
                allow_null=True,
            ),
        )
    )

    def validate(self, data):
        """Clean data."""
        data = super().validate(data)

        self.columns = data.get('columns', [])
        self.rows = data.get('rows', [])

        if len(self.rows) == 0:
            raise serializers.ValidationError(_("No data rows provided"))

        if len(self.columns) == 0:
            raise serializers.ValidationError(_("No data columns supplied"))

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
                rows.append({
                    "original": row,
                    "data": processed_row,
                })

        return {
            'fields': model_fields,
            'columns': self.columns,
            'rows': rows,
        }

    def process_row(self, row):
        """Process a 'row' of data, which is a mapped column:value dict.

        Returns either a mapped column:value dict, or None.

        If the function returns None, the column is ignored!
        """
        # Default implementation simply returns the original row data
        return row

    def row_to_dict(self, row):
        """Convert a "row" to a named data dict."""
        row_dict = {
            'errors': {},
        }

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
                    raise serializers.ValidationError(_(f"Missing required column: '{name}'"))

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
