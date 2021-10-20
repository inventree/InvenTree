"""
Provides a JSON API for common components.
"""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json

from django.http.response import HttpResponse
from django.utils.decorators import method_decorator
from django.urls import path
from django.views.decorators.csrf import csrf_exempt

from rest_framework.views import APIView
from rest_framework.exceptions import NotAcceptable, NotFound
from django_q.tasks import async_task

from .models import WebhookEndpoint, WebhookMessage
from InvenTree.helpers import inheritors


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
            self._process_result(
                self.webhook.process_payload(message, payload, headers),
                message,
            )

        # return results
        data = self.webhook.get_return(payload, headers, request)
        return HttpResponse(data)

    def _process_payload(self, message_id):
        message = WebhookMessage.objects.get(message_id=message_id)
        self._process_result(
            self.webhook.process_payload(message, message.body, message.header),
            message,
        )

    def _process_result(self, result, message):
        if result:
            message.worked_on = result
            message.save()
        else:
            message.delete()

    def _escalate_object(self, obj):
        classes = inheritors(obj.__class__)
        for cls in classes:
            mdl_name = cls._meta.model_name
            if hasattr(obj, mdl_name):
                return getattr(obj, mdl_name)
        return obj

    def _get_webhook(self, endpoint, request, *args, **kwargs):
        try:
            webhook = self.model_class.objects.get(endpoint_id=endpoint)
            self.webhook = self._escalate_object(webhook)
            self.webhook.init(request, *args, **kwargs)
            return self.webhook.process_webhook()
        except self.model_class.DoesNotExist:
            raise NotFound()


common_api_urls = [
    path('webhook/<slug:endpoint>/', WebhookView.as_view(), name='api-webhook'),
]
