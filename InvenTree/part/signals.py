from django.dispatch import Signal

part_tab_event = Signal(
    providing_args=["request"]
)
"""
This signal allows you to add additional tabs to the part view.
You will get the request as a keyword argument ``request``.
Receivers are expected to return a list of dictionaries. The dictionaries
should contain at least the keys ``label`` and ``url``. You can also return
a fontawesome icon name with the key ``icon``, it will  be respected depending
on the type of navigation. You should also return an ``active`` key with a boolean
set to ``True``, when this item should be marked as active. The ``request`` object
will have an attribute ``event``.
If you use this, you should read the documentation on :ref:`how to deal with URLs <urlconf>`
in pretix.
As with all plugin signals, the ``sender`` keyword argument will contain the
part.
"""
