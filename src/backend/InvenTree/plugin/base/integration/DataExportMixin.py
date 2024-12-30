"""Plugin mixin class for DataExportMixin."""


class DataExportMixin:
    """Mixin which provides support for custom data export functionality.

    This mixin class allows plugins to implement custom "export" functionality for a queryset.
    """

    class MixinMeta:
        """Meta options for this mixin."""

        MIXIN_NAME = 'DataExport'

    def __init__(self):
        """Register mixin."""
        super().__init__()
        self.add_mixin('export', True, __class__)

    def supports_model(self, model: str) -> bool:
        """Check if this mixin supports the given model.

        Arguments:
            model: The qualified app.model type to check e.g. 'part.partcategory'

        By default, all model types are supported
        """
        return True
