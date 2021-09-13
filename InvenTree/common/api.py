"""
Provides a JSON API for common components.
"""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json
import hmac
import hashlib
import base64
from secrets import compare_digest

from django.utils.decorators import method_decorator
from django.urls import path
from django.views.decorators.csrf import csrf_exempt

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, NotFound, NotAcceptable
from django_q.tasks import async_task

from .models import WebhookEndpoint, WebhookMessage


class CsrfExemptMixin(object):
    """
    Exempts the view from CSRF requirements.
    """

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super(CsrfExemptMixin, self).dispatch(*args, **kwargs)


class VerificationMethod:
    NONE = 0
    TOKEN = 1
    HMAC = 2


class WebhookView(CsrfExemptMixin, APIView):
    """
    Endpoint for receiving webhooks.
    """
    authentication_classes = []
    permission_classes = []
    model_class = WebhookEndpoint
    run_async = False

    # Token
    TOKEN_NAME = "Token"
    VERIFICATION_METHOD = VerificationMethod.NONE

    MESSAGE_OK = "Message was received."
    MESSAGE_TOKEN_ERROR = "Incorrect token in header."

    def post(self, request, endpoint, *args, **kwargs):
        self.init(request, *args, **kwargs)
        # get webhook definition
        self.get_webhook(endpoint, *args, **kwargs)

        # check headers
        headers = request.headers
        try:
            payload = json.loads(request.body)
        except json.decoder.JSONDecodeError as error:
            raise NotAcceptable(error.msg)

        # validate
        self.validate_token(payload, headers, request)
        # process data
        message = self.save_data(payload, headers, request)
        if self.run_async:
            async_task(self._process_payload, message.id)
        else:
            message.worked_on = self.process_payload(message, payload, headers)
            message.save()

        # return results
        return_kwargs = self.get_result(payload, headers, request)
        return Response(**return_kwargs)

    def _process_payload(self, message_id):
        message = WebhookMessage.objects.get(message_id=message_id)
        process_result = self.process_payload(message, message.body, message.header)
        message.worked_on = process_result
        message.save()

    # To be overridden
    def init(self, request, *args, **kwargs):
        self.token = ''
        self.secret = ''
        self.verify = self.VERIFICATION_METHOD

    def get_webhook(self, endpoint):
        try:
            webhook = self.model_class.objects.get(endpoint_id=endpoint)
            self.webhook = webhook
            return self.process_webhook()
        except self.model_class.DoesNotExist:
            raise NotFound()

    def process_webhook(self):
        if self.webhook.token:
            self.token = self.webhook.token
            self.verify = VerificationMethod.TOKEN
            # TODO make a object-setting
        if self.webhook.secret:
            self.secret = self.webhook.secret
            self.verify = VerificationMethod.HMAC
            # TODO make a object-setting
        return True

    def validate_token(self, payload, headers, request):
        token = headers.get(self.TOKEN_NAME, "")

        # no token
        if self.verify == VerificationMethod.NONE:
            pass

        # static token
        elif self.verify == VerificationMethod.TOKEN:
            if not compare_digest(token, self.token):
                raise PermissionDenied(self.MESSAGE_TOKEN_ERROR)

        # hmac token
        elif self.verify == VerificationMethod.HMAC:
            digest = hmac.new(self.secret.encode('utf-8'), request.body, hashlib.sha256).digest()
            computed_hmac = base64.b64encode(digest)
            if not hmac.compare_digest(computed_hmac, token.encode('utf-8')):
                raise PermissionDenied(self.MESSAGE_TOKEN_ERROR)

        return True

    def save_data(self, payload, headers=None, request=None):
        return WebhookMessage.objects.create(
            # host=request.host,
            # TODO fix
            header=headers,
            body=payload,
            endpoint=self.webhook,
        )

    def process_payload(self, message, payload=None, headers=None):
        return True

    def get_result(self, payload, headers=None, request=None):
        context = {}
        context['data'] = {'message': self.MESSAGE_OK}
        context['status'] = 200
        return context


common_api_urls = [
    path('webhook/<slug:endpoint>/', WebhookView.as_view(), name='api-webhook'),
]
