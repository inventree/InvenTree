"""Helpers for logging integrations."""

from django.dispatch import receiver

import structlog
from django_structlog import signals


@receiver(signals.update_failure_response)
@receiver(signals.bind_extra_request_finished_metadata)
def add_request_id_to_response(response, logger, **kwargs):
    """Add the request ID to the response header, so that it can be traced through logs.

    source: https://django-structlog.readthedocs.io/en/latest/how_tos.html#bind-request-id-to-response-s-header
    """
    context = structlog.contextvars.get_merged_contextvars(logger)
    response['X-InvenTree-ReqId'] = context['request_id']
