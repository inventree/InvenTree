import inspect
from enum import Enum


class ChoiceEnum(Enum):
    """ Helper class to provide enumerated choice values for integer fields
    """
    # http://blog.richard.do/index.php/2014/02/how-to-use-enums-for-django-field-choices/

    @classmethod
    def choices(cls):
        # get all members of the class
        members = inspect.getmembers(cls, lambda m: not(inspect.isroutine(m)))
        # filter down to just properties
        props = [m for m in members if not(m[0][:2] == '__')]
        # format into django choice tuple
        choices = tuple([(str(p[1].value), p[0]) for p in props])
        return choices