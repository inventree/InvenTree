"""Async routings for InvenTree."""

from django.urls import path

from channels.routing import URLRouter

from web.consumers import InvenTreeConsumer

websocket_urlpatterns = [
    path('ws/', URLRouter([path('page/<url_name>/', InvenTreeConsumer.as_asgi())]))
]
