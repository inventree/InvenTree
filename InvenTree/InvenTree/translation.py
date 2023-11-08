"""Translation helper functions"""

import json

from django.conf import settings

# translation completion stats
_translation_stats = None


def reload_translation_stats():
    """Reload the translation stats from the compiled file"""
    global _translation_stats

    STATS_FILE = settings.BASE_DIR.joinpath('InvenTree/locale_stats.json').absolute()

    try:
        with open(STATS_FILE, 'r') as f:
            _translation_stats = json.load(f)
    except Exception:
        _translation_stats = None
        return

    keys = _translation_stats.keys()

    # Note that the names used in the stats file may not align 100%
    for (code, _lang) in settings.LANGUAGES:
        if code in keys:
            # Direct match, move on
            continue

        code_lower = code.lower().replace('-', '_')

        for k in keys:
            if k.lower() == code_lower:
                # Make a copy of the code which matches
                _translation_stats[code] = _translation_stats[k]
                break


def get_translation_percent(lang_code):
    """Return the translation percentage for the given language code"""
    if _translation_stats is None:
        reload_translation_stats()

    if _translation_stats is None:
        return 0

    return _translation_stats.get(lang_code, 0)
