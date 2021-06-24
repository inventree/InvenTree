
# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models

from collections import OrderedDict

from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.utils.encoding import force_str

from rest_framework import exceptions, serializers, fields
from rest_framework.request import clone_request
from rest_framework.utils.field_mapping import ClassLookupDict

from rest_framework.metadata import SimpleMetadata

import users.models


class InvenTreeMetadata(SimpleMetadata):
    """
    Custom metadata class for the DRF API.

    This custom metadata class imits the available "actions",
    based on the user's role permissions.

    Thus when a client send an OPTIONS request to an API endpoint,
    it will only receive a list of actions which it is allowed to perform!

    Additionally, we include some extra information about database models,
    so we can perform lookup for ForeignKey related fields.

    """

    def determine_metadata(self, request, view):
        
        metadata = super().determine_metadata(request, view)

        user = request.user

        if user is None:
            # No actions for you!
            metadata['actions'] = {}
            return metadata

        try:
            # Extract the model name associated with the view
            model = view.serializer_class.Meta.model

            # Construct the 'table name' from the model
            app_label = model._meta.app_label
            tbl_label = model._meta.model_name

            table = f"{app_label}_{tbl_label}"

            actions = metadata.get('actions', None)

            if actions is not None:

                check = users.models.RuleSet.check_table_permission

                # Map the request method to a permission type
                rolemap = {
                    'POST': 'add',
                    'PUT': 'change',
                    'PATCH': 'change',
                    'DELETE': 'delete',
                }

                # Remove any HTTP methods that the user does not have permission for
                for method, permission in rolemap.items():
                    if method in actions and not check(user, table, permission):
                        del actions[method]

                # Add a 'DELETE' action if we are allowed to delete
                if 'DELETE' in view.allowed_methods and check(user, table, 'delete'):
                    actions['DELETE'] = True

                # Add a 'VIEW' action if we are allowed to view
                if 'GET' in view.allowed_methods and check(user, table, 'view'):
                    actions['GET'] = True

        except AttributeError:
            # We will assume that if the serializer class does *not* have a Meta
            # then we don't need a permission
            pass

        return metadata

    def get_field_info(self, field):
        """
        Given an instance of a serializer field, return a dictionary
        of metadata about it.
        """

        field_info = OrderedDict()

        field_info['type'] = self.label_lookup[field]
        field_info['required'] = getattr(field, 'required', False)

        if field_info['type'] == 'field':

            # If the field is a 'ForeignKey' field
            if isinstance(field, serializers.ModelSerializer): # or isinstance(field, serializers.PrimaryKeyRelatedField):
                model = field.Meta.model

                # Construct the 'table name' from the model
                app_label = model._meta.app_label
                tbl_label = model._meta.model_name

                table = f"{app_label}_{tbl_label}"
                field_info['model'] = table

            print(field_info['type'], field, type(field))

        attrs = [
            'read_only', 'label', 'help_text',
            'min_length', 'max_length',
            'min_value', 'max_value'
        ]

        for attr in attrs:
            value = getattr(field, attr, None)
            if value is not None and value != '':
                field_info[attr] = force_str(value, strings_only=True)

        if getattr(field, 'child', None):
            field_info['child'] = self.get_field_info(field.child)
        elif getattr(field, 'fields', None):
            field_info['children'] = self.get_serializer_info(field)

        if (not field_info.get('read_only') and
            not isinstance(field, (serializers.RelatedField, serializers.ManyRelatedField)) and
                hasattr(field, 'choices')):
            field_info['choices'] = [
                {
                    'value': choice_value,
                    'display_name': force_str(choice_name, strings_only=True)
                }
                for choice_value, choice_name in field.choices.items()
            ]

        return field_info