"""WSGI config for InvenTree project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.10/howto/deployment/wsgi/
"""

import os
import signal  # pragma: no cover
import sys

from django.core.wsgi import get_wsgi_application  # pragma: no cover
from django.dispatch import Signal

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "InvenTree.settings")  # pragma: no cover

application = get_wsgi_application()  # pragma: no cover

# Shutdown signal
# Ref: https://stackoverflow.com/questions/15472075/django-framework-is-there-a-shutdown-event-that-can-be-subscribed-to
shutdown_signal = Signal()


def _forward_to_django_shutdown_signal(signal, frame):
    shutdown_signal.send('system')
    print("AFTER SIGNALS SEND")
    sys.exit(0)   # So runserver does try to exit


signal.signal(signal.SIGINT, _forward_to_django_shutdown_signal)
