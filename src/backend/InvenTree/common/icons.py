"""Icon utilities for InvenTree."""

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import TypedDict

from django.core.exceptions import ValidationError
from django.templatetags.static import static

logger = logging.getLogger('inventree')

_icon_packs = None


class Icon(TypedDict):
    """Dict type for an icon.

    Attributes:
        name: The name of the icon.
        category: The category of the icon.
        tags: A list of tags for the icon (used for search).
        variants: A dictionary of variants for the icon, where the key is the variant name and the value is the variant's unicode hex character.
    """

    name: str
    category: str
    tags: list[str]
    variants: dict[str, str]


@dataclass
class IconPack:
    """Dataclass for an icon pack.

    Attributes:
        name: The name of the icon pack.
        prefix: The prefix used for the icon pack.
        fonts: A dictionary of different font file formats for the icon pack, where the key is the css format and the value a path to the font file.
        icons: A dictionary of icons in the icon pack, where the key is the icon name and the value is a dictionary of the icon's variants.
    """

    name: str
    prefix: str
    fonts: dict[str, str]
    icons: dict[str, Icon]


def get_icon_packs():
    """Return a dictionary of available icon packs including their icons."""
    global _icon_packs

    if _icon_packs is None:
        tabler_icons_path = Path(__file__).parent.parent.joinpath(
            'InvenTree/static/tabler-icons/icons.json'
        )
        with open(tabler_icons_path, encoding='utf-8') as tabler_icons_file:
            tabler_icons = json.load(tabler_icons_file)

        icon_packs = [
            IconPack(
                name='Tabler Icons',
                prefix='ti',
                fonts={
                    'woff2': static('tabler-icons/tabler-icons.woff2'),
                    'woff': static('tabler-icons/tabler-icons.woff'),
                    'truetype': static('tabler-icons/tabler-icons.ttf'),
                },
                icons=tabler_icons,
            )
        ]

        from plugin import registry

        for plugin in registry.with_mixin('icon_pack', active=True):
            try:
                icon_packs.extend(plugin.icon_packs())
            except Exception as e:
                logger.warning('Error loading icon pack from plugin %s: %s', plugin, e)

        _icon_packs = {pack.prefix: pack for pack in icon_packs}

    return _icon_packs


def reload_icon_packs():
    """Reload the icon packs."""
    global _icon_packs
    _icon_packs = None
    get_icon_packs()


def validate_icon(icon: str):
    """Validate an icon string in the format pack:name:variant."""
    try:
        pack, name, variant = icon.split(':')
    except ValueError:
        raise ValidationError(
            f'Invalid icon format: {icon}, expected: pack:name:variant'
        )

    packs = get_icon_packs()

    if pack not in packs:
        raise ValidationError(f'Invalid icon pack: {pack}')

    if name not in packs[pack].icons:
        raise ValidationError(f'Invalid icon name: {name}')

    if variant not in packs[pack].icons[name]['variants']:
        raise ValidationError(f'Invalid icon variant: {variant}')

    return packs[pack], packs[pack].icons[name], variant
