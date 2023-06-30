"""Target model definitions for django-data-wizard import tool:

- Any model which supports direct data import must be registered here
"""

import data_wizard

import part.models
import part.serializers

# Register Part models
data_wizard.register(part.models.Part, part.serializers.PartSerializer)
data_wizard.register(part.models.PartCategory, part.serializers.CategorySerializer)
data_wizard.register(part.models.PartParameterTemplate, part.serializers.PartParameterTemplateSerializer)
data_wizard.register(part.models.PartParameter, part.serializers.PartParameterSerializer)
data_wizard.register(part.models.BomItem, part.serializers.BomItemSerializer)
