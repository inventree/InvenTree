"""Generic implementation of status for InvenTree models."""

import enum
import logging
import re
from enum import Enum
from typing import Optional

logger = logging.getLogger('inventree')


class BaseEnum(enum.IntEnum):  # noqa: PLW1641
    """An `Enum` capabile of having its members have docstrings.

    Based on https://stackoverflow.com/questions/19330460/how-do-i-put-docstrings-on-enums
    """

    def __new__(cls, *args):
        """Assign values on creation."""
        obj = object.__new__(cls)
        obj._value_ = args[0]
        return obj

    def __int__(self):
        """Return an integer representation of the value."""
        return self.value

    def __str__(self):
        """Return a string representation of the value."""
        return str(self.value)

    def __eq__(self, obj):
        """Override equality operator to allow comparison with int."""
        if type(obj) is int:
            return self.value == obj

        if isinstance(obj, BaseEnum):
            return self.value == obj.value

        if hasattr(obj, 'value'):
            return self.value == obj.value

        return super().__eq__(obj)

    def __ne__(self, obj):
        """Override inequality operator to allow comparison with int."""
        if type(self) is type(obj):
            return super().__ne__(obj)
        return self.value != obj


class StatusCode(BaseEnum):
    """Base class for representing a set of StatusCodes.

    Use enum syntax to define the status codes, e.g.
    ```python
    PENDING = 10, _("Pending"), 'secondary'
    ```

    The values of the status can be accessed with `StatusCode.PENDING.value`.

    Additionally there are helpers to access all additional attributes `text`, `label`, `color`.
    """

    def __new__(cls, *args):
        """Define object out of args."""
        obj = int.__new__(cls)
        obj._value_ = args[0]

        # Normal item definition
        if len(args) == 1:
            obj.label = args[0]
            obj.color = ColorEnum.secondary
        else:
            obj.label = args[1]
            obj.color = args[2] if len(args) > 2 else ColorEnum.secondary

        # Ensure color is a valid value
        if isinstance(obj.color, str):
            try:
                obj.color = ColorEnum(obj.color)
            except ValueError:
                raise ValueError(
                    f"Invalid color value '{obj.color}' for status '{obj.label}'"
                )

        # Set color value as string
        obj.color = obj.color.value
        obj.color_class = obj.color

        return obj

    @classmethod
    def _is_element(cls, d):
        """Check if the supplied value is a valid status code."""
        if d.startswith('_'):
            return False
        if d != d.upper():
            return False

        value = getattr(cls, d, None)

        if value is None:
            return False
        if callable(value):
            return False
        return isinstance(value.value, int)

    @classmethod
    def custom_queryset(cls):
        """Return a queryset of all custom values for this status class."""
        from common.models import InvenTreeCustomUserStateModel

        try:
            return InvenTreeCustomUserStateModel.objects.filter(
                reference_status=cls.__name__
            )
        except Exception:
            return None

    @classmethod
    def custom_values(cls):
        """Return all user-defined custom values for this status class."""
        if query := cls.custom_queryset():
            return list(query)
        return []

    @classmethod
    def values(cls, key=None):
        """Return a dict representation containing all required information."""
        elements = [itm for itm in cls if cls._is_element(itm.name)]

        if key is None:
            return elements

        ret = [itm for itm in elements if itm.value == key]
        if ret:
            return ret[0]
        return None

    @classmethod
    def render(cls, key, large=False):
        """Render the value as a HTML label."""
        # If the key cannot be found, pass it back
        item = cls.values(key)
        if item is None:
            return key

        return f"<span class='badge rounded-pill bg-{item.color}'>{item.label}</span>"

    @classmethod
    def tag(cls):
        """Return tag for this status code."""
        # Return the tag if it is defined
        if hasattr(cls, '_TAG') and bool(cls._TAG):
            return cls._TAG.value

        # Try to find a default tag
        # Remove `Status` from the class name
        ref_name = cls.__name__.removesuffix('Status')
        # Convert to snake case
        return re.sub(r'(?<!^)(?=[A-Z])', '_', ref_name).lower()

    @classmethod
    def items(cls, custom=False):
        """All status code items."""
        data = [(x.value, x.label) for x in cls.values()]

        if custom:
            try:
                for item in cls.custom_values():
                    data.append((item.key, item.label))
            except Exception:
                pass

        return data

    @classmethod
    def keys(cls, custom=True):
        """All status code keys."""
        return [el[0] for el in cls.items(custom=custom)]

    @classmethod
    def labels(cls, custom=True):
        """All status code labels."""
        return [el[1] for el in cls.items(custom=custom)]

    @classmethod
    def names(cls):
        """Return a map of all 'names' of status codes in this class."""
        return {x.name: x.value for x in cls.values()}

    @classmethod
    def text(cls, key):
        """Text for supplied status code."""
        filtered = cls.values(key)
        if filtered is None:
            return key
        return filtered.label

    @classmethod
    def label(cls, key):
        """Return the status code label associated with the provided value."""
        filtered = cls.values(key)
        if filtered is None:
            return key
        return filtered.label

    @classmethod
    def dict(cls, key=None, custom=True):
        """Return a dict representation containing all required information."""
        data = {
            x.name: {'color': x.color, 'key': x.value, 'label': x.label, 'name': x.name}
            for x in cls.values(key)
        }

        if custom:
            try:
                for item in cls.custom_values():
                    if item.name not in data:
                        data[item.name] = {
                            'color': item.color,
                            'key': item.key,
                            'label': item.label,
                            'name': item.name,
                            'custom': True,
                        }
            except Exception:
                pass

        return data

    @classmethod
    def list(cls, custom=True):
        """Return the StatusCode options as a list of mapped key / value items."""
        return list(cls.dict(custom=custom).values())

    @classmethod
    def template_context(cls, custom=True):
        """Return a dict representation containing all required information for templates."""
        data = cls.dict(custom=custom)

        ret = {x['name']: x['key'] for x in data.values()}

        ret['list'] = list(data.values())

        return ret


