"""Central registration for frontend tips.

This is a pretty simple system for now, could be enhanced in the future with plugin registrations, more complex server side logic, and dynamic tips.
"""

COMMON_PREFIX = 'org.inventree.i.tip'

available_tips: dict = {
    COMMON_PREFIX + '.ftug': {}  # First-time user guide
    # COMMON_PREFIX + '.example': {},  # Example tip
}

KNOWN_IDS: list = list(available_tips.keys())
