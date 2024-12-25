"""Overrides for allauth and adjacent packages to enforce InvenTree specific auth settings and restirctions."""

from urllib.parse import urlencode

from django import forms
from django.conf import settings
from django.contrib.auth.models import Group
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

import structlog
from allauth.account.adapter import DefaultAccountAdapter
from allauth.account.forms import LoginForm, SignupForm, set_form_field_order
from allauth.core.exceptions import ImmediateHttpResponse
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth_2fa.adapter import OTPAdapter
from allauth_2fa.forms import TOTPDeviceForm
from allauth_2fa.utils import user_has_valid_totp_device
from dj_rest_auth.registration.serializers import (
    RegisterSerializer as DjRestRegisterSerializer,
)
from rest_framework import serializers

import InvenTree.helpers_model
import InvenTree.sso
from common.settings import get_global_setting
from InvenTree.exceptions import log_error

logger = structlog.get_logger('inventree')


# override allauth
class CustomLoginForm(LoginForm):
    """Custom login form to override default allauth behaviour."""

    def login(self, request, redirect_url=None):
        """Perform login action.

        First check that:
        - A valid user has been supplied
        """
        if not self.user:
            # No user supplied - redirect to the login page
            return HttpResponseRedirect(reverse('account_login'))

        # Now perform default login action
        return super().login(request, redirect_url)


class CustomSignupForm(SignupForm):
    """Override to use dynamic settings."""

    def __init__(self, *args, **kwargs):
        """Check settings to influence which fields are needed."""
        kwargs['email_required'] = get_global_setting('LOGIN_MAIL_REQUIRED')

        super().__init__(*args, **kwargs)

        # check for two mail fields
        if get_global_setting('LOGIN_SIGNUP_MAIL_TWICE'):
            self.fields['email2'] = forms.EmailField(
                label=_('Email (again)'),
                widget=forms.TextInput(
                    attrs={
                        'type': 'email',
                        'placeholder': _('Email address confirmation'),
                    }
                ),
            )

        # check for two password fields
        if not get_global_setting('LOGIN_SIGNUP_PWD_TWICE'):
            self.fields.pop('password2', None)

        # reorder fields
        set_form_field_order(
            self, ['username', 'email', 'email2', 'password1', 'password2']
        )

    def clean(self):
        """Make sure the supplied emails match if enabled in settings."""
        cleaned_data = super().clean()

        # check for two mail fields
        if get_global_setting('LOGIN_SIGNUP_MAIL_TWICE'):
            email = cleaned_data.get('email')
            email2 = cleaned_data.get('email2')
            if (email and email2) and email != email2:
                self.add_error('email2', _('You must type the same email each time.'))

        return cleaned_data


class CustomTOTPDeviceForm(TOTPDeviceForm):
    """Ensure that db registration is enabled."""

    def __init__(self, user, metadata=None, **kwargs):
        """Override to check if registration is open."""
        if not settings.MFA_ENABLED:
            raise forms.ValidationError(_('MFA Registration is disabled.'))
        super().__init__(user, metadata, **kwargs)


def registration_enabled():
    """Determine whether user registration is enabled."""
    if (
        get_global_setting('LOGIN_ENABLE_REG')
        or InvenTree.sso.sso_registration_enabled()
    ):
        if settings.EMAIL_HOST:
            return True
        else:
            logger.error(
                'Registration cannot be enabled, because EMAIL_HOST is not configured.'
            )
    return False


