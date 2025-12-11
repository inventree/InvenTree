"""Stuff for Server Side Events / Websockets."""

import random

from django.http import HttpResponse
from django.urls import include, path

import django_eventstream
from django_eventstream import send_event
from django_eventstream.channelmanager import DefaultChannelManager


class MyChannelManager(DefaultChannelManager):
    """Custom channel manager to restrict access to user-specific channels."""

    def can_read_channel(self, user, channel):
        """Override to restrict channel access."""
        # require auth for prefixed channels - there should only be prefixed channels
        if channel.startswith('_') and user is None:
            return False
        return channel == f'_user_{user.pk}'


def push_msg(request):
    """Function to push a test message to the current user."""
    usr_pk = request.user.pk
    rndm = random.randint(0, 1000)
    send_event(f'_user_{usr_pk}', 'message', {'text': f'hello world {usr_pk}: {rndm}'})
    return HttpResponse('Message sent')


sse_urlpatterns = [
    path('events/push_msg/', push_msg, name='push-msg'),
    path(
        'events/<usr_pk>/',
        include(django_eventstream.urls),
        {'format-channels': ['_user_{usr_pk}']},
    ),
]

# router = DefaultRouter()

# # register by class
# router.register(
#     "events2",
#     EventsViewSet(channels=["channel1", "channel2"]),
#     basename="events")

# sse_urlpatterns = [
#     path("", include(router.urls)),
# ]
