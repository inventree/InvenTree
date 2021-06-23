
# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework.metadata import SimpleMetadata

import users.models


class InvenTreeMetadata(SimpleMetadata):
    """
    Custom metadata class for the DRF API.

    This custom metadata class imits the available "actions",
    based on the user's role permissions.

    Thus when a client send an OPTIONS request to an API endpoint,
    it will only receive a list of actions which it is allowed to perform!

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
                if check(user, table, 'delete'):
                    actions['DELETE'] = True

                # Add a 'VIEW' action if we are allowed to view
                if check(user, table, 'view'):
                    actions['GET'] = True

        except AttributeError:
            # We will assume that if the serializer class does *not* have a Meta
            # then we don't need a permission
            pass

        return metadata
