"""Helper forms which subclass Django forms to provide additional functionality."""

import logging
from urllib.parse import urlencode

from django import forms
from django.conf import settings
from django.contrib.auth.models import Group, User
from django.contrib.sites.models import Site
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from allauth.account.adapter import DefaultAccountAdapter
from allauth.account.forms import LoginForm, SignupForm, set_form_field_order
from allauth.core.exceptions import ImmediateHttpResponse
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth_2fa.adapter import OTPAdapter
from allauth_2fa.utils import user_has_valid_totp_device
from crispy_forms.bootstrap import (AppendedText, PrependedAppendedText,
                                    PrependedText)
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Field, Layout
from dj_rest_auth.registration.serializers import RegisterSerializer
from rest_framework import serializers

import InvenTree.sso
from common.models import InvenTreeSetting
from InvenTree.exceptions import log_error

logger = logging.getLogger('inventree')


class HelperForm(forms.ModelForm):
    """Provides simple integration of crispy_forms extension."""

    # Custom field decorations can be specified here, per form class
    field_prefix = {}
    field_suffix = {}
    field_placeholder = {}

    def __init__(self, *args, **kwargs):
        """Setup layout."""
        super(forms.ModelForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()

        self.helper.form_tag = False
        self.helper.form_show_errors = True

        """
        Create a default 'layout' for this form.
        Ref: https://django-crispy-forms.readthedocs.io/en/latest/layouts.html
        This is required to do fancy things later (like adding PrependedText, etc).

        Simply create a 'blank' layout for each available field.
        """

        self.rebuild_layout()

    def rebuild_layout(self):
        """Build crispy layout out of current fields."""
        layouts = []

        for field in self.fields:
            prefix = self.field_prefix.get(field, None)
            suffix = self.field_suffix.get(field, None)
            placeholder = self.field_placeholder.get(field, '')

            # Look for font-awesome icons
            if prefix and prefix.startswith('fa-'):
                prefix = f"<i class='fas {prefix}'/>"

            if suffix and suffix.startswith('fa-'):
                suffix = f"<i class='fas {suffix}'/>"

            if prefix and suffix:
                layouts.append(
                    Field(
                        PrependedAppendedText(
                            field,
                            prepended_text=prefix,
                            appended_text=suffix,
                            placeholder=placeholder
                        )
                    )
                )

            elif prefix:
                layouts.append(
                    Field(
                        PrependedText(
                            field,
                            prefix,
                            placeholder=placeholder
                        )
                    )
                )

            elif suffix:
                layouts.append(
                    Field(
                        AppendedText(
                            field,
                            suffix,
                            placeholder=placeholder
                        )
                    )
                )

            else:
                layouts.append(Field(field, placeholder=placeholder))

        self.helper.layout = Layout(*layouts)


class EditUserForm(HelperForm):
    """Form for editing user information."""

    class Meta:
        """Metaclass options."""

        model = User
        fields = [
            'first_name',
            'last_name',
        ]


class SetPasswordForm(HelperForm):
    """Form for setting user password."""

    class Meta:
        """Metaclass options."""

        model = User
        fields = [
            'enter_password',
            'confirm_password',
            'old_password',
        ]

    enter_password = forms.CharField(
        max_length=100,
        min_length=8,
        required=True,
        initial='',
        widget=forms.PasswordInput(attrs={'autocomplete': 'off'}),
        label=_('Enter password'),
        help_text=_('Enter new password')
    )

    confirm_password = forms.CharField(
        max_length=100,
        min_length=8,
        required=True,
        initial='',
        widget=forms.PasswordInput(attrs={'autocomplete': 'off'}),
        label=_('Confirm password'),
        help_text=_('Confirm new password')
    )

    old_password = forms.CharField(
        label=_("Old password"),
        strip=False,
        required=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'current-password', 'autofocus': True}),
    )


