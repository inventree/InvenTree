"""Custom metadata for DRF."""

import logging

from rest_framework import serializers
from rest_framework.fields import empty
from rest_framework.metadata import SimpleMetadata
from rest_framework.utils import model_meta

import common.models
import InvenTree.permissions
import users.models
from InvenTree.helpers import str2bool
from InvenTree.serializers import DependentField

logger = logging.getLogger('inventree')


class InvenTreeMetadata(SimpleMetadata):
    """Custom metadata class for the DRF API.

    This custom metadata class imits the available "actions",
    based on the user's role permissions.

    Thus when a client send an OPTIONS request to an API endpoint,
    it will only receive a list of actions which it is allowed to perform!

    Additionally, we include some extra information about database models,
    so we can perform lookup for ForeignKey related fields.
    """

    def determine_metadata(self, request, view):
        """Overwrite the metadata to adapt to the request user."""
        self.request = request
        self.view = view

        metadata = super().determine_metadata(request, view)

        """
        Custom context information to pass through to the OPTIONS endpoint,
        if the "context=True" is supplied to the OPTIONS request

        Serializer class can supply context data by defining a get_context_data() method (no arguments)
        """

        context = {}

        if str2bool(request.query_params.get('context', False)):
            if hasattr(self, 'serializer') and hasattr(
                self.serializer, 'get_context_data'
            ):
                context = self.serializer.get_context_data()

            metadata['context'] = context

        user = request.user

        if user is None:
            # No actions for you!
            metadata['actions'] = {}
            return metadata

        try:
            # Extract the model name associated with the view
            self.model = InvenTree.permissions.get_model_for_view(view)

            # Construct the 'table name' from the model
            app_label = self.model._meta.app_label
            tbl_label = self.model._meta.model_name

            metadata['model'] = tbl_label

            table = f'{app_label}_{tbl_label}'

            actions = metadata.get('actions', None)

            if actions is None:
                actions = {}

            check = users.models.RuleSet.check_table_permission

            # Map the request method to a permission type
            rolemap = {
                'POST': 'add',
                'PUT': 'change',
                'PATCH': 'change',
                'DELETE': 'delete',
            }

            # let the view define a custom rolemap
            if hasattr(view, 'rolemap'):
                rolemap.update(view.rolemap)

            # Remove any HTTP methods that the user does not have permission for
            for method, permission in rolemap.items():
                result = check(user, table, permission)

                if method in actions and not result:
                    del actions[method]

            # Add a 'DELETE' action if we are allowed to delete
            if 'DELETE' in view.allowed_methods and check(user, table, 'delete'):
                actions['DELETE'] = {}

            # Add a 'VIEW' action if we are allowed to view
            if 'GET' in view.allowed_methods and check(user, table, 'view'):
                actions['GET'] = {}

            metadata['actions'] = actions

        except AttributeError:
            # We will assume that if the serializer class does *not* have a Meta
            # then we don't need a permission
            pass

        return metadata

    def override_value(self, field_name: str, field_key: str, field_value, model_value):
        """Override a value on the serializer with a matching value for the model.

        Often, the serializer field will point to an underlying model field,
        which contains extra information (which is translated already).

        Rather than duplicating this information in the serializer, we can extract it from the model.

        This is used to override the serializer values with model values,
        if (and *only* if) the model value should take precedence.

        The values are overridden under the following conditions:
        - field_value is None
        - model_value is callable, and field_value is not (this indicates that the model value is translated)
        - model_value is not a string, and field_value is a string (this indicates that the model value is translated)

        Arguments:
            - field_name: The name of the field
            - field_key: The property key to override
            - field_value: The value of the field (if available)
            - model_value: The equivalent value of the model (if available)
        """
        if field_value is None and model_value is not None:
            return model_value

        if model_value is None and field_value is not None:
            return field_value

        # Callable values will be evaluated later
        if callable(model_value) and not callable(field_value):
            return model_value

        if callable(field_value) and not callable(model_value):
            return field_value

        # Prioritize translated text over raw string values
        if type(field_value) is str and type(model_value) is not str:
            return model_value

        return field_value

    def get_serializer_info(self, serializer):
        """Override get_serializer_info so that we can add 'default' values to any fields whose Meta.model specifies a default value."""
        self.serializer = serializer

        request = getattr(self, 'request', None)

        serializer_info = super().get_serializer_info(serializer)

        # Look for any dynamic fields which were not available when the serializer was instantiated
        if hasattr(serializer, 'Meta'):
            for field_name in serializer.Meta.fields:
                if field_name in serializer_info:
                    # Already know about this one
                    continue

                if field := getattr(serializer, field_name, None):
                    serializer_info[field_name] = self.get_field_info(field)

        model_class = None

        # Extract read_only_fields and write_only_fields from the Meta class (if available)
        if meta := getattr(serializer, 'Meta', None):
            read_only_fields = getattr(meta, 'read_only_fields', [])
            write_only_fields = getattr(meta, 'write_only_fields', [])
        else:
            read_only_fields = []
            write_only_fields = []

        # Attributes to copy extra attributes from the model to the field (if they don't exist)
        # Note that the attributes may be named differently on the underlying model!
        extra_attributes = {
            'help_text': 'help_text',
            'max_length': 'max_length',
            'label': 'verbose_name',
        }

        try:
            model_class = serializer.Meta.model

            model_fields = model_meta.get_field_info(model_class)

            if model_default_func := getattr(model_class, 'api_defaults', None):
                model_default_values = model_default_func(request=request) or {}
            else:
                model_default_values = {}

            # Iterate through simple fields
            for name, field in model_fields.fields.items():
                if name in serializer_info:
                    if name in read_only_fields:
                        serializer_info[name]['read_only'] = True

                    if name in write_only_fields:
                        serializer_info[name]['write_only'] = True

                    if field.has_default():
                        default = field.default

                        if callable(default):
                            try:
                                default = default()
                            except Exception:
                                continue

                        serializer_info[name]['default'] = default

                    elif name in model_default_values:
                        serializer_info[name]['default'] = model_default_values[name]

                    for field_key, model_key in extra_attributes.items():
                        field_value = getattr(serializer.fields[name], field_key, None)
                        model_value = getattr(field, model_key, None)

                        if value := self.override_value(
                            name, field_key, field_value, model_value
                        ):
                            serializer_info[name][field_key] = value

            # Iterate through relations
            for name, relation in model_fields.relations.items():
                if name not in serializer_info:
                    # Skip relation not defined in serializer
                    continue

                if relation.reverse:
                    # Ignore reverse relations
                    continue

                if name in read_only_fields:
                    serializer_info[name]['read_only'] = True

                if name in write_only_fields:
                    serializer_info[name]['write_only'] = True

                # Extract and provide the "limit_choices_to" filters
                # This is used to automatically filter AJAX requests
                serializer_info[name]['filters'] = (
                    relation.model_field.get_limit_choices_to()
                )

                for field_key, model_key in extra_attributes.items():
                    field_value = getattr(serializer.fields[name], field_key, None)
                    model_value = getattr(relation.model_field, model_key, None)

                    if value := self.override_value(
                        name, field_key, field_value, model_value
                    ):
                        serializer_info[name][field_key] = value

                if name in model_default_values:
                    serializer_info[name]['default'] = model_default_values[name]

        except AttributeError:
            pass

        # Try to extract 'instance' information
        instance = None

        # Extract extra information if an instance is available
        if hasattr(serializer, 'instance'):
            instance = serializer.instance

        if instance is None and model_class is not None:
            # Attempt to find the instance based on kwargs lookup
            view = getattr(self, 'view', None)
            kwargs = getattr(view, 'kwargs', None) if view else None

            if kwargs:
                pk = None

                for field in ['pk', 'id', 'PK', 'ID']:
                    if field in kwargs:
                        pk = kwargs[field]
                        break

                if issubclass(model_class, common.models.BaseInvenTreeSetting):
                    instance = model_class.get_setting_object(**kwargs, create=False)

                elif pk is not None:
                    try:
                        instance = model_class.objects.get(pk=pk)
                    except (ValueError, model_class.DoesNotExist):
                        pass

        if instance is not None:
            """If there is an instance associated with this API View, introspect that instance to find any specific API info."""

            if hasattr(instance, 'api_instance_filters'):
                instance_filters = instance.api_instance_filters()

                for field_name, field_filters in instance_filters.items():
                    if field_name not in serializer_info:
                        # The field might be missing, but is added later on
                        # This function seems to get called multiple times?
                        continue

                    if 'instance_filters' not in serializer_info[field_name]:
                        serializer_info[field_name]['instance_filters'] = {}

                    for key, value in field_filters.items():
                        serializer_info[field_name]['instance_filters'][key] = value

        return serializer_info

    def get_field_info(self, field):
        """Given an instance of a serializer field, return a dictionary of metadata about it.

        We take the regular DRF metadata and add our own unique flavor
        """
        # Try to add the child property to the dependent field to be used by the super call
        if self.label_lookup[field] == 'dependent field':
            field.get_child(raise_exception=True)

        # Run super method first
        field_info = super().get_field_info(field)

        # If a default value is specified for the serializer field, add it!
        if 'default' not in field_info and field.default != empty:
            field_info['default'] = field.get_default()

        # Force non-nullable fields to read as "required"
        # (even if there is a default value!)
        if (
            'required' not in field_info
            and not field.allow_null
            and not (hasattr(field, 'allow_blank') and field.allow_blank)
        ):
            field_info['required'] = True

        # Introspect writable related fields
        if field_info['type'] == 'field' and not field_info['read_only']:
            # If the field is a PrimaryKeyRelatedField, we can extract the model from the queryset
            if isinstance(field, serializers.PrimaryKeyRelatedField) or issubclass(
                field.__class__, serializers.PrimaryKeyRelatedField
            ):
                model = field.queryset.model
            else:
                logger.debug(
                    'Could not extract model for:', field_info.get('label'), '->', field
                )
                model = None

            if model:
                # Mark this field as "related", and point to the URL where we can get the data!
                field_info['type'] = 'related field'
                field_info['model'] = model._meta.model_name

                # Special case for special models
                if field_info['model'] == 'user':
                    field_info['api_url'] = '/api/user/'
                elif field_info['model'] == 'contenttype':
                    field_info['api_url'] = '/api/contenttype/'
                elif hasattr(model, 'get_api_url'):
                    field_info['api_url'] = model.get_api_url()
                else:
                    logger.warning("'get_api_url' method not defined for %s", model)
                    field_info['api_url'] = getattr(model, 'api_url', None)

                # Handle custom 'primary key' field
                field_info['pk_field'] = getattr(field, 'pk_field', 'pk') or 'pk'

        # Add more metadata about dependent fields
        if field_info['type'] == 'dependent field':
            field_info['depends_on'] = field.depends_on

        # Extend field info if the field has a get_field_info method
        if (
            not field_info.get('read_only')
            and hasattr(field, 'get_field_info')
            and callable(field.get_field_info)
        ):
            field_info = field.get_field_info(field, field_info)

        return field_info


InvenTreeMetadata.label_lookup[DependentField] = 'dependent field'
