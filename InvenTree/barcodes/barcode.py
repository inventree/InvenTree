# -*- coding: utf-8 -*-
import warnings

import plugin.builtin.barcode.mixins as mixin
import plugin.integration


hash_barcode = mixin.hash_barcode


class BarcodePlugin(mixin.BarcodeMixin, plugin.integration.IntegrationPluginBase):
    """
    Legacy barcode plugin definition - will be replaced
    Please use the new Integration Plugin API and the BarcodeMixin
    """
    # TODO @matmair remove this with InvenTree 0.7.0
    def __init__(self, barcode_data=None):
        warnings.warn("using the BarcodePlugin is depreceated", DeprecationWarning)
        super().__init__()
        self.init(barcode_data)