class RegistrationMixin:
    """Mixin to check if registration should be enabled."""

    def is_open_for_signup(self, request, *args, **kwargs):
        """Check if signup is enabled in settings.

        Configure the class variable `REGISTRATION_SETTING` to set which setting should be used, default: `LOGIN_ENABLE_REG`.
        """
        if registration_enabled():
            return super().is_open_for_signup(request, *args, **kwargs)
        return False

    def clean_email(self, email):
        """Check if the mail is valid to the pattern in LOGIN_SIGNUP_MAIL_RESTRICTION (if enabled in settings)."""
        mail_restriction = get_global_setting('LOGIN_SIGNUP_MAIL_RESTRICTION', None)
        if not mail_restriction:
            return super().clean_email(email)

        split_email = email.split('@')
        if len(split_email) != 2:
            logger.error('The user %s has an invalid email address', email)
            raise forms.ValidationError(
                _('The provided primary email address is not valid.')
            )

        mailoptions = mail_restriction.split(',')
        for option in mailoptions:
            if not option.startswith('@'):
                log_error('LOGIN_SIGNUP_MAIL_RESTRICTION is not configured correctly')
                raise forms.ValidationError(
                    _('The provided primary email address is not valid.')
                )
            elif split_email[1] == option[1:]:
                return super().clean_email(email)

        logger.info('The provided email domain for %s is not approved', email)
        raise forms.ValidationError(_('The provided email domain is not approved.'))

    def save_user(self, request, user, form, commit=True):
        """Check if a default group is set in settings."""
        # Create the user
        user = super().save_user(request, user, form)

        # Check if a default group is set in settings
        start_group = get_global_setting('SIGNUP_GROUP')
        if (
            start_group and user.groups.count() == 0
        ):  # check that no group has been added through SSO group sync
            try:
                group = Group.objects.get(id=start_group)
                user.groups.add(group)
            except Group.DoesNotExist:
                logger.exception(
                    'The setting `SIGNUP_GROUP` contains an non existent group',
                    start_group,
                )
        user.save()
        return user


class CustomUrlMixin:
    """Mixin to set urls."""

    def get_email_confirmation_url(self, request, emailconfirmation):
        """Custom email confirmation (activation) url."""
        url = reverse('account_confirm_email', args=[emailconfirmation.key])

        return InvenTree.helpers_model.construct_absolute_url(url)


class CustomAccountAdapter(
    CustomUrlMixin, RegistrationMixin, OTPAdapter, DefaultAccountAdapter
):
    """Override of adapter to use dynamic settings."""

    def send_mail(self, template_prefix, email, context):
        """Only send mail if backend configured."""
        if settings.EMAIL_HOST:
            try:
                result = super().send_mail(template_prefix, email, context)
            except Exception:
                # An exception occurred while attempting to send email
                # Log it (for admin users) and return silently
                log_error('account email')
                result = False

            return result

        return False

    def get_email_confirmation_url(self, request, emailconfirmation):
        """Construct the email confirmation url."""
        url = super().get_email_confirmation_url(request, emailconfirmation)
        url = InvenTree.helpers_model.construct_absolute_url(url)
        return url


class CustomSocialAccountAdapter(
    CustomUrlMixin, RegistrationMixin, DefaultSocialAccountAdapter
):
    """Override of adapter to use dynamic settings."""

    def is_auto_signup_allowed(self, request, sociallogin):
        """Check if auto signup is enabled in settings."""
        if get_global_setting('LOGIN_SIGNUP_SSO_AUTO', True):
            return super().is_auto_signup_allowed(request, sociallogin)
        return False

    # from OTPAdapter
    def has_2fa_enabled(self, user):
        """Returns True if the user has 2FA configured."""
        return user_has_valid_totp_device(user)

    def login(self, request, user):
        """Ensure user is send to 2FA before login if enabled."""
        # Require two-factor authentication if it has been configured.
        if self.has_2fa_enabled(user):
            # Cast to string for the case when this is not a JSON serializable
            # object, e.g. a UUID.
            request.session['allauth_2fa_user_id'] = str(user.id)

            redirect_url = reverse('two-factor-authenticate')
            # Add GET parameters to the URL if they exist.
            if request.GET:
                redirect_url += '?' + urlencode(request.GET)

            raise ImmediateHttpResponse(response=HttpResponseRedirect(redirect_url))

        # Otherwise defer to the original allauth adapter.
        return super().login(request, user)

    def authentication_error(
        self, request, provider_id, error=None, exception=None, extra_context=None
    ):
        """Callback method for authentication errors."""
        if not error:
            error = request.GET.get('error', None)

        if not exception:
            exception = request.GET.get('error_description', None)

        path = request.path or 'sso'

        # Log the error to the database
        log_error(path, error_name=error, error_data=exception)
        logger.error("SSO error for provider '%s' - check admin error log", provider_id)


# override dj-rest-auth
class RegisterSerializer(DjRestRegisterSerializer):
    """Registration requires email, password (twice) and username."""

    email = serializers.EmailField()

    def save(self, request):
        """Override to check if registration is open."""
        if registration_enabled():
            return super().save(request)
        raise forms.ValidationError(_('Registration is disabled.'))
