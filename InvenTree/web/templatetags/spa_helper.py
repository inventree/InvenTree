"""Template tag to render SPA imports."""

import json
from logging import getLogger
from pathlib import Path

from django import template
from django.conf import settings
from django.utils.safestring import mark_safe

logger = getLogger("InvenTree")
register = template.Library()

FRONTEND_SETTINGS = json.dumps(settings.FRONTEND_SETTINGS)


@register.simple_tag
def spa_bundle():
    """Render SPA bundle."""
    manifest = Path(__file__).parent.parent.joinpath("static/web/manifest.json")

    if not manifest.exists():
        logger.error("Manifest file not found")
        return

    try:
        manifest_data = json.load(manifest.open())
    except (TypeError, json.decoder.JSONDecodeError):
        logger.exception("Failed to parse manifest file")
        return
    manifest_data = json.load(manifest.open())
    index = manifest_data.get("index.html")
    css_index = manifest_data.get("index.css")

    dynamic_files = index.get("dynamicImports", [])
    imports_files = "".join(
        [
            f'<script type="module" src="{settings.STATIC_URL}web/{manifest_data[file]["file"]}"></script>'
            for file in dynamic_files
        ]
    )

    return mark_safe(
        f"""<link rel="stylesheet" href="{settings.STATIC_URL}web/{css_index['file']}" />
        <script type="module" src="{settings.STATIC_URL}web/{index['file']}"></script>{imports_files}"""
    )


@register.simple_tag
def spa_settings():
    """Render settings for spa."""
    return mark_safe(f"""<script>window.INVENTREE_SETTINGS={FRONTEND_SETTINGS}</script>""")
