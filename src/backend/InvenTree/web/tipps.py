"""Central registration for frontend tipps.

This is a pretty simple system for now, could be enhanced in the future with plugin registrations, more complex server side logic, and dynamic tipps.
"""

COMMON_PREFIX = 'org.inventree.i.tipp'

available_tipps: dict = {
    COMMON_PREFIX + '.ftue': {}  # First-time user experience guide
    # COMMON_PREFIX + '.example': {},  # Example tip
}

KNOWN_IDS: list = list(available_tipps.keys())
