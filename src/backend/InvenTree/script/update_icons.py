"""This script updates the vendored tabler icons package."""

import json
import os
import shutil
import tempfile

if __name__ == '__main__':
    MY_DIR = os.path.dirname(os.path.realpath(__file__))
    STATIC_FOLDER = os.path.abspath(
        os.path.join(MY_DIR, '..', 'InvenTree', 'static', 'tabler-icons')
    )
    TMP_FOLDER = os.path.join(tempfile.gettempdir(), 'tabler-icons')

    if not os.path.exists(TMP_FOLDER):
        os.mkdir(TMP_FOLDER)

    if not os.path.exists(STATIC_FOLDER):
        os.mkdir(STATIC_FOLDER)

    print('Downloading tabler icons...')
    os.system(f'npm install --prefix {TMP_FOLDER} @tabler/icons @tabler/icons-webfont')

    print(f'Copying tabler icons to {STATIC_FOLDER}...')

    for font in ['tabler-icons.woff', 'tabler-icons.woff2', 'tabler-icons.ttf']:
        shutil.copyfile(
            os.path.join(
                TMP_FOLDER,
                'node_modules',
                '@tabler',
                'icons-webfont',
                'dist',
                'fonts',
                font,
            ),
            os.path.join(STATIC_FOLDER, font),
        )

    # Copy license
    shutil.copyfile(
        os.path.join(TMP_FOLDER, 'node_modules', '@tabler', 'icons-webfont', 'LICENSE'),
        os.path.join(STATIC_FOLDER, 'LICENSE'),
    )

    print('Generating icon list...')
    with open(
        os.path.join(TMP_FOLDER, 'node_modules', '@tabler', 'icons', 'icons.json'),
        encoding='utf-8',
    ) as f:
        icons = json.load(f)

    res = {}
    for icon in icons.values():
        res[icon['name']] = {
            'name': icon['name'],
            'category': icon['category'],
            'tags': icon['tags'],
            'variants': {
                name: style['unicode'] for name, style in icon['styles'].items()
            },
        }

    with open(os.path.join(STATIC_FOLDER, 'icons.json'), 'w', encoding='utf-8') as f:
        json.dump(res, f, separators=(',', ':'))

    print('Cleaning up...')
    shutil.rmtree(TMP_FOLDER)
