"""Tests for fast media URL generation (InvenTree.helpers.get_media_url)."""

import random

from django.core.files.storage import default_storage
from django.test import TestCase, override_settings

from InvenTree.helpers import get_media_url


class MediaUrlTest(TestCase):
    """Tests for InvenTree.helpers.get_media_url."""

    NAMES = [
        '',
        'a.png',
        '/a.png',
        '//a.png',
        'part_images/x.thumbnail.png',
        'a/./b.png',
        'a/../b.png',
        '../x',
        './x',
        '.',
        '..',
        'a/..b/c',
        'a//b',
        'a?b#c;d:e',
        'http://evil.com/x',
        'C:\\x\\y.png',
        'ünï cödé.png',
        '%2e%2e/x',
        'x/',
    ]

    def check_names(self, names):
        """Assert get_media_url matches default_storage.url for all names."""
        for name in names:
            self.assertEqual(get_media_url(name), default_storage.url(name), name)

    def test_equivalence(self):
        """Output matches default_storage.url() for the filesystem backend."""
        rnd = random.Random(0)
        alphabet = "ab./\\?#;:%~!*()'é "
        fuzz = [
            ''.join(rnd.choice(alphabet) for _ in range(rnd.randint(0, 12)))
            for _ in range(2000)
        ]

        for media_url in ('/media/', 'https://cdn.example.com/media/'):
            with override_settings(MEDIA_URL=media_url):
                self.check_names(self.NAMES + fuzz)

    @override_settings(
        STORAGES={
            'default': {
                'BACKEND': 'django.core.files.storage.InMemoryStorage',
                'OPTIONS': {'base_url': '/memory/'},
            },
            'staticfiles': {
                'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'
            },
        }
    )
    def test_other_backend(self):
        """Other storage backends are delegated to default_storage.url()."""
        self.assertEqual(get_media_url('a/b.png'), '/memory/a/b.png')
        self.check_names(self.NAMES)
