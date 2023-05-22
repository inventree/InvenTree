"""Generic implementation of status for InvenTree models."""
import enum


class StatusCode:
    """Base class for representing a set of StatusCodes.

    This is used to map a set of integer values to text.
    """

    colors = {}

    @classmethod
    def render(cls, key, large=False):
        """Render the value as a HTML label."""
        # If the key cannot be found, pass it back
        if key not in cls.options.keys():
            return key

        value = cls.options.get(key, key)
        color = cls.colors.get(key, 'secondary')

        span_class = f'badge rounded-pill bg-{color}'

        return "<span class='{cl}'>{value}</span>".format(
            cl=span_class,
            value=value
        )

    @classmethod
    def list(cls):
        """Return the StatusCode options as a list of mapped key / value items."""
        return list(cls.dict().values())

    @classmethod
    def text(cls, key):
        """Text for supplied status code."""
        return cls.options.get(key, None)

    @classmethod
    def items(cls):
        """All status code items."""
        return cls.options.items()

    @classmethod
    def keys(cls):
        """All status code keys."""
        return cls.options.keys()

    @classmethod
    def labels(cls):
        """All status code labels."""
        return cls.options.values()

    @classmethod
    def names(cls):
        """Return a map of all 'names' of status codes in this class

        Will return a dict object, with the attribute name indexed to the integer value.

        e.g.
        {
            'PENDING': 10,
            'IN_PROGRESS': 20,
        }
        """
        keys = cls.keys()
        status_names = {}

        for d in dir(cls):
            if d.startswith('_'):
                continue
            if d != d.upper():
                continue

            value = getattr(cls, d, None)

            if value is None:
                continue
            if callable(value):
                continue
            if type(value) != int:
                continue
            if value not in keys:
                continue

            status_names[d] = value

        return status_names

    @classmethod
    def dict(cls):
        """Return a dict representation containing all required information"""
        values = {}

        for name, value, in cls.names().items():
            entry = {
                'key': value,
                'name': name,
                'label': cls.label(value),
            }

            if hasattr(cls, 'colors'):
                if color := cls.colors.get(value, None):
                    entry['color'] = color

            values[name] = entry

        return values

    @classmethod
    def label(cls, value):
        """Return the status code label associated with the provided value."""
        return cls.options.get(value, value)

    @classmethod
    def value(cls, label):
        """Return the value associated with the provided label."""
        for k in cls.options.keys():
            if cls.options[k].lower() == label.lower():
                return k

        raise ValueError("Label not found")


class BaseEnum(enum.Enum):
    """
    An `Enum` capabile of having its members have docstrings

    Should be passed in the form of:
      value, docstring

    Based on https://stackoverflow.com/questions/19330460/how-do-i-put-docstrings-on-enums
    """

    def __new__(cls, *args):
        obj = object.__new__(cls)
        obj._value_ = args[0]
        return obj

    def __eq__(self, obj):
        if type(self) == type(obj):
            return super().__eq__(obj)
        return self.value == obj

    def __ne__(self, obj):
        if type(self) == type(obj):
            return super().__ne__(obj)
        return self.value != obj

    def __init__(self, *args):
        """
        Creates a generic enumeration with potential assigning of a member docstring

        Should be passed in the form of:
          value, docstring
        Or:
          docstring
        """
        if len(args) == 2 and isinstance(args[-1], str):
            self.__doc__ = args[-1]


class NewStatusCode(BaseEnum):
    """Base class for representing a set of StatusCodes.

    Use enum syntax to define the status codes, e.g.
    ```python
    PENDING = 10, _("Pending"), 'secondary'
    ```
    """

    def __new__(cls, *args):
        """Define object out of args."""
        obj = object.__new__(cls)
        obj._value_ = args[0]
        if len(args) == 1:
            obj.label = args[0]
            obj.color = 'secondary'
        else:
            obj.label = args[1]
            obj.color = args[2] if len(args) > 2 else 'secondary'
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
        if type(value.value) != int:
            return False
        # if value not in keys:
        #     continue
        return True

    @classmethod
    def values(cls, key=None):
        """Return a dict representation containing all required information"""
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
        if not item:
            return key

        return f"<span class='badge rounded-pill bg-{item.color}'>{item.label}</span>"

    @classmethod
    def items(cls):
        """All status code items."""
        return [(x.value, x.label) for x in cls.values()]

    @classmethod
    def keys(cls):
        """All status code keys."""
        return [x.value for x in cls.values()]

    @classmethod
    def labels(cls):
        """All status code labels."""
        return [x.label for x in cls.values()]

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
    def dict(cls, key=None):
        """Return a dict representation containing all required information"""
        return {x.name: {
            'color': x.color,
            'key': x.value,
            'label': x.label,
            'name': x.name,
        } for x in cls.values(key)}

    @classmethod
    def list(cls):
        """Return the StatusCode options as a list of mapped key / value items."""
        return list(cls.dict().values())
