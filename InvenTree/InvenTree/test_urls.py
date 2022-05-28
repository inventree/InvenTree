"""Validate that all URLs specified in template files are correct."""

import os
import re
from pathlib import Path

from django.test import TestCase
from django.urls import reverse


class URLTest(TestCase):

    # Need fixture data in the database
    fixtures = [
        'settings',
        'build',
        'company',
        'manufacturer_part',
        'price_breaks',
        'supplier_part',
        'order',
        'sales_order',
        'bom',
        'category',
        'params',
        'part_pricebreaks',
        'part',
        'test_templates',
        'location',
        'stock_tests',
        'stock',
        'users',
    ]

    def find_files(self, suffix):
        """Search for all files in the template directories, which can have URLs rendered."""
        template_dirs = [
            ('build', 'templates'),
            ('common', 'templates'),
            ('company', 'templates'),
            ('label', 'templates'),
            ('order', 'templates'),
            ('part', 'templates'),
            ('report', 'templates'),
            ('stock', 'templates'),
            ('templates', ),
        ]

        template_files = []

        here = os.path.abspath(os.path.dirname(__file__))
        tld = os.path.join(here, '..')

        for directory in template_dirs:

            template_dir = os.path.join(tld, *directory)

            for path in Path(template_dir).rglob(suffix):

                f = os.path.abspath(path)

                if f not in template_files:
                    template_files.append(f)

        return template_files

    def find_urls(self, input_file):
        """Search for all instances of {% url %} in supplied template file."""
        urls = []

        pattern = "{% url ['\"]([^'\"]+)['\"]([^%]*)%}"

        with open(input_file, 'r') as f:

            data = f.read()

            results = re.findall(pattern, data)

        for result in results:
            if len(result) == 2:
                urls.append([
                    result[0].strip(),
                    result[1].strip()
                ])
            elif len(result) == 1:  # pragma: no cover
                urls.append([
                    result[0].strip(),
                    ''
                ])

        return urls

    def reverse_url(self, url_pair):
        """Perform lookup on the URL."""
        url, pk = url_pair

        # Ignore "renaming"
        if pk.startswith('as '):
            pk = None

        # TODO: Handle reverse lookup of admin URLs!
        if url.startswith("admin:"):
            return

        # TODO can this be more elegant?
        if url.startswith("account_"):
            return

        if pk:
            # We will assume that there is at least one item in the database
            reverse(url, kwargs={"pk": 1})
        else:
            reverse(url)

    def check_file(self, f):
        """Run URL checks for the provided file."""
        urls = self.find_urls(f)

        for url in urls:
            self.reverse_url(url)

    def test_html_templates(self):

        template_files = self.find_files("*.html")

        for f in template_files:
            self.check_file(f)

    def test_js_templates(self):

        template_files = self.find_files("*.js")

        for f in template_files:
            self.check_file(f)
