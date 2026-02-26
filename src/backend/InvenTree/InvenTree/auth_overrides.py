"""Overrides for allauth and adjacent packages to enforce InvenTree specific auth settings and restirctions."""

from typing import Literal

from django import forms
from django.conf import settings
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

import structlog
from allauth.account.adapter import DefaultAccountAdapter
from allauth.account.forms import LoginForm, SignupForm, set_form_field_order
from allauth.headless.adapter import DefaultHeadlessAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter

from common.settings import get_global_setting
from InvenTree.exceptions import log_error

from .helpers import str2bool
from .helpers_email import is_email_configured

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


RegistrationKeys = Literal['LOGIN_ENABLE_REG', 'LOGIN_ENABLE_SSO_REG']


def registration_enabled(setting_name: RegistrationKeys = 'LOGIN_ENABLE_REG'):
    """Determine whether user registration is enabled."""
    if str2bool(get_global_setting(setting_name)):
        if is_email_configured():
            return True
        else:
            logger.warning(
                'INVE-W11: Registration cannot be enabled, because EMAIL_HOST is not configured.'
            )
    return False


class RegistrationMixin:
    """Mixin to check if registration should be enabled."""

    REGISTRATION_SETTING: RegistrationKeys = 'LOGIN_ENABLE_REG'

    def is_open_for_signup(self, request, *args, **kwargs):
        """Check if signup is enabled in settings.

        Configure the class variable `REGISTRATION_SETTING` to set which setting should be used, default: `LOGIN_ENABLE_REG`.
        """
        if registration_enabled(self.REGISTRATION_SETTING):
            return True
        logger.warning(
            f'INVE-W12: Signup attempt blocked, because registration is disabled via setting {self.REGISTRATION_SETTING}.'
        )
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


class CustomAccountAdapter(RegistrationMixin, DefaultAccountAdapter):
    """Override of adapter to use dynamic settings."""

    def send_mail(self, template_prefix, email, context):
        """Only send mail if backend configured."""
        if settings.EMAIL_HOST:
            try:
                result = super().send_mail(template_prefix, email, context)
            except Exception:
                # An exception occurred while attempting to send email
                # Log it (for admin users) and return silently
                log_error('send_mail', scope='auth')
                result = False

            return result

        return False

    def send_password_reset_mail(self, user, email, context):
        """Send the password reset mail."""
        if not get_global_setting('LOGIN_ENABLE_PWD_FORGOT'):
            raise PermissionDenied('Password reset is disabled')
        return super().send_password_reset_mail(user, email, context)


class CustomSocialAccountAdapter(RegistrationMixin, DefaultSocialAccountAdapter):
    """Override of adapter to use dynamic settings."""

    REGISTRATION_SETTING = 'LOGIN_ENABLE_SSO_REG'

    def is_auto_signup_allowed(self, request, sociallogin):
        """Check if auto signup is enabled in settings."""
        if get_global_setting('LOGIN_SIGNUP_SSO_AUTO', True):
            return super().is_auto_signup_allowed(request, sociallogin)
        return False

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
        log_error(path, error_name=error, error_data=exception, scope='auth')
        logger.error("SSO error for provider '%s' - check admin error log", provider_id)

    def get_connect_redirect_url(self, request, socialaccount):
        """Redirect to the frontend after connecting an account."""
        return request.build_absolute_uri(f'/{settings.FRONTEND_URL_BASE}/')


class CustomHeadlessAdapter(DefaultHeadlessAdapter):
    """Override of adapter to use dynamic settings."""

    def get_frontend_url(self, urlname, **kwargs):
        """Get the frontend URL for the given URL name respecting the request."""
        HEADLESS_FRONTEND_URLS = {
            'account_confirm_email': 'verify-email/{key}',
            'account_reset_password': 'reset-password',
            'account_reset_password_from_key': 'set-password?key={key}',
            'account_signup': 'register',
            'socialaccount_login_error': 'social-login-error',
        }
        if urlname not in HEADLESS_FRONTEND_URLS:
            raise ValueError(
                f'URL name "{urlname}" not found in HEADLESS_FRONTEND_URLS'
            )  # pragma: no cover

        return self.request.build_absolute_uri(
            f'/{settings.FRONTEND_URL_BASE}/{HEADLESS_FRONTEND_URLS[urlname].format(**kwargs)}'
        )
