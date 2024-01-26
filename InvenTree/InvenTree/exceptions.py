"""Custom exception handling for the DRF API."""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging
import sys
import traceback

from django.conf import settings
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.utils import IntegrityError, OperationalError
from django.utils.translation import gettext_lazy as _

import rest_framework.views as drfviews
from error_report.models import Error
from rest_framework import serializers
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.response import Response

import InvenTree.sentry

logger = logging.getLogger('inventree')


def log_error(path, error_name=None, error_info=None, error_data=None):
    """Log an error to the database.

    - Uses python exception handling to extract error details

    Arguments:
        path: The 'path' (most likely a URL) associated with this error (optional)

    kwargs:
        error_name: The name of the error (optional, overrides 'kind')
        error_info: The error information (optional, overrides 'info')
        error_data: The error data (optional, overrides 'data')
    """
    kind, info, data = sys.exc_info()

    # Check if the error is on the ignore list
    if kind in settings.IGNORED_ERRORS:
        return

    if error_name:
        kind = error_name
    else:
        kind = getattr(kind, '__name__', 'Unknown Error')

    if error_info:
        info = error_info

    if error_data:
        data = error_data
    else:
        try:
            data = '\n'.join(traceback.format_exception(kind, info, data))
        except AttributeError:
            data = 'No traceback information available'

    # Log error to stderr
    logger.error(info)

    # Ensure the error information does not exceed field size limits
    path = path[:200]
    kind = kind[:128]

    try:
        Error.objects.create(kind=kind, info=info or '', data=data or '', path=path)
    except Exception:
        # Not much we can do if logging the error throws a db exception
        logger.exception('Failed to log exception to database')


def exception_handler(exc, context):
    """Custom exception handler for DRF framework.

    Ref: https://www.django-rest-framework.org/api-guide/exceptions/#custom-exception-handling
    Catches any errors not natively handled by DRF, and re-throws as an error DRF can handle.

    If sentry error reporting is enabled, we will also provide the original exception to sentry.io
    """
    response = None

    # Pass exception to sentry.io handler
    try:
        InvenTree.sentry.report_exception(exc)
    except Exception:
        # If sentry.io fails, we don't want to crash the server!
        pass

    # Catch any django validation error, and re-throw a DRF validation error
    if isinstance(exc, DjangoValidationError):
        exc = DRFValidationError(detail=serializers.as_serializer_error(exc))

    # Default to the built-in DRF exception handler
    response = drfviews.exception_handler(exc, context)

    if response is None:
        # DRF handler did not provide a default response for this exception

        if settings.TESTING:
            # If in TESTING mode, re-throw the exception for traceback
            raise exc
        elif settings.DEBUG:
            # If in DEBUG mode, provide error information in the response
            error_detail = str(exc)
        else:
            error_detail = _('Error details can be found in the admin panel')

        response_data = {
            'error': type(exc).__name__,
            'error_class': str(type(exc)),
            'detail': error_detail,
            'path': context['request'].path,
            'status_code': 500,
        }

        response = Response(response_data, status=500)

        log_error(context['request'].path)

    if response is not None:
        # Convert errors returned under the label '__all__' to 'non_field_errors'
        if '__all__' in response.data:
            response.data['non_field_errors'] = response.data['__all__']
            del response.data['__all__']

    return response
