"""Test wizard for importing data into InvenTree"""

import data_wizard

import part.models
import part.serializers

data_wizard.register(part.models.Part, part.serializers.PartSerializer)
