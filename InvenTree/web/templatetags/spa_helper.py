"""Template tag to render SPA imports."""

import json
from logging import getLogger
from pathlib import Path
from typing import Union

from django import template
from django.conf import settings
from django.utils.safestring import mark_safe

logger = getLogger("InvenTree")
register = template.Library()

FRONTEND_SETTINGS = json.dumps(settings.FRONTEND_SETTINGS)


@register.simple_tag
def spa_bundle(manifest_path: Union[str, Path] = '', app: str = 'web'):
    """Render SPA bundle."""
    def get_url(file: str) -> str:
        """Get static url for file."""
        return f"{settings.STATIC_URL}{app}/{file}"

    if manifest_path == '':
        manifest_path = Path(__file__).parent.parent.joinpath("static/web/manifest.json")
    manifest = Path(manifest_path)

    if not manifest.exists():
        logger.error("Manifest file not found")
        return

    try:
        manifest_data = json.load(manifest.open())
    except (TypeError, json.decoder.JSONDecodeError):
        logger.exception("Failed to parse manifest file")
        return

    return_string = ""
    # JS (based on index.html file as entrypoint)
    index = manifest_data.get("index.html")
    dynamic_files = index.get("dynamicImports", [])
    imports_files = "".join(
        [
            f'<script type="module" src="{get_url(manifest_data[file]["file"])}"></script>'
            for file in dynamic_files
        ]
    )
    return_string += f'<script type="module" src="{get_url(index["file"])}"></script>{imports_files}'

    # CSS (based on index.css file as entrypoint)
    css_index = manifest_data.get("index.css")
    if css_index:
        return_string += f'<link rel="stylesheet" href="{get_url(css_index["file"])}" />'

    return mark_safe(return_string)


@register.simple_tag
def spa_settings():
    """Render settings for spa."""
    return mark_safe(f"""<script>window.INVENTREE_SETTINGS={FRONTEND_SETTINGS}</script>""")
