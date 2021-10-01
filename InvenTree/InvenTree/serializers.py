"""
Serializers used in various InvenTree apps
"""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals


import os

from decimal import Decimal

from collections import OrderedDict

from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils.translation import ugettext_lazy as _

from djmoney.contrib.django_rest_framework.fields import MoneyField
from djmoney.money import Money
from djmoney.utils import MONEY_CLASSES, get_currency_field_name

from rest_framework import serializers
from rest_framework.utils import model_meta
from rest_framework.fields import empty
from rest_framework.exceptions import ValidationError
from rest_framework.serializers import DecimalField


class InvenTreeMoneySerializer(MoneyField):
    """
    Custom serializer for 'MoneyField',
    which ensures that passed values are numerically valid

    Ref: https://github.com/django-money/django-money/blob/master/djmoney/contrib/django_rest_framework/fields.py
    """

    def get_value(self, data):
        """
        Test that the returned amount is a valid Decimal
        """

        amount = super(DecimalField, self).get_value(data)

        # Convert an empty string to None
        if len(str(amount).strip()) == 0:
            amount = None

        try:
            if amount is not None and amount is not empty:
                amount = Decimal(amount)
        except:
            raise ValidationError({
                self.field_name: _("Must be a valid number")
            })

        currency = data.get(get_currency_field_name(self.field_name), self.default_currency)

        if currency and amount is not None and not isinstance(amount, MONEY_CLASSES) and amount is not empty:
            return Money(amount, currency)
        
        return amount


class UserSerializer(serializers.ModelSerializer):
    """ Serializer for User - provides all fields """

    class Meta:
        model = User
        fields = 'all'


class UserSerializerBrief(serializers.ModelSerializer):
    """ Serializer for User - provides limited information """

    class Meta:
        model = User
        fields = [
            'pk',
            'username',
        ]


class InvenTreeModelSerializer(serializers.ModelSerializer):
    """
    Inherits the standard Django ModelSerializer class,
    but also ensures that the underlying model class data are checked on validation.
    """

    def __init__(self, instance=None, data=empty, **kwargs):
        """
        Custom __init__ routine to ensure that *default* values (as specified in the ORM)
        are used by the DRF serializers, *if* the values are not provided by the user.
        """

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
                        except:
                            continue

                    data[field_name] = value

        super().__init__(instance, data, **kwargs)

    def get_initial(self):
        """
        Construct initial data for the serializer.
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
                        except:
                            continue

                    initials[field_name] = value

        return initials

    def save(self, **kwargs):
        """
        Catch any django ValidationError thrown at the moment save() is called,
        and re-throw as a DRF ValidationError
        """

        try:
            super().save(**kwargs)
        except (ValidationError, DjangoValidationError) as exc:
            raise ValidationError(detail=serializers.as_serializer_error(exc))

        return self.instance

    def update(self, instance, validated_data):
        """
        Catch any django ValidationError, and re-throw as a DRF ValidationError
        """

        try:
            instance = super().update(instance, validated_data)
        except (ValidationError, DjangoValidationError) as exc:
            raise ValidationError(detail=serializers.as_serializer_error(exc))

        return instance

    def run_validation(self, data=empty):
        """
        Perform serializer validation.
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


class InvenTreeAttachmentSerializer(InvenTreeModelSerializer):
    """
    Special case of an InvenTreeModelSerializer, which handles an "attachment" model.

    The only real addition here is that we support "renaming" of the attachment file.
    """

    # The 'filename' field must be present in the serializer
    filename = serializers.CharField(
        label=_('Filename'),
        required=False,
        source='basename',
        allow_blank=False,
    )


class InvenTreeAttachmentSerializerField(serializers.FileField):
    """
    Override the DRF native FileField serializer,
    to remove the leading server path.

    For example, the FileField might supply something like:

    http://127.0.0.1:8000/media/foo/bar.jpg

    Whereas we wish to return:

    /media/foo/bar.jpg

    Why? You can't handle the why!

    Actually, if the server process is serving the data at 127.0.0.1,
    but a proxy service (e.g. nginx) is then providing DNS lookup to the outside world,
    then an attachment which prefixes the "address" of the internal server
    will not be accessible from the outside world.
    """

    def to_representation(self, value):

        if not value:
            return None

        return os.path.join(str(settings.MEDIA_URL), str(value))


class InvenTreeImageSerializerField(serializers.ImageField):
    """
    Custom image serializer.
    On upload, validate that the file is a valid image file
    """

    def to_representation(self, value):

        if not value:
            return None

        return os.path.join(str(settings.MEDIA_URL), str(value))
