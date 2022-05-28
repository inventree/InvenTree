import logging

from rest_framework import serializers
from rest_framework.fields import empty
from rest_framework.metadata import SimpleMetadata
from rest_framework.utils import model_meta

import users.models
from InvenTree.helpers import str2bool

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

        self.request = request
        self.view = view

        metadata = super().determine_metadata(request, view)

        """
        Custom context information to pass through to the OPTIONS endpoint,
        if the "context=True" is supplied to the OPTIONS requst

        Serializer class can supply context data by defining a get_context_data() method (no arguments)
        """

        context = {}

        if str2bool(request.query_params.get('context', False)):

            if hasattr(self.serializer, 'get_context_data'):
                context = self.serializer.get_context_data()

            metadata['context'] = context

        user = request.user

        if user is None:
            # No actions for you!
            metadata['actions'] = {}
            return metadata

        try:
            # Extract the model name associated with the view
            self.model = view.serializer_class.Meta.model

            # Construct the 'table name' from the model
            app_label = self.model._meta.app_label
            tbl_label = self.model._meta.model_name

            metadata['model'] = tbl_label

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

                    result = check(user, table, permission)

                    if method in actions and not result:
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

    def get_serializer_info(self, serializer):
        """Override get_serializer_info so that we can add 'default' values to any fields whose Meta.model specifies a default value."""
        self.serializer = serializer

        serializer_info = super().get_serializer_info(serializer)

        model_class = None

        try:
            model_class = serializer.Meta.model

            model_fields = model_meta.get_field_info(model_class)

            model_default_func = getattr(model_class, 'api_defaults', None)

            if model_default_func:
                model_default_values = model_class.api_defaults(self.request)
            else:
                model_default_values = {}

            # Iterate through simple fields
            for name, field in model_fields.fields.items():

                if name in serializer_info.keys():

                    if field.has_default():

                        default = field.default

                        if callable(default):
                            try:
                                default = default()
                            except:
                                continue

                        serializer_info[name]['default'] = default

                    elif name in model_default_values:
                        serializer_info[name]['default'] = model_default_values[name]

                    # Attributes to copy from the model to the field (if they don't exist)
                    attributes = ['help_text']

                    for attr in attributes:
                        if attr not in serializer_info[name]:

                            if hasattr(field, attr):
                                serializer_info[name][attr] = getattr(field, attr)

            # Iterate through relations
            for name, relation in model_fields.relations.items():

                if name not in serializer_info.keys():
                    # Skip relation not defined in serializer
                    continue

                if relation.reverse:
                    # Ignore reverse relations
                    continue

                # Extract and provide the "limit_choices_to" filters
                # This is used to automatically filter AJAX requests
                serializer_info[name]['filters'] = relation.model_field.get_limit_choices_to()

                if 'help_text' not in serializer_info[name] and hasattr(relation.model_field, 'help_text'):
                    serializer_info[name]['help_text'] = relation.model_field.help_text

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
            kwargs = getattr(self.view, 'kwargs', None)

            if kwargs:
                pk = None

                for field in ['pk', 'id', 'PK', 'ID']:
                    if field in kwargs:
                        pk = kwargs[field]
                        break

                if pk is not None:
                    try:
                        instance = model_class.objects.get(pk=pk)
                    except (ValueError, model_class.DoesNotExist):
                        pass

        if instance is not None:
            """If there is an instance associated with this API View, introspect that instance to find any specific API info."""

            if hasattr(instance, 'api_instance_filters'):

                instance_filters = instance.api_instance_filters()

                for field_name, field_filters in instance_filters.items():

                    if field_name not in serializer_info.keys():
                        # The field might be missing, but is added later on
                        # This function seems to get called multiple times?
                        continue

                    if 'instance_filters' not in serializer_info[field_name].keys():
                        serializer_info[field_name]['instance_filters'] = {}

                    for key, value in field_filters.items():
                        serializer_info[field_name]['instance_filters'][key] = value

        return serializer_info

    def get_field_info(self, field):
        """Given an instance of a serializer field, return a dictionary of metadata about it.

        We take the regular DRF metadata and add our own unique flavor
        """
        # Run super method first
        field_info = super().get_field_info(field)

        # If a default value is specified for the serializer field, add it!
        if 'default' not in field_info and field.default != empty:
            field_info['default'] = field.get_default()

        # Force non-nullable fields to read as "required"
        # (even if there is a default value!)
        if not field.allow_null and not (hasattr(field, 'allow_blank') and field.allow_blank):
            field_info['required'] = True

        # Introspect writable related fields
        if field_info['type'] == 'field' and not field_info['read_only']:

            # If the field is a PrimaryKeyRelatedField, we can extract the model from the queryset
            if isinstance(field, serializers.PrimaryKeyRelatedField):
                model = field.queryset.model
            else:
                logger.debug("Could not extract model for:", field_info['label'], '->', field)
                model = None

            if model:
                # Mark this field as "related", and point to the URL where we can get the data!
                field_info['type'] = 'related field'
                field_info['model'] = model._meta.model_name

                # Special case for 'user' model
                if field_info['model'] == 'user':
                    field_info['api_url'] = '/api/user/'
                else:
                    field_info['api_url'] = model.get_api_url()

        return field_info
