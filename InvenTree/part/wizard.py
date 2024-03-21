"""Target model registration for django-data-wizard.

Each model we want to be able to import data into needs to be registered here.
"""

import data_wizard

from . import models, serializers

# Register the Part model serializers
data_wizard.register('Part', serializers.PartSerializer)
data_wizard.register('Part Category', serializers.CategorySerializer)
data_wizard.register('Part Parameter', serializers.PartParameterSerializer)
data_wizard.register('Part Test Template', serializers.PartTestTemplateSerializer)
data_wizard.register(
    'Part Parameter Template', serializers.PartParameterTemplateSerializer
)
data_wizard.register(
    'Category Parameter Template', serializers.CategoryParameterTemplateSerializer
)

# Register the BomItem model serializers
data_wizard.register('BOM Item', serializers.BomItemSerializer)
