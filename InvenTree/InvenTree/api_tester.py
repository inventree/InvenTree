"""
Helper functions for performing API unit tests
"""

from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase


class InvenTreeAPITestCase(APITestCase):
    """
    Base class for running InvenTree API tests
    """

    # User information 
    username = 'testuser'
    password = 'mypassword'
    email = 'test@testing.com'

    auto_login = True

    def setUp(self):

        super().setUp()

        # Create a user to log in with
        self.user = get_user_model().objects.create_user(
            username=self.username,
            password=self.password,
            email=self.email
        )

        if self.auto_login:
            self.client.login(username=self.username, password=self.password)

    def setRoles(self, roles):
        """
        Set the user roles for the registered user
        """

        pass