class ColorEnum(Enum):
    """Enum for color values."""

    primary = 'primary'
    secondary = 'secondary'
    success = 'success'
    danger = 'danger'
    warning = 'warning'
    info = 'info'
    dark = 'dark'


class StatusCodeMixin:
    """Mixin class which handles custom 'status' fields.

    - Implements a 'set_stutus' method which can be used to set the status of an object
    - Implements a 'get_status' method which can be used to retrieve the status of an object

    This mixin assumes that the implementing class has a 'status' field,
    which must be an instance of the InvenTreeCustomStatusModelField class.
    """

    STATUS_CLASS = None
    STATUS_FIELD = 'status'

    @property
    def status_class(self):
        """Return the status class associated with this model."""
        return self.STATUS_CLASS

    def save(self, *args, **kwargs):
        """Custom save method for StatusCodeMixin.

        - Ensure custom status code values are correctly updated
        """
        if self.status_class:
            # Check that the current 'logical key' actually matches the current status code
            custom_values = self.status_class.custom_queryset().filter(
                logical_key=self.get_status(), key=self.get_custom_status()
            )

            if not custom_values.exists():
                # No match - null out the custom value
                setattr(self, f'{self.STATUS_FIELD}_custom_key', None)

        super().save(*args, **kwargs)

    def get_status(self) -> int:
        """Return the status code for this object."""
        return getattr(self, self.STATUS_FIELD)

    def get_custom_status(self) -> Optional[int]:
        """Return the custom status code for this object."""
        return getattr(self, f'{self.STATUS_FIELD}_custom_key', None)

    def compare_status(self, status: int) -> bool:
        """Determine if the current status matches the provided status code.

        Arguments:
            status: The status code to compare against

        Returns:
            True if the status matches, False otherwise.
        """
        try:
            status = int(status)
        except (ValueError, TypeError):
            # Value cannot be converted to integer - so it cannot match
            return False

        if status == self.get_status():
            return True

        return status is not None and status == self.get_custom_status()

    def set_status(self, status: int, custom_values=None) -> bool:
        """Set the status code for this object.

        Arguments:
            status: The status code to set
            custom_values: Optional list of custom values to consider (can be used to avoid DB queries)
        """
        if not self.status_class:
            raise NotImplementedError('Status class not defined')

        base_values = self.status_class.values()

        custom_value_set = (
            self.status_class.custom_values()
            if custom_values is None
            else custom_values
        )

        # The status must be an integer
        try:
            status = int(status)
        except (ValueError, TypeError):
            logger.warning(f'Invalid status value {status} for class {self.__class__}')
            return False

        custom_field = f'{self.STATUS_FIELD}_custom_key'

        result = False

        if status in base_values:
            # Set the status to a 'base' value
            setattr(self, self.STATUS_FIELD, status)
            setattr(self, custom_field, None)
            result = True
        else:
            for item in custom_value_set:
                if item.key == status:
                    # Set the status to a 'custom' value
                    setattr(self, self.STATUS_FIELD, item.logical_key)
                    setattr(self, custom_field, item.key)
                    result = True
                    break

        if not result:
            logger.warning(f'Failed to set status {status} for class {self.__class__}')

        return result
