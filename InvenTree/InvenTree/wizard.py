"""Target model definitions for django-data-wizard import tool:

- Any model which supports direct data import must be registered here
"""

import data_wizard

import order.models
import order.serializers
import part.models
import part.serializers
import stock.models
import stock.serializers

# Register Part models
data_wizard.register(part.models.Part, part.serializers.PartSerializer)
data_wizard.register(part.models.PartCategory, part.serializers.CategorySerializer)
data_wizard.register(part.models.PartParameterTemplate, part.serializers.PartParameterTemplateSerializer)
data_wizard.register(part.models.PartParameter, part.serializers.PartParameterSerializer)
data_wizard.register(part.models.BomItem, part.serializers.BomItemSerializer)

# Register Order models
data_wizard.register(order.models.SalesOrder, order.serializers.SalesOrderSerializer)
data_wizard.register(order.models.SalesOrderLineItem, order.serializers.SalesOrderLineItemSerializer)
data_wizard.register(order.models.PurchaseOrder, order.serializers.PurchaseOrderSerializer)
data_wizard.register(order.models.PurchaseOrderLineItem, order.serializers.PurchaseOrderLineItemSerializer)
data_wizard.register(order.models.ReturnOrder, order.serializers.ReturnOrderSerializer)
data_wizard.register(order.models.ReturnOrderLineItem, order.serializers.ReturnOrderLineItemSerializer)

# Register Stock models
data_wizard.register(stock.models.StockItem, stock.serializers.StockItemSerializer)
data_wizard.register(stock.models.StockLocation, stock.serializers.LocationSerializer)