# override allauth
class CustomLoginForm(LoginForm):
    """Custom login form to override default allauth behaviour"""

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
        kwargs['email_required'] = InvenTreeSetting.get_setting('LOGIN_MAIL_REQUIRED')

        super().__init__(*args, **kwargs)

        # check for two mail fields
        if InvenTreeSetting.get_setting('LOGIN_SIGNUP_MAIL_TWICE'):
            self.fields["email2"] = forms.EmailField(
                label=_("Email (again)"),
                widget=forms.TextInput(
                    attrs={
                        "type": "email",
                        "placeholder": _("Email address confirmation"),
                    }
                ),
            )

        # check for two password fields
        if not InvenTreeSetting.get_setting('LOGIN_SIGNUP_PWD_TWICE'):
            self.fields.pop("password2")

        # reorder fields
        set_form_field_order(self, ["username", "email", "email2", "password1", "password2", ])

    def clean(self):
        """Make sure the supplied emails match if enabled in settings."""
        cleaned_data = super().clean()

        # check for two mail fields
        if InvenTreeSetting.get_setting('LOGIN_SIGNUP_MAIL_TWICE'):
            email = cleaned_data.get("email")
            email2 = cleaned_data.get("email2")
            if (email and email2) and email != email2:
                self.add_error("email2", _("You must type the same email each time."))

        return cleaned_data


def registration_enabled():
    """Determine whether user registration is enabled."""
    if InvenTreeSetting.get_setting('LOGIN_ENABLE_REG') or InvenTree.sso.registration_enabled():
        if settings.EMAIL_HOST:
            return True
        else:
            logger.error("Registration cannot be enabled, because EMAIL_HOST is not configured.")
    return False


class RegistratonMixin:
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
        mail_restriction = InvenTreeSetting.get_setting('LOGIN_SIGNUP_MAIL_RESTRICTION', None)
        if not mail_restriction:
            return super().clean_email(email)

        split_email = email.split('@')
        if len(split_email) != 2:
            logger.error('The user %s has an invalid email address', email)
            raise forms.ValidationError(_('The provided primary email address is not valid.'))

        mailoptions = mail_restriction.split(',')
        for option in mailoptions:
            if not option.startswith('@'):
                log_error('LOGIN_SIGNUP_MAIL_RESTRICTION is not configured correctly')
                raise forms.ValidationError(_('The provided primary email address is not valid.'))
            else:
                if split_email[1] == option[1:]:
                    return super().clean_email(email)

        logger.info('The provided email domain for %s is not approved', email)
        raise forms.ValidationError(_('The provided email domain is not approved.'))

    def save_user(self, request, user, form, commit=True):
        """Check if a default group is set in settings."""
        # Create the user
        user = super().save_user(request, user, form)

        # Check if a default group is set in settings
        start_group = InvenTreeSetting.get_setting('SIGNUP_GROUP')
        if start_group:
            try:
                group = Group.objects.get(id=start_group)
                user.groups.add(group)
            except Group.DoesNotExist:
                logger.exception('The setting `SIGNUP_GROUP` contains an non existent group', start_group)
        user.save()
        return user


class CustomUrlMixin:
    """Mixin to set urls."""

    def get_email_confirmation_url(self, request, emailconfirmation):
        """Custom email confirmation (activation) url."""
        url = reverse("account_confirm_email", args=[emailconfirmation.key])
        return Site.objects.get_current().domain + url


class CustomAccountAdapter(CustomUrlMixin, RegistratonMixin, OTPAdapter, DefaultAccountAdapter):
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
        """Construct the email confirmation url"""
        from InvenTree.helpers_model import construct_absolute_url

        url = super().get_email_confirmation_url(request, emailconfirmation)
        url = construct_absolute_url(url)
        return url


class CustomSocialAccountAdapter(CustomUrlMixin, RegistratonMixin, DefaultSocialAccountAdapter):
    """Override of adapter to use dynamic settings."""

    def is_auto_signup_allowed(self, request, sociallogin):
        """Check if auto signup is enabled in settings."""
        if InvenTreeSetting.get_setting('LOGIN_SIGNUP_SSO_AUTO', True):
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

            raise ImmediateHttpResponse(
                response=HttpResponseRedirect(redirect_url)
            )

        # Otherwise defer to the original allauth adapter.
        return super().login(request, user)

    def authentication_error(self, request, provider_id, error=None, exception=None, extra_context=None):
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
class CustomRegisterSerializer(RegisterSerializer):
    """Override of serializer to use dynamic settings."""
    email = serializers.EmailField()

    def __init__(self, instance=None, data=..., **kwargs):
        """Check settings to influence which fields are needed."""
        kwargs['email_required'] = InvenTreeSetting.get_setting('LOGIN_MAIL_REQUIRED')
        super().__init__(instance, data, **kwargs)

    def save(self, request):
        """Override to check if registration is open."""
        if registration_enabled():
            return super().save(request)
        raise forms.ValidationError(_('Registration is disabled.'))
