"""
Custom exception handling for the DRF API
"""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import sys
import traceback

from django.conf import settings
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils.translation import gettext_lazy as _
from django.views.debug import ExceptionReporter

import rest_framework.views as drfviews
from error_report.models import Error
from rest_framework import serializers
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.response import Response


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

    # Default to the built-in DRF exception handler
    response = drfviews.exception_handler(exc, context)

    if response is None:
        # DRF handler did not provide a default response for this exception

        # If in DEBUG or TESTING mode, provide error information in the response
        if settings.DEBUG or settings.TESTING:
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
        kind, info, data = sys.exc_info()

        Error.objects.create(
            kind=kind.__name__,
            info=info,
            data='\n'.join(traceback.format_exception(kind, info, data)),
            path=context['request'].path,
            html=ExceptionReporter(context['request'], kind, info, data).get_traceback_html(),
        )

    if response is not None:
        # Convert errors returned under the label '__all__' to 'non_field_errors'
        if '__all__' in response.data:
            response.data['non_field_errors'] = response.data['__all__']
            del response.data['__all__']

    return response
