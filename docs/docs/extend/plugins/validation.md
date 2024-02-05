---
title: Validation Mixin
---

## ValidationMixin

The `ValidationMixin` class enables plugins to perform custom validation of objects within the database.

Any of the methods described below can be implemented in a custom plugin to provide functionality as required.

!!! info "More Info"
    For more information on any of the methods described below, refer to the InvenTree source code. [A working example is available as a starting point](https://github.com/inventree/InvenTree/blob/master/InvenTree/plugin/samples/integration/validation_sample.py).

!!! info "Multi Plugin Support"
    It is possible to have multiple plugins loaded simultaneously which support validation methods. For example when validating a field, if one plugin returns a null value (`None`) then the *next* plugin (if available) will be queried.

## Model Validation

Any model which inherits the `PluginValidationMixin` mixin class is exposed to the plugin system for custom validation. Before the model is saved to the database (either when created, or updated), it is first passed to the plugin ecosystem for validation.

Any plugin which inherits the `ValidationMixin` can implement the `validate_model_instance` method, and run a custom validation routine.

The `validate_model_instance` method is passed the following arguments:

| Argument | Description |
| --- | --- |
| `instance` | The model instance to be validated |
| `deltas` | A dict of field deltas (if the instance is being updated) |

```python
def validate_model_instance(self, instance, deltas=None):
    """Validate the supplied model instance.

    Arguments:
        instance: The model instance to be validated
        deltas: A dict of field deltas (if the instance is being updated)
    """
    ...
```

### Error Messages

Any error messages must be raised as a `ValidationError`. The `ValidationMixin` class provides the `raise_error` method, which is a simple wrapper method which raises a `ValidationError`

#### Instance Errors

To indicate an *instance* validation error (i.e. the validation error applies to the entire model instance), the body of the error should be either a string, or a list of strings.

#### Field Errors

To indicate a *field* validation error (i.e. the validation error applies only to a single field on the model instance), the body of the error should be a dict, where the key(s) of the dict correspond to the model fields.

Note that an error can be which corresponds to multiple model instance fields.

### Example

Presented below is a simple working example for a plugin which implements the `validate_model_instance` method:

```python
from plugin import InvenTreePlugin
from plugin.mixins import ValidationMixin

import part.models


class MyValidationMixin(Validationixin, InvenTreePlugin):
    """Custom validation plugin."""

    def validate_model_instance(self, instance, deltas=None):
        """Custom model validation example.

        - A part name and category name must have the same starting letter
        - A PartCategory description field cannot be shortened after it has been created
        """

        if isinstance(instance, part.models.Part):
            if category := instance.category:
                if category.name[0] != part.name[0]:
                    self.raise_error({
                        "name": "Part name and category name must start with the same letter"
                    })

        if isinstance(instance, part.models.PartCategory):
            if deltas and 'description' in deltas:
                d_new = deltas['description']['new']
                d_old = deltas['description']['old']

                if len(d_new) < len(d_old):
                    self.raise_error({
                        "description": "Description cannot be shortened"
                    })

```

## Field Validation

In addition to the general purpose model instance validation routine provided above, the following fields support custom validation routines:

### Part Name

By default, part names are not subject to any particular naming conventions or requirements. However if custom validation is required, the `validate_part_name` method can be implemented to ensure that a part name conforms to a required convention.

If the custom method determines that the part name is *objectionable*, it should throw a `ValidationError` which will be handled upstream by parent calling methods.

### Part IPN

Validation of the Part IPN (Internal Part Number) field is exposed to custom plugins via the `validate_part_IPN` method. Any plugins which extend the `ValidationMixin` class can implement this method, and raise a `ValidationError` if the IPN value does not match a required convention.

### Part Parameter Values

[Part parameters](../../part/parameter.md) can also have custom validation rules applied, by implementing the `validate_part_parameter` method. A plugin which implements this method should raise a `ValidationError` with an appropriate message if the part parameter value does not match a required convention.

### Batch Codes

[Batch codes](../../stock/tracking.md#batch-codes) can be generated and/or validated by custom plugins.

The `validate_batch_code` method allows plugins to raise an error if a batch code input by the user does not meet a particular pattern.

The `generate_batch_code` method can be implemented to generate a new batch code.

### Serial Numbers

Requirements for serial numbers can vary greatly depending on the application. Rather than attempting to provide a "one size fits all" serial number implementation, InvenTree allows custom serial number schemes to be implemented via plugins.

The default InvenTree [serial numbering system](../../stock/tracking.md#serial-numbers) uses a simple algorithm to validate and increment serial numbers. More complex behaviors can be implemented using the `ValidationMixin` plugin class and the following custom methods:

#### Serial Number Validation

Custom serial number validation can be implemented using the `validate_serial_number` method. A *proposed* serial number is passed to this method, which then has the opportunity to raise a `ValidationError` to indicate that the serial number is not valid.

##### Example

A plugin which requires all serial numbers to be valid hexadecimal values may implement this method as follows:

```python
def validate_serial_number(self, serial: str, part: Part):
    """Validate the supplied serial number

    Arguments:
        serial: The proposed serial number (string)
        part: The Part instance for which this serial number is being validated
    """

    try:
        # Attempt integer conversion
        int(serial, 16)
    except ValueError:
        raise ValidationError("Serial number must be a valid hex value")
```

#### Serial Number Sorting

While InvenTree supports arbitrary text values in the serial number fields, behind the scenes it attempts to "coerce" these values into an integer representation for more efficient sorting.

A custom plugin can implement the `convert_serial_to_int` method to determine how a particular serial number is converted to an integer representation.

!!! info "Not Required"
    If this method is not implemented, or the serial number cannot be converted to an integer, then the sorting algorithm falls back to the text (string) value

#### Serial Number Incrementing

A core component of the InvenTree serial number system is the ability to *increment* serial numbers - to determine the *next* serial number value in a sequence.

For custom serial number schemes, it is important to provide a method to generate the *next* serial number given a current value. The `increment_serial_number` method can be implemented by a plugin to achieve this.

!!! info "Invalid Increment"
    If the provided number cannot be incremented (or an error occurs) the method should return `None`

##### Example

Continuing with the hexadecimal example as above, the method may be implemented as follows:

```python
def increment_serial_number(self, serial: str):
    """Provide the next hexadecimal number in sequence"""

    try:
        val = int(serial, 16) + 1
        val = hex(val).upper()[2:]
    except ValueError:
        val = None

    return val
```
