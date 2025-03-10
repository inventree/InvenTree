"""Plugin mixin classes for icon pack plugin."""

import structlog

from common.icons import IconPack, reload_icon_packs
from plugin.helpers import MixinNotImplementedError

logger = structlog.get_logger('inventree')


class IconPackMixin:
    """Mixin that add custom icon packs."""

    class MixinMeta:
        """Meta options for this mixin."""

        MIXIN_NAME = 'icon_pack'

    def __init__(self):
        """Register mixin."""
        super().__init__()
        self.add_mixin('icon_pack', True, __class__)

    @classmethod
    def _activate_mixin(cls, registry, plugins, *args, **kwargs):
        """Activate icon pack plugins."""
        logger.debug('Reloading icon packs')
        reload_icon_packs()

    def icon_packs(self) -> list[IconPack]:
        """Return a list of custom icon packs."""
        raise MixinNotImplementedError(
            f"{__class__} is missing the 'icon_packs' method"
        )
