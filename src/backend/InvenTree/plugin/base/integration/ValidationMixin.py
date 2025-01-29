"""Validation mixin class definition."""

from typing import Optional

from django.core.exceptions import ValidationError
from django.db.models import Model

import part.models
import stock.models


class ValidationMixin:
    """Mixin class that allows custom validation for various parts of InvenTree.

    Any model which inherits from the PluginValidationMixin class is exposed here,
    via the 'validate_model_instance' method (see below).

    Additionally, custom generation and validation functionality is provided for:

    - Part names
    - Part IPN (internal part number) values
    - Part parameter values
    - Serial numbers
    - Batch codes

    Notes:
    - Multiple ValidationMixin plugins can be used simultaneously
    - The stub methods provided here generally return None (null value).
    - The "first" plugin to return a non-null value for a particular method "wins"
    - In the case of "validation" functions, all loaded plugins are checked until an exception is thrown

    Implementing plugins may override any of the following methods which are of interest.

    For 'validation' methods, there are three 'acceptable' outcomes:
    - The method determines that the value is 'invalid' and raises a django.core.exceptions.ValidationError
    - The method passes and returns None (the code then moves on to the next plugin)
    - The method passes and returns True (and no subsequent plugins are checked)

    """

    class MixinMeta:
        """Metaclass for this mixin."""

        MIXIN_NAME = 'Validation'

    def __init__(self):
        """Register the mixin."""
        super().__init__()
        self.add_mixin('validation', True, __class__)

    def raise_error(self, message):
        """Raise a ValidationError with the given message."""
        raise ValidationError(message)

    def validate_model_deletion(self, instance: Model) -> None:
        """Run custom validation when a model instance is being deleted.

        This method is called when a model instance is being deleted.
        It allows the plugin to raise a ValidationError if the instance cannot be deleted.

        Arguments:
            instance: The model instance to validate

        Returns:
            None: or True (refer to class docstring)

        Raises:
            ValidationError: If the instance cannot be deleted
        """
        return None

    def validate_model_instance(
        self, instance: Model, deltas: Optional[dict] = None
    ) -> None:
        """Run custom validation on a database model instance.

        This method is called when a model instance is being validated.
        It allows the plugin to raise a ValidationError on any field in the model.

        Arguments:
            instance: The model instance to validate
            deltas: A dictionary of field names and updated values (if the instance is being updated)

        Returns:
            None: or True (refer to class docstring)

        Raises:
            ValidationError: If the instance is invalid
        """
        return None

    def validate_part_name(self, name: str, part: part.models.Part) -> None:
        """Perform validation on a proposed Part name.

        Arguments:
            name: The proposed part name
            part: The part instance we are validating against

        Returns:
            None or True (refer to class docstring)

        Raises:
            ValidationError: If the proposed name is objectionable
        """
        return None

    def validate_part_ipn(self, ipn: str, part: part.models.Part) -> None:
        """Perform validation on a proposed Part IPN (internal part number).

        Arguments:
            ipn: The proposed part IPN
            part: The Part instance we are validating against

        Returns:
            None or True (refer to class docstring)

        Raises:
            ValidationError: If the proposed IPN is objectionable
        """
        return None

    def validate_batch_code(
        self, batch_code: str, item: stock.models.StockItem
    ) -> None:
        """Validate the supplied batch code.

        Arguments:
            batch_code: The proposed batch code (string)
            item: The StockItem instance we are validating against

        Returns:
            None or True (refer to class docstring)

        Raises:
            ValidationError: If the proposed batch code is objectionable
        """
        return None

    def generate_batch_code(self, **kwargs) -> str:
        """Generate a new batch code.

        This method is called when a new batch code is required.

        kwargs:
            Any additional keyword arguments which are passed through to the plugin, based on the context of the caller

        Returns:
            A new batch code (string) or None
        """
        return None

    def validate_serial_number(
        self,
        serial: str,
        part: part.models.Part,
        stock_item: stock.models.StockItem = None,
    ) -> None:
        """Validate the supplied serial number.

        Arguments:
            serial: The proposed serial number (string)
            part: The Part instance for which this serial number is being validated
            stock_item: The StockItem instance for which this serial number is being validated (if applicable)

        Returns:
            None or True (refer to class docstring)

        Raises:
            ValidationError: If the proposed serial is objectionable
        """
        return None

    def convert_serial_to_int(self, serial: str) -> int:
        """Convert a serial number (string) into an integer representation.

        This integer value is used for efficient sorting based on serial numbers.

        A plugin which implements this method can either return:

        - An integer based on the serial string, according to some algorithm
        - A fixed value, such that serial number sorting reverts to the string representation
        - None (null value) to let any other plugins perform the conversion

        Note that there is no requirement for the returned integer value to be unique.

        Arguments:
            serial: Serial value (string)

        Returns:
            integer representation of the serial number, or None
        """
        return None

    def get_latest_serial_number(self, part, **kwargs):
        """Return the 'latest' serial number for a given Part instance.

        A plugin which implements this method can either return:
        - A string which represents the "latest" serial number
        - None (null value) if the latest value could not be determined

        Arguments:
            part: The Part instance for which the latest serial number is being requested

        Returns:
            The latest serial number (string), or None
        """
        # Default implementation returns None
        return None

    def increment_serial_number(
        self, serial: str, part: part.models.Part = None, **kwargs
    ) -> str:
        """Return the next sequential serial based on the provided value.

        A plugin which implements this method can either return:

        - A string which represents the "next" serial number in the sequence
        - None (null value) if the next value could not be determined

        Arguments:
            serial: Current serial value (string)
            part: The Part instance for which this serial number is being incremented

        Returns:
            The next serial number in the sequence (string), or None
        """
        return None

    def validate_part_parameter(
        self, parameter: part.models.PartParameter, data: str
    ) -> None:
        """Validate a parameter value.

        Arguments:
            parameter: The parameter we are validating
            data: The proposed parameter value

        Returns:
            None or True (refer to class docstring)

        Raises:
            ValidationError: If the proposed parameter value is objectionable
        """
