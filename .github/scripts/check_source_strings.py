"""Script to check source strings for translations."""

import os

import rapidfuzz

BACKEND_SOURCE_FILE = [
    '..',
    '..',
    'src',
    'backend',
    'InvenTree',
    'locale',
    'en',
    'LC_MESSAGES',
    'django.po',
]

FRONTEND_SOURCE_FILE = [
    '..',
    '..',
    'src',
    'frontend',
    'src',
    'locales',
    'en',
    'messages.po',
]


def extract_source_strings(file_path):
    """Extract source strings from the provided file."""
    here = os.path.abspath(os.path.dirname(__file__))
    abs_file_path = os.path.abspath(os.path.join(here, *file_path))

    sources = []

    with open(abs_file_path, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line.startswith('msgid '):
                msgid = line[6:].strip()

                if msgid in sources:
                    print(f'Duplicate source string: {msgid}')
                else:
                    sources.append(msgid)

    return sources


def compare_source_strings(sources):
    """Compare source strings to find duplicates (or close matches)."""
    THRESHOLD = 98

    for i, source in enumerate(sources):
        for other in sources[i + 1 :]:
            ratio = rapidfuzz.fuzz.ratio(source, other)

            if ratio > THRESHOLD:
                print(f'- Close match: {source} ~ {other} ({ratio}%)')


if __name__ == '__main__':
    backend_sources = extract_source_strings(BACKEND_SOURCE_FILE)
    frontend_sources = extract_source_strings(FRONTEND_SOURCE_FILE)

    print('Backend source strings:', len(backend_sources))
    compare_source_strings(backend_sources)

    print('Frontend source strings:', len(frontend_sources))
    compare_source_strings(frontend_sources)
