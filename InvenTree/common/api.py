"""
Provides a JSON API for common components.
"""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json

from django.utils.decorators import method_decorator
from django.urls import path
from django.views.decorators.csrf import csrf_exempt

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import NotAcceptable, NotFound
from django_q.tasks import async_task

from .models import WebhookEndpoint, WebhookMessage


class CsrfExemptMixin(object):
    """
    Exempts the view from CSRF requirements.
    """

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super(CsrfExemptMixin, self).dispatch(*args, **kwargs)


class WebhookView(CsrfExemptMixin, APIView):
    """
    Endpoint for receiving webhooks.
    """
    authentication_classes = []
    permission_classes = []
    model_class = WebhookEndpoint
    run_async = False

    def post(self, request, endpoint, *args, **kwargs):
        # get webhook definition
        self._get_webhook(endpoint, request, *args, **kwargs)

        # check headers
        headers = request.headers
        try:
            payload = json.loads(request.body)
        except json.decoder.JSONDecodeError as error:
            raise NotAcceptable(error.msg)

        # validate
        self.webhook.validate_token(payload, headers, request)
        # process data
        message = self.webhook.save_data(payload, headers, request)
        if self.run_async:
            async_task(self._process_payload, message.id)
        else:
            message.worked_on = self.webhook.process_payload(message, payload, headers)
            message.save()

        # return results
        return_kwargs = self.webhook.get_result(payload, headers, request)
        return Response(**return_kwargs)

    def _process_payload(self, message_id):
        message = WebhookMessage.objects.get(message_id=message_id)
        process_result = self.webhook.process_payload(message, message.body, message.header)
        message.worked_on = process_result
        message.save()

    def _get_webhook(self, endpoint, request, *args, **kwargs):
        try:
            webhook = self.model_class.objects.get(endpoint_id=endpoint)
            self.webhook = webhook
            self.webhook.init(request, *args, **kwargs)
            return self.webhook.process_webhook()
        except self.model_class.DoesNotExist:
            raise NotFound()


common_api_urls = [
    path('webhook/<slug:endpoint>/', WebhookView.as_view(), name='api-webhook'),
]
