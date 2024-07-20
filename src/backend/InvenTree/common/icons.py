"""Icon utilities for InvenTree."""

import json
from pathlib import Path

from django.core.exceptions import ValidationError
from django.templatetags.static import static

_icon_packs = None


def get_icon_packs():
    """Return a dictionary of available icon packs including their icons."""
    global _icon_packs

    if _icon_packs is None:
        icons_path = Path(__file__).parent.parent.joinpath(
            'InvenTree/static/tabler-icons/icons.json'
        )
        with open(icons_path, 'r') as tabler_icons_file:
            tabler_icons = json.load(tabler_icons_file)

        _icon_packs = {
            'ti': {
                'name': 'Tabler Icons',
                'prefix': 'ti',
                'fonts': {
                    'woff2': static('tabler-icons/tabler-icons.woff2'),
                    'woff': static('tabler-icons/tabler-icons.woff'),
                    'ttf': static('tabler-icons/tabler-icons.ttf'),
                },
                'icons': tabler_icons,
            }
        }

    return _icon_packs


def validate_icon(icon: str):
    """Validate an icon string in the format pack:name:variant."""
    try:
        pack, name, variant = icon.split(':')
    except:
        raise ValidationError(
            f'Invalid icon format: {icon}, expected: pack:name:variant'
        )

    packs = get_icon_packs()

    if pack not in packs:
        raise ValidationError(f'Invalid icon pack: {pack}')

    if name not in packs[pack]['icons']:
        raise ValidationError(f'Invalid icon name: {name}')

    if variant not in packs[pack]['icons'][name]['variants']:
        raise ValidationError(f'Invalid icon variant: {variant}')
