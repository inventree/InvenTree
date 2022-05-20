"""
Unit tests for the main web views
"""

import re
import os

from django.urls import reverse

from InvenTree.helpers import InvenTreeTestCase


class ViewTests(InvenTreeTestCase):
    """ Tests for various top-level views """

    username = 'test_user'
    password = 'test_pass'

    def test_api_doc(self):
        """ Test that the api-doc view works """

        api_url = os.path.join(reverse('index'), 'api-doc') + '/'

        response = self.client.get(api_url)
        self.assertEqual(response.status_code, 200)

    def test_index_redirect(self):
        """
        top-level URL should redirect to "index" page
        """

        response = self.client.get("/")

        self.assertEqual(response.status_code, 302)

    def get_index_page(self):
        """
        Retrieve the index page (used for subsequent unit tests)
        """

        response = self.client.get("/index/")

        self.assertEqual(response.status_code, 200)

        return str(response.content.decode())

    def test_panels(self):
        """
        Test that the required 'panels' are present
        """

        content = self.get_index_page()

        self.assertIn("<div id='detail-panels'>", content)

        # TODO: In future, run the javascript and ensure that the panels get created!

    def test_js_load(self):
        """
        Test that the required javascript files are loaded correctly
        """

        # Change this number as more javascript files are added to the index page
        N_SCRIPT_FILES = 40

        content = self.get_index_page()

        # Extract all required javascript files from the index page content
        script_files = re.findall("<script type='text\\/javascript' src=\"([^\"]*)\"><\\/script>", content)

        self.assertEqual(len(script_files), N_SCRIPT_FILES)

        # TODO: Request the javascript files from the server, and ensure they are correcty loaded
