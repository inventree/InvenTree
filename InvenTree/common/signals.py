from django.dispatch import Signal

#from pretix.base.signals import DeprecatedSignal, EventPluginSignal

html_page_start = Signal(
    providing_args=[]
)
"""
This signal allows you to put code in the beginning of the main page for every
page. You are expected to return HTML.
The ``sender`` keyword argument will contain the request.
"""

html_head = Signal(
    providing_args=["request"]
)
"""
This signal allows you to put code inside the HTML ``<head>`` tag
of every page. You will get the request as the keyword argument
``request`` and are expected to return plain HTML.
As with all plugin signals, the ``sender`` keyword argument will contain the event.
"""

admin_nav_event = Signal(
    providing_args=["request"]
)
"""
This signal allows you to add additional views to the admin panel
navigation. You will get the request as a keyword argument ``request``.
Receivers are expected to return a list of dictionaries. The dictionaries
should contain at least the keys ``label`` and ``url``. You can also return
a fontawesome icon name with the key ``icon``, it will  be respected depending
on the type of navigation. You should also return an ``active`` key with a boolean
set to ``True``, when this item should be marked as active. The ``request`` object
will have an attribute ``event``.
If you use this, you should read the documentation on :ref:`how to deal with URLs <urlconf>`
in pretix.
As with all plugin signals, the ``sender`` keyword argument will contain the event.
"""

nav_topbar = Signal(
    providing_args=["request"]
)
"""
This signal allows you to add additional views to the top navigation bar.
You will get the request as a keyword argument ``request``.
Receivers are expected to return a list of dictionaries. The dictionaries
should contain at least the keys ``label`` and ``url``. You can also return
a fontawesome icon name with the key ``icon``, it will be respected depending
on the type of navigation. If set, on desktops only the ``icon`` will be shown.
The ``title`` property can be used to set the alternative text.
If you use this, you should read the documentation on :ref:`how to deal with URLs <urlconf>`
in pretix.
This is no ``EventPluginSignal``, so you do not get the event in the ``sender`` argument
and you may get the signal regardless of whether your plugin is active.
"""

nav_global = Signal(
    providing_args=["request"]
)
