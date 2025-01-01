"""Plugin mixin class for DataExportMixin."""


class DataExportMixin:
    """Mixin which allows custom data export functionality."""

    class MixinMeta:
        """Meta options for this mixin."""

        MIXIN_NAME = 'DataExport'

    def __init__(self):
        """Register mixin."""
        super().__init__()
        self.add_mixin('export', True, __class__)
