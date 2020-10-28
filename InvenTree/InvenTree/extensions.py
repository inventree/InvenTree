import os
import sys
from enum import Enum
from typing import List

from django.apps import AppConfig, apps
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

def get_all_extensions(event=None) -> List[type]:
    """
    Returns the InvenTreeExtensionMeta classes of all extensions found in the installed Django apps.
    """
    extensions = []
    for app in apps.get_app_configs():
        if hasattr(app, 'InvenTreeExtensionMeta'):
            meta = app.InvenTreeExtensionMeta
            meta.module = app.name
            meta.app = app
            if app.name in settings.EXTENSIONS_EXCLUDE:
                continue

            if hasattr(app, 'is_available') and event:
                if not app.is_available(event):
                    continue
            extensions.append(meta)

    return sorted(
        extensions,
        key=lambda m: (0 if m.module.startswith('pretix.') else 1, str(m.name).lower().replace('pretix ', ''))
    )

