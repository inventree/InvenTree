"""Plugin mixin classes for icon pack plugin."""

from common.icons import IconPack


class IconPackMixin:
    """Mixin that add custom icon packs."""

    class MixinMeta:
        """Meta options for this mixin."""

        MIXIN_NAME = 'icon_pack'

    def __init__(self):
        """Register mixin."""
        super().__init__()
        self.add_mixin('icon_pack', True, __class__)

    def icon_packs(self) -> list[IconPack]:
        """Return a list of custom icon packs."""
        return []
