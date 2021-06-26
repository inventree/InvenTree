"""
Serializers used in various InvenTree apps
"""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os

from collections import OrderedDict

from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError as DjangoValidationError

from rest_framework import serializers
from rest_framework.utils import model_meta
from rest_framework.fields import empty
from rest_framework.exceptions import ValidationError


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

        self.instance = instance

        # If instance is None, we are creating a new instance
        if instance is None:
            
            if data is empty:
                data = OrderedDict()
            else:
                # Required to side-step immutability of a QueryDict
                data = data.copy()

            # Add missing fields which have default values
            ModelClass = self.Meta.model

            fields = model_meta.get_field_info(ModelClass)

            for field_name, field in fields.fields.items():

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

        initials = super().get_initial()

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

    def run_validation(self, data=empty):
        """ Perform serializer validation.
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
                setattr(instance, attr, value)

        # Run a 'full_clean' on the model.
        # Note that by default, DRF does *not* perform full model validation!
        try:
            instance.full_clean()
        except (ValidationError, DjangoValidationError) as exc:
            raise ValidationError(detail=serializers.as_serializer_error(exc))

        return data


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
