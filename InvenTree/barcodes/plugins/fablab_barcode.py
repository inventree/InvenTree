"""
Barcode reader class for part IPNs used in the FabLab.
Author: Julian Guinane (jgui0653@uni.sydney.edu.au)
"""

# -*- coding: utf-8 -*-

import json
import barcodenumber

from barcodes.barcode import BarcodePlugin

from part.models import Part

from rest_framework.exceptions import ValidationError


class FablabBarcodePlugin(BarcodePlugin):

    PLUGIN_NAME = "FablabBarcode"
    BARCODE_STANDARDS = ['EAN', 'EAN13', 'EAN8', 'UPC'] # print(barcodenumber.barcodes()) for list of possible choices

    @property
    def name(self):
        return self.PLUGIN_NAME

    def validate(self):
        """
        A "Fablab" barcode must be a valid product code that follows any of the following standards:
          * ean (ean12)
          * ean8
          * ean13
          * upc (ean12)
        """       

        # Iterate through each barcode type and check validity
        for codeType in self.BARCODE_STANDARDS:
            if barcodenumber.check_code(codeType, self.data):
                return True
        
        # Invalid if data does not match any of the standards
        return False

    def getPart(self):

        try:
            part = Part.objects.get(IPN__iexact=self.data)
            return part
        except (ValueError, Part.DoesNotExist):
                raise ValidationError({'part', 'Part does not exist'})