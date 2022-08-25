"""Plugin mixin for integrating suppliers."""

import logging
from typing import Dict

from common.models import WebConnectionData

logger = logging.getLogger('inventree')


class SupplierMixin:
    """Mixin to enable supplier integration."""

    CONNECTIONS: Dict[str, WebConnectionData]

    class MixinMeta:
        """Meta for mixin."""
        MIXIN_NAME = "Supplier"

    def __init__(self):
        """Register the mixin."""
        super().__init__()
        self.add_mixin('supplier', True, __class__)
        self.connections = self.setup_connections()

    def setup_connections(self):
        """Setup web connections for this plugin."""
        return getattr(self, 'CONNECTIONS', None)
