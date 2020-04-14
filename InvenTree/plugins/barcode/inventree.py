# -*- coding: utf-8 -*-

from . import barcode

from stock.models import StockItem, StockLocation
from part.models import Part

from django.utils.translation import ugettext as _


class InvenTreeBarcodePlugin(barcode.BarcodePlugin):

    PLUGIN_NAME = "InvenTreeBarcodePlugin"

    def validate(self):
        """
        An "InvenTree" barcode must include the following tags:

        {
            'tool': 'InvenTree',
            'version': <anything>
        }

        """

        for key in ['tool', 'version']:
            if key not in self.data.keys():
                return False

        if not self.data['tool'] == 'InvenTree':
            return False

        return True

    def decode(self):

        response = {}
        
        if 'part' in self.data.keys():
            id = self.data['part'].get('id', None)

            try:
                part = Part.objects.get(id=id)
                response['part'] = self.render_part(part)
            except (ValueError, Part.DoesNotExist):
                response['error'] = _('Part does not exist')

        elif 'stocklocation' in self.data.keys():
            id = self.data['stocklocation'].get('id', None)

            try:
                loc = StockLocation.objects.get(id=id)
                response['stocklocation'] = self.render_stock_location(loc)
            except (ValueError, StockLocation.DoesNotExist):
                response['error'] = _('StockLocation does not exist')

        elif 'stockitem' in self.data.keys():
            
            id = self.data['stockitem'].get('id', None)

            try:
                item = StockItem.objects.get(id=id)
                response['stockitem'] = self.render_stock_item(item)
            except (ValueError, StockItem.DoesNotExist):
                response['error'] = _('StockItem does not exist')

        else:
            response['error'] = _('No matching data')

        return response

