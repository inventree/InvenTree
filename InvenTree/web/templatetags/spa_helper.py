"""Template tag to render SPA imports."""
import json
from logging import getLogger
from pathlib import Path

from django import template
from django.conf import settings
from django.utils.safestring import mark_safe

logger = getLogger("gwaesser_backend")
register = template.Library()


@register.simple_tag
def spa_bundle():
    """Render SPA bundle."""
    manifest = Path(__file__).parent.parent.joinpath("static/web/manifest.json")

    if not manifest.exists():
        logger.error("Manifest file not found")
        return

    manifest_data = json.load(manifest.open())
    index = manifest_data.get("index.html")

    dynmanic_files = index.get("dynamicImports", [])
    imports_files = "".join(
        [
            f'<script type="module" src="{settings.STATIC_URL}web/{manifest_data[file]["file"]}"></script>'
            for file in dynmanic_files
        ]
    )

    return mark_safe(
        f"""<script type="module" src="{settings.STATIC_URL}web/{index['file']}"></script>{imports_files}"""
    )
