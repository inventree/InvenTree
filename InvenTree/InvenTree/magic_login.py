"""Functions for magic login."""
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

import sesame.utils
from rest_framework import serializers
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response


def send_simple_login_email(user, link):
    """Send an email with the login link to this user."""
    site = Site.objects.get_current()

    context = {
        "username": user.username,
        "site_name": site.name,
        "link": link,
    }
    email_plaintext_message = render_to_string("InvenTree/user_simple_login.txt", context)

    send_mail(
        _(f"[{site.name}] Log in to the app"),
        email_plaintext_message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
    )


class GetSimpleLoginSerializer(serializers.Serializer):
    """Serializer for the simple login view."""

    email = serializers.CharField(label=_("Email"))


class GetSimpleLoginView(GenericAPIView):
    """View to send a simple login link."""

    permission_classes = ()
    serializer_class = GetSimpleLoginSerializer

    def post(self, request, *args, **kwargs):
        """Get the token for the current user or fail."""
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.email_submitted(email=serializer.data["email"])
        return Response({"status": "ok"})

    def email_submitted(self, email):
        """Notify user about link."""
        user = self.get_user(email)
        if user is None:
            print("user not found:", email)
            return
        link = self.create_link(user)
        send_simple_login_email(user, link)

    def get_user(self, email):
        """Find the user with this email address."""
        try:
            return User.objects.get(email=email)
        except User.DoesNotExist:
            return None

    def create_link(self, user):
        """Create a login link for this user."""
        link = reverse("sesame-login")
        link = self.request.build_absolute_uri(link)
        link += sesame.utils.get_query_string(user)
        return link
