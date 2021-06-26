"""
Serializers used in various InvenTree apps
"""


# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework import serializers
from rest_framework.utils import model_meta

import os

from django.conf import settings
from django.contrib.auth.models import User


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

    def is_valid(self, raise_exception=False):
        """
        Override the 'is_valid' method of the underlying ModelSerializer class.

        - This is so we can intercept the data before save() is called.
        - If we are creating a *new* model, replace any "missing" fields with the default values
        - Default values are those specified by the database model
        """

        # This serializer is *not* associated with a model instance
        # This means that we are trying to *create* a new model
        if self.instance is None:
            ModelClass = self.Meta.model

            fields = model_meta.get_field_info(ModelClass)

            for field_name, field in fields.fields.items():

                # Check if the field has a default value
                if field.has_default():

                    # Value not specified?
                    if field_name not in self.initial_data:
                        
                        self.initial_data[field_name] = field.default


        return super().is_valid(raise_exception=raise_exception)

    def validate(self, data):
        """ Perform serializer validation.
        In addition to running validators on the serializer fields,
        this class ensures that the underlying model is also validated.
        """

        # Run any native validation checks first (may throw an ValidationError)
        data = super(serializers.ModelSerializer, self).validate(data)

        # Now ensure the underlying model is correct
        instance = self.Meta.model(**data)
        instance.clean()

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
