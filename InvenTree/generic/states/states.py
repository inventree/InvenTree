"""Generic implementation of status for InvenTree models."""


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
