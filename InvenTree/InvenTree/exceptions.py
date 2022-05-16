"""
Custom exception handling for the DRF API
"""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json

from django.db.utils import OperationalError, ProgrammingError, IntegrityError
from django.conf import settings
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils.translation import gettext_lazy as _

from error_report.models import Error

from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.response import Response
from rest_framework import serializers
import rest_framework.views as drfviews


def exception_handler(exc, context):
    """
    Custom exception handler for DRF framework.
    Ref: https://www.django-rest-framework.org/api-guide/exceptions/#custom-exception-handling

    Catches any errors not natively handled by DRF, and re-throws as an error DRF can handle
    """

    response = None

    # Catch any django validation error, and re-throw a DRF validation error
    if isinstance(exc, DjangoValidationError):
        exc = DRFValidationError(detail=serializers.as_serializer_error(exc))

    # Exceptions we will manually check for here
    handled_exceptions = [
        IntegrityError,
        OperationalError,
        ProgrammingError,
        ValueError,
        TypeError,
        NameError,
    ]

    if any([isinstance(exc, err_type) for err_type in handled_exceptions]):

        if settings.DEBUG:
            error_detail = str(exc)
        else:
            error_detail = _("Error details can be found in the admin panel")

        response_data = {
            'error': type(exc).__name__,
            'error_class': str(type(exc)),
            'detail': error_detail,
            'path': context['request'].path,
            'status_code': 500,
        }

        response = Response(response_data, status=500)

        # Log the exception to the database, too
        Error.objects.create(
            kind="Unhandled DRF API Exception",
            info=str(type(exc)),
            data=str(exc),
            path=context['request'].path,
        )

    else:
        # Fallback to the default DRF exception handler
        response = drfviews.exception_handler(exc, context)

    if response is not None:
        # For an error response, include status code information
        response.data['status_code'] = response.status_code
    
        # Convert errors returned under the label '__all__' to 'non_field_errors'
        if '__all__' in response.data:
            response.data['non_field_errors'] = response.data['all']
            del response.data['__all__']

    return response
