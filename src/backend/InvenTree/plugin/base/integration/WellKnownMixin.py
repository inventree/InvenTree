"""Plugin mixin class for adding well-known urls."""

from plugin import PluginMixinEnum
from plugin.helpers import MixinNotImplementedError


class WellKnownMixin:
    """Mixin class which provides support for advertising well-known URLs."""

    class MixinMeta:
        """Meta options for this mixin class."""

        MIXIN_NAME = 'WellKnown'

    def __init__(self):
        """Register the mixin."""
        super().__init__()
        self.add_mixin(PluginMixinEnum.WELLKNOWN, True, __class__)

    def get_well_known_urls(self, request=None) -> list[tuple[str, str]]:
        """Get well-known URLs.

        This method *must* be implemented by the plugin class.

        Arguments:
            request: The Django request object (optional)

        Returns:
            A list of well-known URLs as (name, url) tuples, or None if not available

        Raises:
            Can raise any exception if the update fails
        """
        raise MixinNotImplementedError(
            'Plugin must implement get_well_known_urls method'
        )  # pragma: no cover
