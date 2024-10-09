"""Script to check source strings for translations."""

import argparse
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


def compare_source_strings(sources, threshold):
    """Compare source strings to find duplicates (or close matches)."""
    issues = 0

    for i, source in enumerate(sources):
        for other in sources[i + 1 :]:
            if other.lower() == source.lower():
                print(f'- Duplicate: {source} ~ {other}')
                issues += 1
                continue

            ratio = rapidfuzz.fuzz.ratio(source, other)
            if ratio > threshold:
                print(f'- Close match: {source} ~ {other} ({ratio:.1f}%)')
                issues += 1

    if issues:
        print(f' - Found {issues} issues.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Check source strings for translations.'
    )
    parser.add_argument(
        '--backend', action='store_true', help='Check backend source strings'
    )
    parser.add_argument(
        '--frontend', action='store_true', help='Check frontend source strings'
    )
    parser.add_argument(
        '--threshold',
        type=int,
        help='Set the threshold for string comparison',
        default=99,
    )

    args = parser.parse_args()

    if args.backend:
        backend_sources = extract_source_strings(BACKEND_SOURCE_FILE)
        print('Backend source strings:', len(backend_sources))
        compare_source_strings(backend_sources, args.threshold)

    if args.frontend:
        frontend_sources = extract_source_strings(FRONTEND_SOURCE_FILE)
        print('Frontend source strings:', len(frontend_sources))
        compare_source_strings(frontend_sources, args.threshold)
