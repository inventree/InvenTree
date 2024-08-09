"""Sample icon pack plugin to add custom icons."""

from django.templatetags.static import static

from common.icons import IconPack
from plugin.base.icons.mixins import IconPackMixin
from plugin.plugin import InvenTreePlugin


class SampleIconPlugin(IconPackMixin, InvenTreePlugin):
    """Example plugin to add custom icons."""

    NAME = 'SampleIconPackPlugin'
    SLUG = 'sampleicons'
    TITLE = 'My sample icon pack plugin'

    VERSION = '0.0.1'

    def icon_packs(self):
        """Return a list of custom icon packs."""
        return [
            IconPack(
                name='My Custom Icons',
                prefix='my',
                fonts={
                    'woff2': static('fontawesome/webfonts/fa-regular-400.woff2'),
                    'woff': static('fontawesome/webfonts/fa-regular-400.woff'),
                    'truetype': static('fontawesome/webfonts/fa-regular-400.ttf'),
                },
                icons={
                    'my-icon': {
                        'name': 'My Icon',
                        'category': '',
                        'tags': ['my', 'icon'],
                        'variants': {'filled': 'f0a5', 'cool': 'f073'},
                    }
                },
            )
        ]
